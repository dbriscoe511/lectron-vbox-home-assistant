"""Run the real HA script engine with isolated services and a controlled clock."""
import asyncio
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch

import pytest
import yaml
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.script import Script, _ScriptRun, async_validate_actions_config

PACKAGE = yaml.safe_load((Path(__file__).resolve().parents[1] / 'home-assistant/lectron_charging.yaml').read_text())


async def exercise(tmp_path, invalid=None, stop_during_grace=False, before=None, after=None, policy='on', manual=False, override=False, blocked_at_start=False, settle=None):
    hass = HomeAssistant(str(tmp_path))
    states = {
        'binary_sensor.lectron_v_box_pro_vehicle_connected': 'on',
        'binary_sensor.lectron_v_box_pro_problem': 'off',
        'binary_sensor.lectron_v_box_pro_charging': 'off',
        'sensor.lectron_v_box_pro_charging_power': 'unavailable',
        'switch.lectron_v_box_pro_charging_request': 'off',
        'script.lectron_vehicle_start_charging': 'off',
        'script.lectron_charge_now': 'off',
        'binary_sensor.lectron_charging_allowed': policy,
        'input_boolean.lectron_manual_charge_override': 'on' if override else 'off',
    }
    for entity, value in states.items():
        hass.states.async_set(entity, value)
    entered, release = asyncio.Event(), asyncio.Event()
    calls, delays = [], []
    start = None
    clock = {'now': datetime.fromisoformat(before or '2026-11-01T12:00:00').replace(tzinfo=ZoneInfo('America/Denver'))}

    async def service(call):
        data = dict(call.data)
        target = data.get('entity_id')
        if isinstance(target, list) and len(target) == 1:
            target = target[0]
            data['entity_id'] = target
        calls.append((call.domain, call.service, data))
        if call.domain == 'script' and call.service == 'turn_off' and target == 'script.lectron_start_charging':
            await start.async_stop()
        if call.domain == 'script' and call.service == 'turn_on' and target == 'script.lectron_vehicle_start_charging':
            hass.states.async_set('binary_sensor.lectron_v_box_pro_charging', 'on')
            hass.states.async_set('sensor.lectron_v_box_pro_charging_power', '9.0')

    for domain, names in {'input_boolean':['turn_on','turn_off'], 'switch': ['turn_on', 'turn_off'], 'script': ['turn_on', 'turn_off'], 'persistent_notification': ['create', 'dismiss']}.items():
        for name in names:
            hass.services.async_register(domain, name, service)

    async def delay(run):
        seconds = run._get_pos_time_period_template('delay').total_seconds()
        delays.append(seconds)
        if seconds == 5 and settle:
            clock['now']=datetime.fromisoformat(settle).replace(tzinfo=ZoneInfo('America/Denver'))
        if seconds == 300:
            entered.set()
            release_task = asyncio.create_task(release.wait())
            tasks = [release_task, run._stop]
            try:
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            finally:
                release_task.cancel()
                await asyncio.gather(release_task, return_exceptions=True)

    async def make(name):
        config = PACKAGE['script'][name]
        sequence = await async_validate_actions_config(hass, cv.SCRIPT_SCHEMA(config['sequence']))
        return Script(hass, sequence, name, 'script', script_mode=config['mode'])

    with patch.object(_ScriptRun, '_async_step_delay', delay), patch('homeassistant.util.dt.now', side_effect=lambda *a, **k: clock['now']):
        start = await make('lectron_start_charging')
        task = asyncio.create_task(start.async_run({'manual_request':manual},context=Context()))
        if blocked_at_start:
            await asyncio.wait_for(task,timeout=2)
            return calls,delays
        await asyncio.wait_for(entered.wait(), timeout=2)
        assert delays == [300]
        assert [(d, s) for d, s, _ in calls] == [('switch', 'turn_on')]
        if after:
            clock['now']=datetime.fromisoformat(after).replace(tzinfo=ZoneInfo('America/Denver'))
        if invalid:
            entity, value = invalid
            hass.states.async_set(entity, value)
        if stop_during_grace:
            stop = await make('lectron_stop_charging')
            await asyncio.wait_for(stop.async_run(context=Context()), timeout=2)
        release.set()
        await asyncio.wait_for(task, timeout=2)
    return calls, delays


def test_vehicle_hook_only_after_full_grace(tmp_path):
    calls, delays = asyncio.run(exercise(tmp_path))
    hooks = [x for x in calls if x[:2] == ('script', 'turn_on')]
    assert len(hooks) == 1
    assert delays == [300, 5]


@pytest.mark.parametrize('invalid', [
    ('switch.lectron_v_box_pro_charging_request', 'unavailable'),
    ('binary_sensor.lectron_v_box_pro_charging', 'unavailable'),
    ('binary_sensor.lectron_v_box_pro_problem', 'on'),
    ('binary_sensor.lectron_v_box_pro_vehicle_connected', 'off'),
])
def test_missing_telemetry_fault_or_unplug_prevents_vehicle_wake(tmp_path, invalid):
    calls, _ = asyncio.run(exercise(tmp_path, invalid=invalid))
    assert not any(x[:2] == ('script', 'turn_on') for x in calls)
    assert any(x[:2] == ('persistent_notification', 'create') for x in calls)


def test_stop_cancels_grace_without_late_restart(tmp_path):
    calls, _ = asyncio.run(exercise(tmp_path, stop_during_grace=True))
    assert not any(x[:2] == ('script', 'turn_on') for x in calls)
    stop_calls = [x for x in calls if x[:2] == ('switch', 'turn_off')]
    assert len(stop_calls) == 1
    cancel = next(i for i, x in enumerate(calls) if x[:2] == ('script', 'turn_off') and x[2]['entity_id'] == 'script.lectron_start_charging')
    hook_cancel = next(i for i, x in enumerate(calls) if x[:2] == ('script', 'turn_off') and x[2]['entity_id'] == 'script.lectron_vehicle_start_charging')
    assert cancel < hook_cancel < calls.index(stop_calls[0])
