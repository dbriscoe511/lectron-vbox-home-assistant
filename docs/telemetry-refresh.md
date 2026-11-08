# DP6 reporting and retention — November 7, 2026

## Current profile

DP6 uses Tuya Local's defaults: retain the last reported value between status
polls, with no forced refresh. The YAML omits both `persist` (default true) and
`force` (default false) on every DP6 reference. This is a device-profile change;
Tuya Local's runtime code is unchanged.

Voltage, current and charging power keep their existing charging-status guards.
A stopped or unknown charging state hides an earlier positive phase reading.
Phase session energy retains its last reported counter through a stop and
updates when the charger sends a new packet. Before the first DP6 report,
phase readings remain unavailable. Raw packet history stays enabled in Recorder.

No age indicator, extra dashboard card, timer or polling loop is added.
The charger reports on its own cadence; the last 15 intervals in the measured
charge were within about 0.03 seconds of 120 seconds. A retained value is the
last device report, as with Tuya Local's normal sensor behavior. Charging state
still comes from its separate status datapoint.

The revised profile is installed in HA and mirrored in the prepared upstream
profile. Configuration validation and a targeted entry reload passed while the
charger was disconnected. Current, mode, vehicle target and entity identities
were preserved. No charging/vehicle command or full HA restart was used.

## Earlier forced-refresh trial

The earlier trial used `force: true` with `persist: false`. The
[November 7 charge](charging-test-2026-11-07.md) ran normally and delivered
15.18 kWh, matching DP6, DP25 and the lifetime-meter increase. The collector
recorded 81 distinct phase packets with no HA read errors. Reports were initially
roughly ten seconds apart, then settled around two minutes apart.

Under that earlier profile, status polls that omitted DP6 cleared its cached
value. Phase energy was consequently unavailable about 65% of charging time.
That was a profile-cache behavior between reports; it does not establish
network packet loss. Forced requests did not demonstrate a need to override
normal reporting, so the trial flag has been removed.

Before the trial, physical unplug at 11:03:02 MST produced DP6
`AAAAAAAAAAAAAAAA` (12 zero bytes). DP25 and lifetime energy retained their
completed readings. The next charge began DP6 at zero and ended at 15.18 kWh.

## Validation

114 local tests passed against the pinned Tuya Local transport. The cache
regression exercises its real full-poll merge: omitted DP6 survives successive
polls, updated charging status still hides stopped power, and a new phase
packet replaces the retained value. Registration requests no forced datapoints.

33 upstream device-config tests passed, along with Ruff, translation, duplicate
and profile YAML checks. No perfect duplicate profile was found. Revised
retention has not yet been observed during another physical charge; the test
covers the actual cache mechanism with synthetic packets and the recorded
report cadence supplies the device evidence. The earlier private capture is
complete; existing Recorder history continues without recurring check-ins.
