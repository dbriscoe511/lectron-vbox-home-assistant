# Historical energy backfill

Historical cloud energy and the local cumulative meter are separate sources.
The included tools create a **separate external statistics series** named
`lectron_history:charging_energy`; they never rewrite live sensor statistics or
guess the energy between the last cloud day and the first local sample.

## Obtain and verify source data

The tested owner's logged-in Lectron Android SDK provided the native app's
**DP1 lifetime-meter difference** statistics. This is account-authorized cloud access, not a public API or an
unauthenticated endpoint. Local keys alone do not grant cloud-history access.
No Android package, app database, account session or credentials are distributed.

Treat these as **cloud-reported daily energy**, not independently validated
midnight meter readings. The native app uses `thing.m.dp.rang.stat.day.list`
and `.month.list`, version1.0, with `devId`, `dpId: "1"`, `type: "minux"`.
Daily ranges use `startDay`/`endDay` as `yyyyMMdd`; monthly ranges use
`startMonth`/`endMonth` as `yyyyMM`. Hourly queries use `.hour.list` and
`date: "yyyyMMdd"`. These names/parameters were verified in the tested app;
they are not a supported public Lectron API contract. Responses return a
date-keyed numeric map, sometimes nested under `result`, already in **kWh**.
`min` identifies earliest available coverage: zeros before it are not evidence
of historical zero consumption. Preserve fractional kWh rather than copying
the app UI's truncated display.

The source assigns cumulative-meter deltas by **report time**; a report just
after midnight can include energy delivered before midnight. Preserve native
date labels and describe this reporting-boundary approximation.

DP25 is a session counter: summing arbitrary progress
samples can overcount energy. Confirm the endpoint's aggregation behavior using
completed-session records, the app's charts and/or cumulative meter deltas.
Daily/monthly agreement is a useful consistency check, not independent proof.

An alternative legacy `getDataPointStat` DP25 endpoint mixed already formatted kWh and raw centikWh
inside the same response. Their `total` field was not reliable. Do not apply a
single scale to the entire response, infer units from magnitude, or assume a
particular list position is always formatted. Verify units with overlapping
requests, the product schema and closed-month reconciliation. Prefer the
native DP1 difference endpoint rather than importing these DP25 sums. Preserve raw
responses and the normalization evidence **privately**.

Prepare a private CSV containing only verified **closed daily periods**:

```csv
date,energy_kwh
2026-01-01,12.34
2026-01-02,0
2026-01-03,8.50
```

An explicit source zero is allowed; missing dates are not zeros. Split actual
gaps into distinct named series. Do not combine overlapping daily, monthly and
session aggregates. Exclude the current partial day and keep its totals in the
private archive until it closes. If only monthly data exists, preserve it as
monthly data rather than claiming daily detail.

## Prepare without changing HA

```bash
.venv/bin/python tools/prepare_history.py /private/history.csv \
  --timezone America/Denver --closed-before 2026-01-04 \
  --output /private/lectron-history.json
```

The payload and immutable manifest are created with mode600; existing output
files are not overwritten. The manifest records source/payload hashes, coverage,
timezone, total and granularity. Keep both outside Git. Review them before import.

HA stores long-term statistics in hourly buckets. A daily increment is assigned
to the **final local-hour bucket** of that day, with a zero baseline before the
coverage starts. These are daily aggregates: the assigned hour is a chart encoding,
not the charging time. No raw states, hourly power, temperature, plug events or
vehicle SOC are fabricated. Calendar boundaries use IANA timezone rules, including
23/25-hour DST days. Use daily/monthly chart aggregation for this series.

## Import and verify

Back up HA first. Requires HA admin access and `aiohttp` (included with the test
dependencies). Store an existing token in a private mode600 file; never pass it
as a command argument or commit it. A dry run does not connect:

```bash
.venv/bin/python tools/import_history.py /private/lectron-history.json
.venv/bin/python tools/import_history.py /private/lectron-history.json \
  --url http://homeassistant.local:8123 --token-file /private/ha-token \
  --backup /private/statistics-before-import.json --apply
```

The importer checks existing rows and refuses conflicting data. It saves the
previous series, submits `recorder/import_statistics`, and queries actual stored
rows afterward: the initial ACK only queues work. Repeating the same payload
upserts the same statistic-ID/timestamp pairs rather than adding energy twice.
Use a fresh backup path on each run. Tested API: HA2026.10.4; later versions may
change. No direct database writes are required.

Add the external statistic to a native statistics graph with `period: day` and
`stat_types: [change]`. It is a statistic ID, not a normal state entity. If the
aggregation has been verified and coverage does not overlap live collection,
you can add it separately under Energy → Individual devices. Label historical
cloud totals clearly and keep the live local meter as the ongoing source.

An imported chart does not calibrate utility-meter helper states. Those helpers
initially count from installation. Do not adjust live sums or calibrate today's
helper merely to make lifetime/cloud totals agree: missing periods, losses and
counter changes must remain explicit.

## Advanced: a single continuous live sensor

The installed development system also tested a one-time migration into the
existing recorder sensor statistic. This is **not what the shipped external-only
importer does**. It requires proving a clean handoff: unchanged lifetime meter
between the cloud cutoff and the first local sample, with no overlapping energy.

Privately export existing hourly/five-minute rows and metadata first. Preserve
the original metadata and an immutable target sum at one fixed live anchor.
Import history strictly before the first live hour (omit historical `state`
unless actual cumulative readings exist). Then adjust both live statistics
tables through `recorder/adjust_sum_statistics`, starting at the first live
five-minute timestamp, by **target anchor sum minus current anchor sum**.
Never blindly add the recovered total again. Verify queued writes, daily/monthly
totals, the anchor, and newly generated five-minute/hourly rows before completing
the operation. Keep an operation manifest for safe retries.

Preserve real hourly data for a partial cutoff day if available; exclude future
zero buckets. Do not force an unexplained lifetime-meter difference into recovered
usage. If the cutoff or units cannot be established, use the separate external
series instead. This advanced path needs an installation-specific review; no
generic automated same-sensor rewrite is included.
