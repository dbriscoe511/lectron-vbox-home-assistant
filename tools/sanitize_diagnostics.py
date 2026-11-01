#!/usr/bin/env python3
"""Allowlist plain DP values; never copy an entire diagnostic payload to issues."""
import argparse
import json
import math
import re
from pathlib import Path

# No account/device identifiers, raw buffers, network addresses, names or keys.
SAFE_DPS = {"1", "3", "4", "5", "9", "10", "13", "14", "15", "18", "23", "24", "25", "27", "101", "103"}
ENUMS = {
    "3": {"charger_free", "charger_insert", "charger_free_fault", "charger_wait", "charger_charging", "charger_pause", "charger_end", "charger_fault", "charger_suddenStop"},
    "13": {"controlpi_12v", "controlpi_12v_pwm", "controlpi_9v", "controlpi_9v_pwm", "controlpi_6v", "controlpi_6v_pwm", "controlpi_error"},
    "14": {"charge_now", "charge_energy", "charge_schedule", "charge_manual"},
    "27": {"offline", "online"},
}


def sanitize(data):
    """Accept a direct TinyTuya status object, not arbitrary nested diagnostics."""
    dps = data.get("dps")
    if not isinstance(dps, dict):
        raise ValueError("Expected a direct status object with a dps dictionary.")
    safe = {}
    for key, value in dps.items():
        key = str(key)
        if key not in SAFE_DPS:
            continue
        if value is None:
            safe[key] = None
        elif key in ENUMS:
            safe[key] = value if isinstance(value, str) and value in ENUMS[key] else "<unknown>"
        elif key == "23":
            safe[key] = value if isinstance(value, str) and re.fullmatch(r"HW V[0-9.]+,SW V[0-9.]+", value) else "<redacted>"
        elif key in {"18", "101", "103"}:
            if isinstance(value, bool):
                safe[key] = value
        elif isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
            safe[key] = value
    return {"dps": safe}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    print(json.dumps(sanitize(json.loads(args.source.read_text())), indent=2))

