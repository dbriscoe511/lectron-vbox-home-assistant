# Charging test — November 6, 2026

Lectron V-BOX Pro NACS Wi-Fi, HW V1.2 / SW V2.0.1, hardwired. Home Assistant
2026.10.4 with Tuya Local 2026.10.0. Times below use America/Denver.

## Automatic start

The plug report changed to connected at 21:09:16.613. HA's existing automatic
start script ran, and the charger reported charging at 21:09:20.579. The script
finished its five-minute observation at 21:14:16.635. Its optional vehicle-start
hook was not triggered. No manual vehicle query or wake command was sent.

The first test command was at 21:14:18.754, more than five minutes after plug-in.
Before that, charging was around 239–240 V, 39.3 A and 9.3 kW at the 40 A setting.
The car's AC target was 80% and was left unchanged.

This verifies the existing HA automatic-start path for this plug-in. It does
not establish startup behavior with HA or Internet access unavailable.

## Current control

Commands used HA's current selector over the existing Tuya Local connection.
The table shows settled values from the final 40 seconds of each observation
window. Measurements come from the charger's DP6 reports, not an independent meter.

| Setting | Observation window | Measured current | Reported power |
| --- | --- | --- | --- |
| 32 A | 90 seconds | 31.42–31.45 A | 7.499–7.506 kW |
| 16 A | 60 seconds | 15.64–15.66 A | 3.753–3.757 kW |
| 48 A | 120 seconds | 47.26 A | 11.179–11.196 kW |
| 40 A | 60 seconds, restored | 39.38–39.42 A | 9.348–9.371 kW |

No fault was reported during these windows. This is a short functional test,
not a long-duration thermal test or a verification of the electrical installation.

## Stop, Manual Start and restoration

Automatic resume was held during the control tests. No vehicle start/stop hook
was called.

- At 21:20:10.615, a local stop request was sent. The charger reported stopped
  by 21:20:15.634. The phase packet also reported zero voltage/current/power.
- Manual Start was selected while stopped. It remained stopped for the
  15-second observation before the explicit local start request.
- The local start request resumed charging with positive reported power by
  21:20:40.825. A second local stop was confirmed at 21:21:05.915.
- Plug and Charge was selected at 21:21:05.926. Charging resumed automatically
  by 21:21:11.005, without another explicit start request. Automatic resume
  was still held, and no vehicle hook was called.
- Final readback confirmed 40 A, immediate/Plug and Charge mode, positive power,
  automatic resume enabled, no reported fault and the unchanged 80% AC target.

The test helper initially waited for the editable mode selector to show Plug
and Charge. Charging resumed first, which correctly made that selector
unavailable. That assertion timed out. The persistent read-only mode sensor
reported `immediate`, and fresh phase packets showed charging at about 9.34 kW.
Those reports confirm restoration. The original error log was retained; the
helper's assertion was corrected for future use without rerunning the controls.

## Session energy

The first captured phase packet after plug-in had a zero energy counter.
At the first stop, its final four bytes were `00 00 00 9f`, or 159 / 100 =
**1.59 kWh**. This matched the reported DP25 checkpoint and the lifetime-meter
increase since plug-in.

The stopped packet was `AAAAAAAAAAAAAACf`: zero V/I/P with energy retained.
On local restart without unplugging, the energy counter retained 1.59 kWh and
continued increasing. A local stop/start does not reset this observed counter.

Values above 2.55 kWh, the natural charging end and a physical unplug/replug
cycle are still being collected. The retained counter must not be presented as
an accumulating lifetime meter or assumed to reset on every start request.

## Reporting gaps

Full status polls omit DP6 on this unit. During the early part of this test,
phase reports arrived about every ten seconds, with brief unavailable periods
when a full poll cleared the nonpersistent field. The last valid report before
a longer gap was at 21:23:41.697, showing 2.04 kWh. The charging status remained
on while phase energy, current and power became unavailable. No new Tuya Local
warning/error was found in the HA log tail during this gap.

This is a reporting limitation to resolve or document before upstream submission.
Do not replace missing samples with zero, retain stale power as current, or
claim the larger counter range has been observed yet. Passive capture continues.
An explicit DP6 refresh through Tuya Local's existing `force` mechanism is a
possible follow-up, but has not been applied or tested on this charger.

Raw captures and control timestamps stay private. This file contains selected
validation results only. State capture records changes exposed by HA, including
the DP6 attribute; it does not capture every identical network frame.
