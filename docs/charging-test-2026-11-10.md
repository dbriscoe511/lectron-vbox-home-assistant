# Standard-retention charging test — November 10, 2026

First physical charge with the final profile: default Tuya Local retention on
DP6, no forced requests, and charging-status guards on voltage/current/power.
Times are America/Denver (MST). Source: HA Recorder history of the existing
entities. No charging, mode or vehicle command was sent for this review.

## Charging and energy

HA reported charging from 21:05:25 to 23:40:51, about 2 hours 35 minutes. The
vehicle stayed connected, status changed charging → paused, and no fault was
reported. Current was 40 A, mode immediate.

Before the charge the retained phase packet was the 12 zero bytes seen at the
earlier physical unplug, and the first charging packet reported 0.05 kWh.
Positive-power packets reported 237.7–240.8 V, 39.40–39.65 A and
9.352–9.466 kW.

The final packet, at 23:40:52, reported **24.36 kWh**. DP25 session energy
and the lifetime-meter increase (2335.00 → 2359.36 kWh) both matched at
**24.36 kWh**. This is agreement within the charger, not an independent meter.

## Retention result

**The reporting gaps seen in the November 7 trial are gone.** There were 82
distinct phase packets, including the zero packet before charging. Reports
settled at 120 seconds apart (median 120.0 s, maximum 120.1 s). Phase session
energy was unavailable for about 18 seconds of the 9,327-second charge, at the
start before the first packet. In the November 7 trial with `persist: false`
it was unavailable for about 65% of the charge.

After charging stopped, phase session energy held 24.36 kWh for about 10 hours,
until an unrelated Home Assistant restart. The retained value is in memory, so
after a restart the phase sensors stay unavailable until the next DP6 report.

Unlike the November 7 stop packet, this final packet still carried nonzero
voltage, current and power. Voltage, current and power went unavailable when
charging turned off, so the charging-status guards kept the stale values out.

## Limits

These figures use HA state history, which records changes, not every network
frame. Why charging ended was not established; no vehicle query was sent.
