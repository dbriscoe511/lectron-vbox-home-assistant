import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from homeassistant.core import Context
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.script import Script, _ScriptRun, async_validate_actions_config
from homeassistant.helpers.template import Template

from test_coordinator import PACKAGE
from test_policy_races import Rig


async def automation(rig, key):
    config = next(x for x in PACKAGE['automation'] if x['id'] == key)
    sequence = config.get('conditions', []) + config['actions']
    sequence = await async_validate_actions_config(rig.hass, cv.SCRIPT_SCHEMA(sequence))
    return Script(rig.hass, sequence, key, 'automation')


@pytest.mark.parametrize('manual', [False, True])
def test_block_reacts_to_charging_without_stopping_manual_session(tmp_path, manual):
    async def check():
        rig = Rig(tmp_path)
        await rig.setup()
        rig.set_peak()
        rig.hass.states.async_set('switch.lectron_v_box_pro_charging_request', 'on')
        rig.hass.states.async_set('binary_sensor.lectron_v_box_pro_charging', 'on')
        rig.hass.states.async_set('input_boolean.lectron_manual_charge_override', 'on' if manual else 'off')
        async def delay(run):
            await rig.delay(run)
        with patch('homeassistant.util.dt.now', side_effect=lambda *a, **k: rig.now), patch.object(_ScriptRun, '_async_step_delay', delay):
            try:
                runner = await automation(rig, 'lectron_peak_charge_enforcement')
                await runner.async_run({'trigger': {'id': 'plug'}}, context=Context())
                await asyncio.sleep(0)
                if not manual:
                    await rig.until(lambda: rig.hass.states.get('switch.lectron_v_box_pro_charging_request').state == 'off')
                else:
                    assert rig.hass.states.get('switch.lectron_v_box_pro_charging_request').state == 'on'
                assert not any(x[0] == 'kia_uvo' for x in rig.calls)
            finally:
                await rig.close()
    asyncio.run(check())


def test_opening_reconciliation_starts_only_one_grace(tmp_path):
    async def check():
        rig = Rig(tmp_path)
        await rig.setup()
        rig.now = rig.now.replace(hour=21, minute=0)
        async def delay(run):
            await rig.delay(run)
        with patch('homeassistant.util.dt.now', side_effect=lambda *a, **k: rig.now), patch.object(_ScriptRun, '_async_step_delay', delay):
            try:
                runner = await automation(rig, 'lectron_scheduled_charging_resume')
                await runner.async_run({'trigger': {'id': 'boundary'}}, context=Context())
                await rig.until(lambda: bool(rig.waits))
                await runner.async_run({'trigger': {'id': 'allowed'}}, context=Context())
                assert len(rig.waits) == 1
                assert len([x for x in rig.calls if x[:2] == ('switch', 'turn_on')]) == 1
                assert not any(x[0] == 'kia_uvo' for x in rig.calls)
            finally:
                await rig.close()
    asyncio.run(check())


def test_blocked_startup_does_not_resume_and_periodic_checks_do_not_wake(tmp_path):
    async def check():
        rig = Rig(tmp_path)
        await rig.setup()
        rig.set_peak()
        with patch('homeassistant.util.dt.now', side_effect=lambda *a, **k: rig.now):
            try:
                runner = await automation(rig, 'lectron_scheduled_charging_resume')
                await runner.async_run({'trigger': {'id': 'startup'}}, context=Context())
                assert not rig.calls
                config = next(x for x in PACKAGE['automation'] if x['id'] == 'lectron_scheduled_charging_resume')
                assert not any(x['trigger'] == 'time_pattern' for x in config['triggers'])
                assert PACKAGE['input_boolean']['lectron_manual_charge_override']['initial'] is False
            finally:
                await rig.close()
    asyncio.run(check())


@pytest.mark.parametrize('manual,override,stale_helper,expect', [
    (False,False,False,False), (False,False,True,False),
    (False,True,False,False), (True,False,False,False),
    (True,True,False,True),
])
def test_private_hook_contract_blocks_direct_automatic_bypass(tmp_path, manual, override, stale_helper, expect):
    async def check():
        rig = Rig(tmp_path)
        await rig.setup()
        rig.set_peak()
        rig.hass.states.async_set('input_boolean.lectron_manual_charge_override','on' if override else 'off')
        rig.hass.states.async_set('binary_sensor.lectron_charging_allowed','on' if stale_helper else 'off')
        config = yaml.safe_load((Path(__file__).resolve().parents[1]/'home-assistant/vehicle-hooks.example.yaml').read_text())['script']['lectron_vehicle_start_charging']
        with patch('homeassistant.util.dt.now', side_effect=lambda *a, **k: rig.now):
            try:
                sequence = await async_validate_actions_config(rig.hass, cv.SCRIPT_SCHEMA(config['sequence']))
                runner = Script(rig.hass, sequence, 'private hook contract', 'script')
                await runner.async_run({'manual_request':manual},context=Context())
                assert bool([x for x in rig.calls if x[0]=='kia_uvo']) is expect
            finally:
                await rig.close()
    asyncio.run(check())


def test_session_cleanup_does_not_clear_manual_takeover(tmp_path):
    async def check():
        rig = Rig(tmp_path)
        await rig.setup()
        config=next(x for x in PACKAGE['automation'] if x['id']=='lectron_clear_manual_charge_override')
        trigger=next(x for x in config['triggers'] if x['id']=='ended')
        assert trigger['for']=='00:00:30'
        rig.hass.states.async_set('script.lectron_charge_now','on')
        assert Template(trigger['value_template'],rig.hass).async_render() is False
        rig.hass.states.async_set('script.lectron_charge_now','off')
        assert Template(trigger['value_template'],rig.hass).async_render() is True
        await rig.close()
    asyncio.run(check())


def test_already_charging_does_not_bypass_peak_policy(tmp_path):
    async def check():
        rig = Rig(tmp_path)
        await rig.setup()
        rig.set_peak()
        rig.hass.states.async_set('switch.lectron_v_box_pro_charging_request','on')
        rig.hass.states.async_set('binary_sensor.lectron_v_box_pro_charging','on')
        rig.hass.states.async_set('sensor.lectron_v_box_pro_charging_power','9.0')
        with patch('homeassistant.util.dt.now', side_effect=lambda *a, **k: rig.now):
            try:
                rig.launch('lectron_start_charging')
                await rig.until(lambda: rig.hass.states.get('switch.lectron_v_box_pro_charging_request').state=='off')
                assert not any(x[0]=='kia_uvo' for x in rig.calls)
            finally:
                await rig.close()
    asyncio.run(check())


def test_recovery_waits_for_all_required_telemetry(tmp_path):
    async def check():
        rig=Rig(tmp_path)
        await rig.setup()
        config=next(x for x in PACKAGE['automation'] if x['id']=='lectron_scheduled_charging_resume')
        trigger=next(x for x in config['triggers'] if x['id']=='recovery')
        assert trigger['trigger']=='template'
        template=Template(trigger['value_template'],rig.hass)
        rig.hass.states.async_set('binary_sensor.lectron_v_box_pro_problem','unavailable')
        assert template.async_render() is False
        rig.hass.states.async_set('binary_sensor.lectron_v_box_pro_problem','off')
        assert template.async_render() is True
        rig.hass.states.async_set('binary_sensor.lectron_v_box_pro_charging','on')
        assert template.async_render() is True
        rig.hass.states.async_set('binary_sensor.lectron_v_box_pro_charging','off')
        assert template.async_render() is True
        await rig.close()
    asyncio.run(check())
