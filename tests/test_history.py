import importlib.util
from pathlib import Path
from datetime import datetime
import pytest

spec = importlib.util.spec_from_file_location("prepare_history", Path(__file__).resolve().parents[1] / "tools/prepare_history.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_daily_sum_and_dst_fall_back():
    rows = [{"date": "2026-10-31", "energy_kwh": "10.25"}, {"date": "2026-11-01", "energy_kwh": "20.50"}]
    p, m = mod.prepare(rows, "America/Denver", "2026-11-02")
    assert [x["sum"] for x in p["stats"]] == [0, 10.25, 30.75]
    assert datetime.fromisoformat(p['stats'][2]['start']) - datetime.fromisoformat(p['stats'][1]['start']) == mod.timedelta(hours=25)
    assert m['energy_kwh'] == '30.75'
    assert all('state' not in row for row in p['stats'])


@pytest.mark.parametrize("values", [[('2026-01-01','NaN')], [('2026-01-01','-1')], [('2026-01-01','Infinity')], [('2026-01-01','1'),('2026-01-01','1')], [('2026-01-01','1'),('2026-01-03','1')], [('2026-02-01','1')]])
def test_bad_or_open_coverage_rejected(values):
    with pytest.raises(ValueError):
        mod.prepare([dict(date=d, energy_kwh=v) for d,v in values], 'UTC', '2026-02-01')


def test_live_sensor_id_rejected():
    with pytest.raises(ValueError):
        mod.prepare([dict(date='2026-01-01', energy_kwh='1')], 'UTC', '2026-02-01', 'sensor.live_energy')
