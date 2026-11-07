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

At the second local stop, DP6 retained 1.65 kWh. DP25 reported 0.06 kWh,
matching the additional 0.06 kWh on the lifetime meter since the first stop.
In this test, DP6 accumulated across local pauses within the plugged session;
DP25 reported the most recently completed charging segment. They should not be
expected to match after each restart.

At 21:27:41.718, packet `CVsAmfwAJJgAAAEL` had final bytes `00 00 01 0b`:
267 / 100 = **2.67 kWh**, with 9.368 kW reported. This is real evidence of the
carry beyond the final byte's 2.55 kWh range. Later packets reported 2.98 kWh at
21:29:41.729 and 3.29 kWh at 21:31:41.742. The highest two energy bytes remained
zero; this test has not exercised the full 32-bit range.

The 2.04 → 2.67 kWh increase over four minutes implies about 9.45 kW average;
the next two 0.31 kWh increases over two minutes each imply about 9.3 kW.
Those are consistent with the surrounding 9.34–9.37 kW reports at the counter's
0.01 kWh resolution. Missing power samples prevent a complete measured-power
integral, and all these readings come from the same charger.

Natural charging completion and a physical unplug/replug cycle remain pending.
The retained counter must not be presented as an accumulating lifetime meter or
assumed to reset on every start request.

## Reporting gaps

Full status polls omit DP6 on this unit. During the early part of this test,
phase reports arrived about every ten seconds, with brief unavailable periods
when a full poll cleared the nonpersistent field. The last valid report before
a longer gap was at 21:23:41.697, showing 2.04 kWh. The charging status remained
on while phase energy, current and power became unavailable. No new Tuya Local
warning/error was found in the HA log tail during this gap.

Reports resumed at 21:27:41.718 after a four-minute gap, followed by reports at
21:29:41.729 and 21:31:41.742, two minutes apart. Capture stayed healthy throughout;
phase sensors became unavailable between these sparse reports.

This is a reporting limitation to resolve or document before upstream submission.
Do not replace missing samples with zero or retain stale power as current.
Passive capture continues.
An explicit DP6 refresh through Tuya Local's existing `force` mechanism is a
possible follow-up, but has not been applied or tested on this charger.

Raw captures and control timestamps stay private. This file contains selected
validation results only. State capture records changes exposed by HA, including
the DP6 attribute; it does not capture every identical network frame.
