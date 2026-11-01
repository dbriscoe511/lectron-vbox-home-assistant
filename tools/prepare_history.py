#!/usr/bin/env python3
"""Prepare closed daily cloud totals as a separate HA statistics series."""
import argparse
import csv
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo


def prepare(rows, timezone_name, closed_before, statistic_id="lectron_history:charging_energy"):
    """Use explicit kWh totals; never guess raw scaling or fill missing dates."""
    if not statistic_id.startswith("lectron_history:") or statistic_id.count(":") != 1:
        raise ValueError("Use a dedicated lectron_history: statistic ID.")
    tz = ZoneInfo(timezone_name)
    cutoff = date.fromisoformat(closed_before)
    values = {}
    for row in rows:
        day = date.fromisoformat(row["date"])
        try:
            energy = Decimal(row["energy_kwh"])
        except InvalidOperation as exc:
            raise ValueError("Invalid energy_kwh") from exc
        if not energy.is_finite() or energy < 0:
            raise ValueError("Energy must be finite and nonnegative.")
        if day >= cutoff:
            raise ValueError("Current/open periods must be excluded before preparation.")
        if day in values:
            raise ValueError("Duplicate source date.")
        values[day] = energy
    days = sorted(values)
    if not days:
        raise ValueError("No daily records.")
    if any(b - a != timedelta(days=1) for a, b in zip(days, days[1:])):
        raise ValueError("Coverage has gaps; split into separately named series, do not invent zeros.")

    def boundary(day):
        return datetime.combine(day, time(), tzinfo=tz).astimezone(timezone.utc)

    # Daily-only source: allocate the increment to its final local hour.
    # This is a chart encoding, not evidence of the hour energy was delivered.
    total = Decimal(0)
    stats = [{"start": (boundary(days[0]) - timedelta(hours=1)).isoformat(), "sum": 0.0}]
    for day in days:
        total += values[day]
        stats.append({"start": (boundary(day + timedelta(days=1)) - timedelta(hours=1)).isoformat(), "sum": float(total)})
    return {
        "type": "recorder/import_statistics",
        "metadata": {"statistic_id": statistic_id, "source": "lectron_history", "name": "Lectron cloud daily energy (historical)", "mean_type": 0, "has_sum": True, "unit_class": "energy", "unit_of_measurement": "kWh"},
        "stats": stats,
    }, {"timezone": timezone_name, "coverage_start": str(days[0]), "coverage_end": str(days[-1]), "days": len(days), "energy_kwh": str(total), "granularity": "daily; assigned to final local hour for HA charts; actual intraday timing unknown", "closed_before": closed_before}


def write_private(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents silently replacing an audited import manifest.
    with path.open("x", encoding="utf-8") as out:
        path.chmod(0o600)
        json.dump(data, out, indent=2, allow_nan=False)
        out.write("\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv", type=Path, help="Private CSV with date,energy_kwh columns")
    p.add_argument("--timezone", required=True)
    p.add_argument("--closed-before", required=True, help="Exclusive local date cutoff; exclude open days")
    p.add_argument("--statistic-id", default="lectron_history:charging_energy")
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    with args.csv.open() as f:
        payload, manifest = prepare(csv.DictReader(f), args.timezone, args.closed_before, args.statistic_id)
    manifest["source_sha256"] = hashlib.sha256(args.csv.read_bytes()).hexdigest()
    manifest["payload_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    write_private(args.output, payload)
    write_private(args.output.with_suffix(".manifest.json"), manifest)
    print(f"Prepared {manifest['days']} closed daily records; {manifest['energy_kwh']} kWh. No HA changes made.")
