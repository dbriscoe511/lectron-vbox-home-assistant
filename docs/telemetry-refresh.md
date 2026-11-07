# DP6 refresh trial — November 7, 2026

Installed in HA on November 7 at 11:07 MST after the car was unplugged.
Configuration validation passed and the existing charger entry reloaded.
Charging performance with this option has not been validated yet.

The profile now marks the phase-energy sensor's read-only DP6 with `force: true`.
Tuya Local registers that datapoint once and requests it through its existing
charger connection using `updatedps`. No extra Tuya client or charging command
is involved. Current, operating mode and vehicle battery target are unchanged.

`persist: false` stays in place. A status response that omits DP6 can still clear
the live readings; this trial checks whether explicit requests provide fresh
phase reports reliably. It does not make cached readings proof of current power
or establish that the earlier reporting gaps were network packet loss.

The next charge should establish:

- Whether the explicit request produces a valid 12-byte DP6 response.
- The interval between fresh phase reports and any unavailable periods.
- Whether local start, charging and the eventual stop remain correctly reported.
- Whether the next plug-in starts from the zero counter observed at unplug.

Keep the existing 40 A setting and 80% vehicle target. Use HA Recorder's existing
`raw_phase_packet` history for the next cycle. No repeated current/start/stop
experiments or vehicle wakes are needed to test telemetry freshness.

Before activation, physical unplug at 11:03:02 MST produced DP6
`AAAAAAAAAAAAAAAA`: all 12 bytes zero, including session energy. DP25 and the
lifetime meter retained their completed readings. This reset preceded the reload.

A private HA-state collector is armed for the next plug-in. It waits up to seven
days, then captures for up to 12 hours from plug-in and finishes three minutes
after charging stops or the vehicle disconnects. It samples existing HA states
every 15 seconds while waiting and every two seconds during the cycle. Resuming
within the end buffer continues the capture. It uses no extra Tuya connection,
charging command or vehicle query. Existing Recorder history remains enabled.
The temporary collector runs on the desktop; desktop sleep or shutdown can
interrupt it. It records state changes, not every identical network frame.

Validation: 108 local tests and 33 upstream config tests passed. A transport
registration test confirms the only explicitly requested datapoint is DP6.
Both profile YAML files pass lint; translation and duplicate checks are tracked
with the upstream preparation. A successful static check is not a successful
physical charging test.
