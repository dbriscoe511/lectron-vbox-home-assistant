# DP6 refresh charging test — November 7, 2026

All times are America/Denver (MST). The profile had `force: true` on DP6,
with `persist: false` retained. Installed profile hash still matched the tested
candidate at review. No configuration or charging controls changed for this review.

## Charging and energy

HA reported charging from 16:50:36 to 18:28:13, about 97 minutes 38 seconds.
The first captured DP6 packet reported 0.00 kWh with positive power, consistent
with the reset observed at the earlier physical unplug. Current remained set
to 40 A and mode immediate; the cached vehicle AC target remained 80%.

The 80 captured positive-power packets reported 235.2–238.8 V, 39.35–39.65 A
and 9.236–9.384 kW. No charger fault was reported. Charging changed to paused,
with the vehicle still connected, at the end. DP6 packet `AAAAAAAAAAAAAAXu`
reported zero V/I/P and retained **15.18 kWh** (tail `00 00 05 ee`). DP25 and
the lifetime-meter increase both matched **15.18 kWh**. Energy divided by the
reported charging duration gives about 9.33 kW average, consistent with those
samples. This is agreement within the charger, not an independent meter check
or a full integral of the sparse power samples.

The start script ran during plug-in. The captured stop script never ran, but
this review did not fetch a stop-window logbook or establish why charging ended.
Do not infer target completion from the configured 80% limit. No vehicle query,
wake, charging command or target write was sent by the capture or this review.

## Live telemetry result

**Explicit DP6 requests did not resolve the reporting gaps in this cycle.**
There were 81 distinct captured phase packets, including the final stopped
packet. Positive-power packet intervals ranged from about 6 to 120 seconds,
with a median of 80 seconds. Reports started roughly ten seconds apart and
later settled around two minutes apart. No four-minute inter-report gap was
observed in this cycle, but that difference alone does not prove improvement
from the flag.

The phase-energy sensor was unavailable for approximately 64 of the 98 charging
minutes (65%), across 59 observed intervals. The longest unavailable interval
was about 99 seconds. These durations use HA state timestamps, clipped to the
charging window. A two-second state sampler can miss shorter transitions;
it also cannot count identical network frames. The same nonpersistent DP6
backs the live phase measurements, so this remains a telemetry limitation.
Do not convert unavailable readings to zero or treat stale power as live.

The collector recorded no HA read errors and exited successfully at 18:31:14,
three minutes after charging stopped. The meter and state transitions were
captured despite sparse phase reporting. These observations do not establish
network packet loss or isolate why the charger sends DP6 intermittently.

## Capture status

The bounded next-cycle collector has finished; no recurring check was added.
Existing HA Recorder packet history remains enabled. The later read-only review
found the charger unplugged, stopped and without a fault, with 40 A, immediate
mode and the 80% AC target retained. That later state is not packet evidence of
the unplug transition, which happened after this collector ended.

Private original state logs, decoded packets and aggregate calculations remain
outside this repository. Upstream PR remains unsubmitted. Reliable live DP6
telemetry remains open; start/stop, current control and matching energy counters
have separate physical evidence.
