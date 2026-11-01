"""Telemetry semantics, missing reports, and limited writes are the contract."""
import base64
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock

import pytest
import yaml

from custom_components.tuya_local.helpers.device_config import TuyaDeviceConfig
from custom_components.tuya_local.sensor import TuyaLocalSensor
from custom_components.tuya_local.switch import TuyaLocalSwitch

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "devices" / "lectron_vbox_pro.yaml"


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
    return next(item for item in config.all_entities() if item.name == name)


def value(config, state, name, field="sensor"):
    return entity(config, name).find_dps(field).get_value(device(state))


def test_energy_scale_and_state_classes(config, state):
    assert value(config, state, "Total energy") == 1234.56
    assert value(config, state, "Session energy") == 12.34
    assert entity(config, "Total energy").find_dps("sensor").state_class == "total_increasing"
    assert entity(config, "Session energy").find_dps("sensor").state_class is None


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


@pytest.mark.parametrize("name,dp", [("Charging power", "9"), ("Single phase power", "5")])
def test_missing_power_is_unavailable_and_does_not_persist(config, state, name, dp):
    assert value(config, state, name) is None
    assert value(config, state, name, "available") is False
    ent = entity(config, name)
    assert ent.find_dps("sensor").persist is False
    assert ent.find_dps("available").persist is False
    state[dp] = 7680
    assert value(config, state, name) == 7.68
    assert value(config, state, name, "available") is True


def test_optional_phase_decoder_is_explicitly_unverified_and_disabled(config, state):
    packet = (2400).to_bytes(2, "big") + (32000).to_bytes(3, "big") + (7680).to_bytes(3, "big")
    state["6"] = base64.b64encode(packet).decode()
    assert value(config, state, "Voltage") == 240
    assert value(config, state, "Current") == 32
    raw = yaml.safe_load(PROFILE.read_text())
    for name in ("Voltage", "Current"):
        assert next(e for e in raw["entities"] if e.get("name") == name)["hidden"] is True


def test_profile_only_writes_charging_request_and_excludes_sensitive_controls(config):
    raw = yaml.safe_load(PROFILE.read_text())
    writable = [item for item in raw['entities'] if item['entity'] not in {'sensor', 'binary_sensor'}]
    assert len(writable) == 1
    assert writable[0]['entity'] == 'switch'
    assert writable[0]['dps'] == [{'id': 18, 'type': 'boolean', 'name': 'switch'}]
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

