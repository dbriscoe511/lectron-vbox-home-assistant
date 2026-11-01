"""Render the actual package templates with Home Assistant's template engine."""
import asyncio
from pathlib import Path
import yaml
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template

PACKAGE = yaml.safe_load((Path(__file__).resolve().parents[1] / 'home-assistant/lectron_charging.yaml').read_text())


def test_fault_details_unknown_and_all_bits(tmp_path):
    async def check():
        hass = HomeAssistant(str(tmp_path))
        sensor = next(x for x in PACKAGE['template'][0]['sensor'] if x['name'] == 'Lectron fault details')
        hass.states.async_set('binary_sensor.lectron_v_box_pro_problem', 'unavailable', {'fault_code': 0})
        assert Template(sensor['availability'], hass).async_render() is False
        hass.states.async_set('binary_sensor.lectron_v_box_pro_problem', 'on', {'fault_code': 131071})
        assert Template(sensor['availability'], hass).async_render() is True
        state = Template(sensor['state'], hass).async_render()
        assert len(state) <= 255
        labels = Template(sensor['attributes']['complete_details'], hass).async_render()
        assert len(labels) == 17 and 'leakagecurr_alarm' in labels and 'unknown_fault_bits' in labels
    asyncio.run(check())


def test_cost_requires_rate_and_uses_session_kwh(tmp_path):
    async def check():
        hass = HomeAssistant(str(tmp_path))
        sensor = PACKAGE['template'][0]['sensor'][0]
        hass.states.async_set('sensor.lectron_v_box_pro_session_energy', '12.34')
        hass.states.async_set('input_number.lectron_flat_electricity_rate', '0')
        assert Template(sensor['availability'], hass).async_render() is False
        hass.states.async_set('input_number.lectron_flat_electricity_rate', '0.15')
        assert Template(sensor['availability'], hass).async_render() is True
        assert Template(sensor['state'], hass).async_render() == 1.85
    asyncio.run(check())
