# Lectron command audit

Hardware V1.2, firmware V2.0.1, NACS Wi-Fi model. This audit uses the charger's
[SDK schema](manufacturer-schema.json), local reports, and
[Lectron's mode guide](https://ev-lectron.com/pages/v-box-pro-q-a).
The SDK export is an alternative to the Tuya Cloud QueryThingsDataModel API;
it is not represented as a response from that API.

## Controls

| DP | Function | Status |
| --- | --- | --- |
| 4 | Charging current | 16/32/40/48 A selector; 32 A setting accepted, 40 A restored and charging observed. Sustained 32 A and 48 A still need a charging test. |
| 14 | Operating mode | Plug and Charge, Manual Start, Scheduled Charge. Local Scheduled → Plug and Charge write/readback verified. Manual Start needs the next charging test. |
| 18 | Charging request | Start/stop supported; an actual stop and restart with positive power were observed. Vehicle acceptance remains separate. |

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

## Next normal charge

1. Save local packet/state history while plugged in and waiting.
2. Request start and observe the local charger for five full minutes before any
   manual vehicle query or wake command.
3. Check measured current and power against the app, including a sustained
   supported current change when practical.
4. Verify Manual Start, stop/start feedback, and the transition back to Plug and
   Charge while stopped. Preserve the user's original current and battery target.
5. Compare phase session energy with DP25 and the lifetime-meter increase above
   2.55 kWh; check pause/end and a real unplug/replug session reset.

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
patch and PR description can be prepared now; physical items above remain
explicitly pending until the next charge.
