"""Telemetry semantics, missing reports, and limited writes are the contract."""
import base64
import asyncio
import json
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock

import pytest
import yaml

from custom_components.tuya_local.helpers.device_config import TuyaDeviceConfig
from custom_components.tuya_local.sensor import TuyaLocalSensor
from custom_components.tuya_local.switch import TuyaLocalSwitch
from custom_components.tuya_local.select import TuyaLocalSelect

ROOT = Path(__file__).resolve().parents[1]
PROFILE = (
    Path(os.environ["TUYA_LOCAL_SOURCE"])
    / "custom_components/tuya_local/devices/lectron_vboxpro_evcharger.yaml"
)


@pytest.fixture
def config():
    return TuyaDeviceConfig(str(PROFILE))


@pytest.fixture
def state():
    return json.loads((ROOT / "tests/fixtures/idle.json").read_text())["dps"]


def device(state):
    mock = Mock()
    mock.name = "Synthetic charger"
    mock.unique_id = "synthetic"
    mock.has_returned_state = True
    mock.get_property.side_effect = lambda key: state.get(str(key))
    return mock


def entity(config, name):
    # Upstream leaves default names (Status, Voltage, ...) to translations or device class.
    slug = name.lower().replace(" ", "_")
    items = list(config.all_entities())
    return next(
        (item for item in items if item.name == name),
        None,
    ) or next(item for item in items if item.name is None and item.config_id == f"{item.entity}_{slug}")


def value(config, state, name, field="sensor"):
    return entity(config, name).find_dps(field).get_value(device(state))


def test_energy_scale_and_state_classes(config, state):
    assert value(config, state, "Total energy") == 1234.56
    assert value(config, state, "Session energy") == 12.34
    assert entity(config, "Total energy").find_dps("sensor").state_class == "total_increasing"
    assert entity(config, "Session energy").find_dps("sensor").state_class is None


def test_phase_uses_normal_reporting_without_forced_requests(config):
    from custom_components.tuya_local.device import TuyaLocalDevice

    # Exercise the transport's registration, without creating a socket or running it.
    transport = Mock()
    transport._hass.is_running = True
    transport._children = []
    transport._force_dps = []
    transport._running = True
    transport.has_returned_state = True
    for definition in config.all_entities():
        child = Mock()
        child._config = definition
        TuyaLocalDevice.register_entity(transport, child)
    assert transport._force_dps == []


def test_temperature_is_fahrenheit(config, state):
    sensor = TuyaLocalSensor(device(state), entity(config, "Internal temperature"))
    assert sensor.native_value == 72
    assert sensor.native_unit_of_measurement == "°F"


@pytest.mark.parametrize("raw,expected", [
    ("charger_free", False), ("charger_charging", True),
    ("charger_end", False), ("charger_suddenStop", False),
    ("new_firmware_state", None), (None, None),
])
def test_confirmed_charging_never_uses_request_switch(config, state, raw, expected):
    state["3"] = raw
    state["18"] = True
    assert value(config, state, "Charging") is expected


@pytest.mark.parametrize("raw,expected", [
    ("controlpi_12v", False), ("controlpi_9v_pwm", True),
    ("controlpi_error", None), ("new_pilot_state", None), (None, None),
])
def test_connected_fails_unknown_on_bad_pilot(config, state, raw, expected):
    state["13"] = raw
    assert value(config, state, "Vehicle connected") is expected


@pytest.mark.parametrize("raw,expected", [(0, False), (1, True), (5, True), (None, None)])
def test_fault_bit_combinations_and_missing_reports(config, state, raw, expected):
    state["10"] = raw
    assert value(config, state, "Problem") is expected


def test_unrecognized_status_is_unknown_and_not_a_valid_enum_option(config, state):
    state["3"] = "future_value"
    assert value(config, state, "Status") is None
    options = entity(config, "Status").find_dps("sensor").values(device(state))
    assert all(isinstance(option, str) for option in options)
    state["3"] = "charger_end"
    assert value(config, state, "Status") == "session_ended"


@pytest.mark.parametrize("name,dp", [("Charging power", "6"), ("Single phase power", "5"), ("Voltage", "6"), ("Current", "6")])
def test_missing_power_is_unavailable_until_first_report(config, state, name, dp):
    assert value(config, state, name) is None
    assert value(config, state, name, "available") is False
    ent = entity(config, name)
    assert ent.find_dps("sensor").persist is (dp == "6")
    assert ent.find_dps("available").persist is (dp == "6")
    state['3'] = 'charger_charging'
    packet = (2400).to_bytes(2, "big") + (32000).to_bytes(3, "big") + (7680).to_bytes(3, "big") + bytes(4)
    state[dp] = base64.b64encode(packet).decode() if dp == '6' else 7680
    assert value(config, state, name) == {'Voltage': 240, 'Current': 32}.get(name, 7.68)
    assert value(config, state, name, "available") is True


def test_twelve_byte_phase_fields_are_independent(config, state):
    packet = (2400).to_bytes(2, "big") + (32000).to_bytes(3, "big") + (7680).to_bytes(3, "big") + (0xDEADBEEF).to_bytes(4, "big")
    state["6"] = base64.b64encode(packet).decode()
    assert value(config, state, "Voltage") == 240
    assert value(config, state, "Current") == 32
    assert value(config, state, 'Charging power') == 7.68
    state['6'] = base64.b64encode(packet[:8] + bytes(4)).decode()
    assert value(config, state, 'Voltage') == 240
    assert value(config, state, 'Current') == 32
    assert value(config, state, 'Charging power') == 7.68


@pytest.mark.parametrize('raw_energy,expected', [
    (0, 0), (52, 0.52), (170, 1.70), (256, 2.56),
    (65536, 655.36), (0x01020304, 169090.60),
])
def test_phase_session_energy_uses_all_four_tail_bytes(config, state, raw_energy, expected):
    prefix = (2400).to_bytes(2, 'big') + (32000).to_bytes(3, 'big') + (7680).to_bytes(3, 'big')
    state['6'] = base64.b64encode(prefix + raw_energy.to_bytes(4, 'big')).decode()
    assert value(config, state, 'Phase session energy') == pytest.approx(expected)
    state['6'] = base64.b64encode(bytes(8) + raw_energy.to_bytes(4, 'big')).decode()
    assert value(config, state, 'Phase session energy') == pytest.approx(expected)


@pytest.mark.parametrize('status', ['charger_charging', 'charger_pause', 'charger_end'])
def test_phase_session_energy_retains_reported_value_when_stopped(config, state, status):
    state['3'] = status
    state['6'] = base64.b64encode(bytes(8) + (170).to_bytes(4, 'big')).decode()
    sensor = TuyaLocalSensor(device(state), entity(config, 'Phase session energy'))
    assert sensor.native_value == 1.70
    assert value(config, state, 'Phase session energy', 'available') is True
    assert sensor.extra_state_attributes['raw_phase_packet'] == state['6']
    assert sensor.state_class is None


def test_missing_phase_energy_is_unavailable_not_zero_or_dp25(config, state):
    sensor = TuyaLocalSensor(device(state), entity(config, 'Phase session energy'))
    assert sensor.native_value is None
    assert value(config, state, 'Phase session energy', 'available') is False
    assert 'raw_phase_packet' not in sensor.extra_state_attributes
    assert all(dp.persist for dp in entity(config, 'Phase session energy').dps())


def test_profile_only_writes_charging_request_and_excludes_sensitive_controls(config):
    raw = yaml.safe_load(PROFILE.read_text())
    writable = [item for item in raw['entities'] if item['entity'] not in {'sensor', 'binary_sensor'}]
    assert len(writable) == 3
    assert {x['entity'] for x in writable} == {'switch', 'select'}
    assert {dp['id'] for x in writable for dp in x['dps'] if dp['name'] in {'switch', 'option'}} == {4, 14, 18}
    assert all(dp["id"] not in {11, 12, 16, 17, 19, 22, 33, 105} for ent in raw["entities"] for dp in ent["dps"])
    ids = [ent.config_id for ent in config.all_entities()]
    assert len(ids) == len(set(ids))


def test_switch_sends_only_boolean_dp18(config, state):
    mock = device(state)
    mock.async_set_properties = AsyncMock()
    switch = TuyaLocalSwitch(mock, entity(config, 'Charging request'))
    assert switch.is_on is False
    asyncio.run(switch.async_turn_on())
    mock.async_set_properties.assert_awaited_once_with({'18': True})
    mock.async_set_properties.reset_mock()
    asyncio.run(switch.async_turn_off())
    mock.async_set_properties.assert_awaited_once_with({'18': False})



def test_current_selector_only_offers_manufacturer_settings(config, state):
    mock = device(state)
    mock.async_set_properties = AsyncMock()
    select = TuyaLocalSelect(mock, entity(config, 'Charging current'))
    assert select.options == ['16 A', '32 A', '40 A', '48 A']
    assert select.current_option == '32 A'
    asyncio.run(select.async_select_option('40 A'))
    mock.async_set_properties.assert_awaited_once_with({'4': 40})


@pytest.mark.parametrize('option,raw', [
    ('Plug and charge', 'charge_now'),
    ('Manual start', 'charge_manual'),
    ('Scheduled charge', 'charge_schedule'),
])
def test_operating_mode_writes_only_dp14(config, state, option, raw):
    state.update({'3': 'charger_pause', '14': 'charge_now'})
    mock = device(state)
    mock.async_set_properties = AsyncMock()
    select = TuyaLocalSelect(mock, entity(config, 'Operating mode'))
    assert select.options == ['Plug and charge', 'Manual start', 'Scheduled charge']
    asyncio.run(select.async_select_option(option))
    mock.async_set_properties.assert_awaited_once_with({'14': raw})


def test_operating_mode_cannot_change_during_charging(config, state):
    state.update({'3': 'charger_charging', '14': 'charge_now'})
    mock = device(state)
    mock.async_set_properties = AsyncMock()
    select = TuyaLocalSelect(mock, entity(config, 'Operating mode'))
    with pytest.raises(AttributeError):
        asyncio.run(select.async_select_option('Manual start'))
    mock.async_set_properties.assert_not_awaited()


@pytest.mark.parametrize('status', ['charger_charging', 'charger_fault', 'charger_free_fault', 'future', None])
def test_operating_mode_unavailable_when_not_known_idle(config, state, status):
    state['3'] = status
    assert value(config, state, 'Operating mode', 'available') is False


@pytest.mark.parametrize('status', ['charger_free','charger_pause','charger_end','charger_fault','future',None])
def test_noncharging_status_hides_stale_phase_packet(config, state, status):
    packet=(2400).to_bytes(2,'big')+(32000).to_bytes(3,'big')+(7680).to_bytes(3,'big')+bytes(4)
    state['6']=base64.b64encode(packet).decode()
    state['3']=status
    for name in ('Voltage','Current','Charging power'):
        assert value(config,state,name,'available') is False


@pytest.mark.parametrize("status", ["charger_charging", "charger_pause", "charger_end", "charger_free", "charger_fault", None])
def test_phase_cache_survives_full_polls_and_obeys_charging_status(config, state, status):
    from custom_components.tuya_local.device import TuyaLocalDevice

    # Use the real transport cache merge; any nonpersistent reference can erase DP6.
    transport = Mock()
    transport._cached_state = dict(state)
    transport._children = []
    for definition in config.all_entities():
        child = Mock()
        child._config = definition
        transport._children.append(child)
    packet = base64.b64encode(
        (2400).to_bytes(2, "big") + (32000).to_bytes(3, "big")
        + (7680).to_bytes(3, "big") + (159).to_bytes(4, "big")
    ).decode()
    transport._api.status.return_value = {"dps": {"3": "charger_charging", "6": packet}}
    TuyaLocalDevice._refresh_cached_state(transport)
    assert transport._cached_state["6"] == packet

    transport._api.status.return_value = {"dps": {"3": status}}
    for _ in range(3):
        TuyaLocalDevice._refresh_cached_state(transport)
        assert transport._cached_state["6"] == packet
        for name in ("Voltage", "Current", "Charging power"):
            assert value(config, transport._cached_state, name, "available") is (status == "charger_charging")
        assert value(config, transport._cached_state, "Phase session energy") == 1.59

    stopped_packet = base64.b64encode(bytes(8) + (170).to_bytes(4, "big")).decode()
    transport._api.status.return_value = {"dps": {"3": "charger_pause", "6": stopped_packet}}
    TuyaLocalDevice._refresh_cached_state(transport)
    assert transport._cached_state["6"] == stopped_packet
    assert value(config, transport._cached_state, "Phase session energy") == 1.70
