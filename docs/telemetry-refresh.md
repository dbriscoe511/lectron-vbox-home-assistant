# DP6 refresh trial — November 7, 2026

Prepared for the next charging cycle. Charging performance with this option has
not been validated yet.

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
- Whether phase energy starts a new count after the physical unplug/replug.

Keep the existing 40 A setting and 80% vehicle target. Use HA Recorder's existing
`raw_phase_packet` history for the next cycle. No repeated current/start/stop
experiments or vehicle wakes are needed to test telemetry freshness.

The unplug transition is being captured separately before activating this
change, so it can be evaluated without confusing a reload with a device reset.

Validation: 108 local tests and 33 upstream config tests passed. A transport
registration test confirms the only explicitly requested datapoint is DP6.
Both profile YAML files pass lint; translation and duplicate checks are tracked
with the upstream preparation. A successful static check is not a successful
physical charging test.
