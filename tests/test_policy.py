import asyncio
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template

from test_coordinator import PACKAGE, exercise

POLICY = next(e for group in PACKAGE['template'] for e in group.get('binary_sensor', []) if e['name'] == 'Lectron charging allowed')


@pytest.mark.parametrize('when,allowed', [
    ('2026-11-02T16:59:59', True), ('2026-11-02T17:00:00', False),
    ('2026-11-02T20:59:59', False), ('2026-11-02T21:00:00', True),
    ('2026-11-06T18:00:00', False), ('2026-11-07T18:00:00', True),
    ('2026-11-01T18:00:00', True), ('2026-07-06T17:00:00', False),
    ('2026-07-06T21:00:00', True), ('2026-03-08T18:00:00', True),
])
def test_actual_policy_template_at_boundaries_and_dst(tmp_path, when, allowed):
    async def check():
        hass = HomeAssistant(str(tmp_path))
        moment = datetime.fromisoformat(when).replace(tzinfo=ZoneInfo('America/Denver'))
        with patch('homeassistant.util.dt.now', return_value=moment):
            assert Template(POLICY['state'], hass).async_render() is allowed
    asyncio.run(check())


def test_wrong_ha_timezone_fails_closed(tmp_path):
    async def check():
        hass = HomeAssistant(str(tmp_path))
        with patch('homeassistant.util.dt.now', return_value=datetime(2026, 11, 1, tzinfo=ZoneInfo('UTC'))):
            assert Template(POLICY['state'], hass).async_render() is False
    asyncio.run(check())


@pytest.mark.parametrize('policy', ['on', 'off', 'unknown', 'unavailable'])
def test_peak_start_rejected_even_with_stale_allowed_helper(tmp_path, policy):
    calls, _ = asyncio.run(exercise(tmp_path, before='2026-11-02T17:00:00', policy=policy, blocked_at_start=True))
    assert not any(x[:2] == ('switch', 'turn_on') for x in calls)
    assert not any(x[:2] == ('script', 'turn_on') and x[2]['entity_id'] == 'script.lectron_vehicle_start_charging' for x in calls)


@pytest.mark.parametrize('policy', ['unknown', 'unavailable'])
def test_unknown_policy_denies_automatic_start_outside_peak(tmp_path, policy):
    calls, _ = asyncio.run(exercise(tmp_path, policy=policy, blocked_at_start=True))
    assert not any(x[:2] == ('switch', 'turn_on') for x in calls)


def test_grace_expiring_at_17_does_not_wake_vehicle(tmp_path):
    calls, delays = asyncio.run(exercise(tmp_path, before='2026-11-02T16:55:00', after='2026-11-02T17:00:00'))
    assert delays == [300]
    assert not any(x[:2] == ('script', 'turn_on') and x[2]['entity_id'] == 'script.lectron_vehicle_start_charging' for x in calls)
    assert any(x[:2] == ('script', 'turn_on') and x[2]['entity_id'] == 'script.lectron_enforce_charging_block' for x in calls)


def test_automatic_call_cannot_borrow_manual_override(tmp_path):
    calls, _ = asyncio.run(exercise(tmp_path, before='2026-11-02T18:00:00', policy='off', override=True, blocked_at_start=True))
    assert not any(x[:2] == ('switch', 'turn_on') for x in calls)


def test_manual_flag_alone_is_insufficient(tmp_path):
    calls, _ = asyncio.run(exercise(tmp_path, before='2026-11-02T18:00:00', policy='off', manual=True, blocked_at_start=True))
    assert not any(x[:2] == ('switch', 'turn_on') for x in calls)


def test_explicit_manual_session_can_start_and_wake_during_peak(tmp_path):
    calls, delays = asyncio.run(exercise(tmp_path, before='2026-11-02T18:00:00', policy='off', manual=True, override=True))
    assert any(x[:2] == ('switch', 'turn_on') for x in calls)
    hook = next(x for x in calls if x[:2] == ('script', 'turn_on') and x[2]['entity_id'] == 'script.lectron_vehicle_start_charging')
    assert hook[2]['variables']['manual_request'] is True
    assert delays == [300, 5]


def test_permission_rechecked_after_vehicle_hook_settles(tmp_path):
    calls, _ = asyncio.run(exercise(tmp_path, before='2026-11-02T16:54:59', after='2026-11-02T16:59:59', settle='2026-11-02T17:00:04'))
    assert any(x[:2] == ('script', 'turn_on') and x[2]['entity_id'] == 'script.lectron_enforce_charging_block' for x in calls)
