# Lectron command audit

Hardware V1.2, firmware V2.0.1, NACS Wi-Fi model. This audit uses the charger's
[SDK schema](manufacturer-schema.json), local reports, and
[Lectron's mode guide](https://ev-lectron.com/pages/v-box-pro-q-a).
The SDK export is an alternative to the Tuya Cloud QueryThingsDataModel API;
it is not represented as a response from that API.

## Controls

| DP | Function | Status |
| --- | --- | --- |
| 4 | Charging current | 16/32/40/48 A selector; all four settings produced sustained measured draw during the November 6 test. Original 40 A restored. See [charging evidence](charging-test-2026-11-06.md). |
| 14 | Operating mode | Plug and Charge, Manual Start, Scheduled Charge. Scheduled → Plug and Charge readback verified; November 6 testing confirmed Manual Start waits for a local request and switching back to Plug and Charge resumes charging. |
| 18 | Charging request | Local stops and restart with positive power confirmed on November 6 without vehicle hooks. Vehicle acceptance remains separate. |

Mode changes are disabled while charging or when the stopped state is unknown.
The selector changes the native mode only. It does not create/delete Lectron
schedule entries or override the separate HA weekday policy.

## Fields still being investigated

| DP | Schema name | What remains |
| --- | --- | --- |
| 17 | `energy_charge` | Schema scale is 2, but saved values and related EVSE profiles do not establish the actual units on this firmware. Not exposed as a write control. |
| 14: `charge_energy` | Fixed-energy mode | Advertised in the schema and Lectron's general guide, but absent from the owner's app UI. Not selectable until confirmed on this unit. |
| 19 | `local_timer` | Raw layout is undocumented in this unit's schema and was absent from local reports. Other brands' two-byte formats are not assumed to apply. Schedule editing stays in the app/HA. |
| 33 | `mode_set` | Raw capability/mode payload, not observed locally. No guessed writes. |
| 105 | `charger_record` | Raw charging record, not observed locally. Cloud backfill is already available separately. |

## Fields that are not normal controls

DP11/12 are undocumented alarm/protection payloads. DP16 clears energy data.
DP27's online status is not a useful user command despite its writable schema
flag. DP22 identifies the private meter. None needs a write control for normal
charging. No reset, protection or identity write is included.

## Remaining passive observations

The [November 6 charging test](charging-test-2026-11-06.md) covered automatic
startup, the five-minute observation, all four current settings, Manual Start,
local stop/restart and restoration. DP6 energy matched DP25 and lifetime-meter
delta at a stop and retained its value across a local restart without unplugging.

The raw counter has now carried into the next byte: `00 00 01 0b` = 2.67 kWh,
followed by 2.98 and 3.29 kWh. DP6 retained energy across local pauses, while DP25
and the lifetime meter reflected each completed segment (1.59 then 0.06 kWh).
The unattended overnight stop was captured at 01:04 MST November 7: status
`paused`, vehicle still connected, zero V/I/P with DP6 retaining 36.73 kWh.
DP25's final 35.08 kWh segment plus the two test segments exactly matched DP6
and the lifetime-meter delta. The next cached vehicle report showed 80%, but
that does not prove the cause of the stop. No preceding HA stop action was
found in the inspected charging activity.

The bounded capture is complete. Physical unplug/replug reset remains unverified;
no more scheduled checks are planned. Existing HA Recorder packet history stays
enabled. DP6 reports resumed after a four-minute gap but remained sparse;
see the charging evidence before treating live telemetry as fully validated.
Do not induce electrical faults or reset counters as a validation test.

## Upstream evidence and checks

Tuya Local asks for the shared product ID, model, local DPS warning log and the
device data model. Any DP missing from discovery must be optional. Their
[agent instructions](https://github.com/make-all/tuya-local/blob/main/AGENTS.md)
also require config tests, duplicate matching, translation checks and lint.

We have the product ID, SDK schema, authenticated local snapshots, live HA
operation and saved charging-test evidence. The original **LOCAL DPS** discovery
warning has rotated out of the HA logs. Do not label a diagnostics snapshot as
that warning; attach it with its actual origin and ask whether the maintainer
needs a fresh discovery log. Do not remove/re-add the working charger just to
generate one. Private keys, meter IDs and network/account identifiers stay out
of the submission.

The new-device template currently says submissions are paused. The upstream
patch and PR description remain prepared and unsubmitted. The completed checks,
telemetry limitation and unverified unplug/reset behavior are documented above.
