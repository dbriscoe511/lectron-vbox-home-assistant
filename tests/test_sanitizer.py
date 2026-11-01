import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('sanitize', Path(__file__).resolve().parents[1] / 'tools/sanitize_diagnostics.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_nested_metadata_identifiers_and_strings_are_not_copied():
    raw = {'key': 'synthetic-private-value', 'ip': '198.51.100.1', 'dps': {'1': 1234, '22': 'synthetic-meter', '6': 'rawbytes', '105': 'rawhistory', '3': 'synthetic-private-value', '23': 'synthetic-private-value', '24': float('nan'), '18': True}}
    result = mod.sanitize(raw)
    assert result == {'dps': {'1': 1234, '3': '<unknown>', '23': '<redacted>', '18': True}}
    assert 'synthetic-private-value' not in json.dumps(result)
