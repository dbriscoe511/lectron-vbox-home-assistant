#!/usr/bin/env python3
"""Import prepared external history through HA's admin WebSocket API."""
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import aiohttp

from prepare_history import write_private


async def run(args):
    payload = json.loads(args.payload.read_text())
    meta = payload["metadata"]
    sid = meta["statistic_id"]
    if payload.get("type") != "recorder/import_statistics" or not sid.startswith("lectron_history:") or meta["source"] != "lectron_history":
        raise ValueError("Only prepared external Lectron history imports are supported.")
    if meta["unit_of_measurement"] != "kWh" or not payload["stats"]:
        raise ValueError("Expected nonempty kWh statistics.")
    starts = [datetime.fromisoformat(x["start"]) for x in payload["stats"]]
    if any(x.tzinfo is None or x.minute or x.second or x.microsecond for x in starts):
        raise ValueError("Statistics must use aware whole-hour timestamps.")
    if starts != sorted(set(starts)) or max(starts) >= datetime.now(timezone.utc):
        raise ValueError("Duplicate, unordered, or future timestamps.")
    sums = [x["sum"] for x in payload["stats"]]
    import math
    if any(not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0 for x in sums) or sums != sorted(sums):
        raise ValueError("Expected finite increasing sums.")
    if not args.apply:
        print(f"Validated {len(starts)} rows. Pass --apply to import; no connection made.")
        return
    if args.token_file.stat().st_mode & 0o077:
        raise ValueError("Token file must be private (chmod 600).")
    url = args.url.rstrip("/").replace("https://", "wss://", 1).replace("http://", "ws://", 1) + "/api/websocket"
    async with aiohttp.ClientSession() as session, session.ws_connect(url) as ws:
        await ws.receive_json()
        await ws.send_json({"type": "auth", "access_token": args.token_file.read_text().strip()})
        if (await ws.receive_json())["type"] != "auth_ok":
            raise RuntimeError("Home Assistant authentication failed.")
        counter = 0
        async def call(message):
            nonlocal counter
            counter += 1
            await ws.send_json({**message, "id": counter})
            while True:
                result = await ws.receive_json(timeout=60)
                if result.get("id") == counter:
                    if not result.get("success"):
                        raise RuntimeError(f"HA rejected {message['type']}; inspect privately.")
                    return result.get("result")
        query = {"type": "recorder/statistics_during_period", "start_time": starts[0].isoformat(), "end_time": (starts[-1] + timedelta(hours=1)).isoformat(), "statistic_ids": [sid], "period": "hour", "types": ["sum"]}
        metadatas = await call({"type": "recorder/list_statistic_ids"})
        existing_meta = next((x for x in metadatas if x["statistic_id"] == sid), None)
        if existing_meta:
            expected_meta = {"source": "lectron_history", "unit_class": "energy", "statistics_unit_of_measurement": "kWh", "has_sum": True, "mean_type": 0}
            if any(existing_meta.get(k) != v for k, v in expected_meta.items()):
                raise ValueError("Existing statistics metadata differs; refusing to relabel it.")
            # Preserve an existing user-visible name.
            payload["metadata"]["name"] = existing_meta.get("name")
        before = await call(query)
        write_private(args.backup, {"captured_at": datetime.now(timezone.utc).isoformat(), "metadata": existing_meta, "statistics": before})
        expected = {x.timestamp(): v for x, v in zip(starts, sums)}
        for row in before.get(sid, []):
            ts = row["start"] / 1000
            if ts not in expected or abs(row["sum"] - expected[ts]) > 1e-6:
                raise ValueError("Existing series differs; refusing to replace it.")
        await call(payload)
        # The ACK only enqueues the recorder job. Read back the stored results.
        for attempt in range(20):
            after = await call(query)
            actual = {x["start"] / 1000: x["sum"] for x in after.get(sid, [])}
            if all(t in actual and abs(actual[t] - v) < 1e-6 for t, v in expected.items()):
                print(f"Verified {len(expected)} imported rows; live recorder statistics were not modified.")
                return
            await asyncio.sleep(1)
        raise RuntimeError("Import acknowledged but readback did not finish; preserve manifest and inspect before retrying.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("payload", type=Path)
    p.add_argument("--url", default="http://homeassistant.local:8123")
    p.add_argument("--token-file", type=Path)
    p.add_argument("--backup", type=Path)
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()
    if args.apply and (not args.token_file or not args.backup):
        p.error("--apply requires a private --token-file and a new --backup path")
    asyncio.run(run(args))
