"""Exercise manual takeover against running HA scripts; all actuators are fakes."""
import asyncio
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.script import Script, _ScriptRun, async_validate_actions_config

from test_coordinator import PACKAGE


class Rig:
    def __init__(self, path):
        self.hass = HomeAssistant(str(path))
        self.scripts, self.tasks, self.calls, self.waits = {}, [], [], []
        self.now = datetime(2026, 11, 2, 16, 55, tzinfo=ZoneInfo('America/Denver'))
        self.race_entered, self.race_release = asyncio.Event(), asyncio.Event()
        self.pause_cancel = False

    async def setup(self):
        for entity, state in {
            'binary_sensor.lectron_v_box_pro_vehicle_connected': 'on',
            'binary_sensor.lectron_v_box_pro_problem': 'off',
            'binary_sensor.lectron_v_box_pro_charging': 'off',
            'sensor.lectron_v_box_pro_status': 'session_ended',
            'sensor.lectron_v_box_pro_charging_power': 'unavailable',
            'switch.lectron_v_box_pro_charging_request': 'off',
            'binary_sensor.lectron_charging_allowed': 'on',
            'input_boolean.lectron_manual_charge_override': 'off',
        }.items():
            self.hass.states.async_set(entity, state)
        configs = dict(PACKAGE['script'])
        # A pending old hook must be cancellable before its next vehicle action.
        configs['lectron_vehicle_start_charging'] = {'mode': 'single', 'sequence': [
            {'delay': {'seconds': 600}}, {'action': 'kia_uvo.start_charge'}]}
        for name, config in configs.items():
            sequence = await async_validate_actions_config(self.hass, cv.SCRIPT_SCHEMA(config['sequence']))
            def changed(name=name):
                self.hass.states.async_set('script.' + name, 'on' if self.scripts[name].is_running else 'off')
            self.scripts[name] = Script(self.hass, sequence, name, 'script', script_mode=config['mode'], change_listener=changed)
            self.hass.states.async_set('script.' + name, 'off')
        for domain, names in {'script':['turn_on','turn_off'], 'input_boolean':['turn_on','turn_off'], 'switch':['turn_on','turn_off'], 'persistent_notification':['create','dismiss'], 'kia_uvo':['start_charge']}.items():
            for name in names:
                self.hass.services.async_register(domain, name, self.service)

    def set_peak(self):
        self.now = self.now.replace(hour=17, minute=0)
        self.hass.states.async_set('binary_sensor.lectron_charging_allowed', 'off')

    async def service(self, call):
        target = call.data.get('entity_id', [])
        targets = target if isinstance(target, list) else [target]
        self.calls.append((call.domain, call.service, targets))
        if call.domain == 'script':
            for target in targets:
                name = target.removeprefix('script.')
                if name not in self.scripts:
                    continue
                if call.service == 'turn_off':
                    if self.pause_cancel and name == 'lectron_start_charging' and self.hass.states.get('input_boolean.lectron_manual_charge_override').state == 'off':
                        self.pause_cancel = False
                        self.race_entered.set()
                        await self.race_release.wait()
                    await self.scripts[name].async_stop()
                else:
                    self.launch(name, dict(call.data.get('variables', {})))
                    await asyncio.sleep(0)
        elif call.domain in ('input_boolean', 'switch'):
            for target in targets:
                self.hass.states.async_set(target, 'on' if call.service == 'turn_on' else 'off')
                if call.domain == 'switch' and call.service == 'turn_off':
                    self.hass.states.async_set('binary_sensor.lectron_v_box_pro_charging', 'off')

    def launch(self, name, variables=None):
        task = asyncio.create_task(self.scripts[name].async_run(variables or {}, context=Context()))
        self.tasks.append(task)
        return task

    async def delay(self, run):
        seconds = run._get_pos_time_period_template('delay').total_seconds()
        if seconds in (300, 600):
            event = asyncio.Event()
            self.waits.append((seconds, event))
            waiter = asyncio.create_task(event.wait())
            try:
                await asyncio.wait([waiter, run._stop], return_when=asyncio.FIRST_COMPLETED)
            finally:
                waiter.cancel()
                await asyncio.gather(waiter, return_exceptions=True)

    async def until(self, check):
        async def spin():
            while not check():
                await asyncio.sleep(0)
        await asyncio.wait_for(spin(), timeout=2)

    async def close(self):
        for script in self.scripts.values():
            await script.async_stop()
        await asyncio.gather(*self.tasks, return_exceptions=True)


async def scenario(path, kind):
    rig = Rig(path)
    await rig.setup()
    async def delay(run):
        await rig.delay(run)
    with patch.object(_ScriptRun, '_async_step_delay', delay), patch('homeassistant.util.dt.now', side_effect=lambda *a, **k: rig.now):
        try:
            if kind == 'old_hook':
                rig.launch('lectron_vehicle_start_charging')
                await rig.until(lambda: len(rig.waits) == 1)
            elif kind == 'enforcement':
                rig.set_peak()
                rig.pause_cancel = True
                rig.launch('lectron_enforce_charging_block')
                await asyncio.wait_for(rig.race_entered.wait(), timeout=2)
            else:
                rig.launch('lectron_start_charging')
                await rig.until(lambda: len(rig.waits) == 1)
            rig.set_peak()
            old_waits = list(rig.waits)
            await asyncio.wait_for(rig.launch('lectron_charge_now'), timeout=2)
            await rig.until(lambda: len(rig.waits) == len(old_waits) + 1)
            assert rig.hass.states.get('input_boolean.lectron_manual_charge_override').state == 'on'
            assert rig.scripts['lectron_start_charging'].is_running
            assert not rig.scripts['lectron_vehicle_start_charging'].is_running
            assert not rig.scripts['lectron_enforce_charging_block'].is_running
            for _, event in old_waits:
                event.set()
            rig.race_release.set()
            await asyncio.sleep(0)
            assert not any(x[0] == 'kia_uvo' for x in rig.calls)
            if kind == 'stop':
                await asyncio.wait_for(rig.launch('lectron_stop_charging'), timeout=2)
                assert rig.hass.states.get('input_boolean.lectron_manual_charge_override').state == 'off'
                assert not rig.scripts['lectron_start_charging'].is_running
        finally:
            await rig.close()


def test_manual_takeover_cancels_old_automatic_grace(tmp_path):
    asyncio.run(scenario(tmp_path, 'grace'))


def test_manual_takeover_cancels_inflight_enforcement(tmp_path):
    asyncio.run(scenario(tmp_path, 'enforcement'))


def test_manual_takeover_cancels_old_vehicle_hook(tmp_path):
    asyncio.run(scenario(tmp_path, 'old_hook'))


def test_stop_clears_manual_intent_and_cancels_new_grace(tmp_path):
    asyncio.run(scenario(tmp_path, 'stop'))
