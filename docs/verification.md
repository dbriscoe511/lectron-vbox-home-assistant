# Verification and known limits

Verified against one Lectron V-BOX Pro NACS Wi-Fi, hardware V1.2/software V2.0.1,
Tuya 3.5, HA 2026.10.4 and Tuya Local 2026.10.0. Initial checks were on
November 1, with [additional physical charging checks on November 6](charging-test-2026-11-06.md).

| Data | Evidence | Limitation |
| --- | --- | --- |
| DP1 total energy | Own schema kWh/scale2; hourly increments during the overnight charge; final 36.73 kWh delta matched DP6 and completed-segment sum | Same-device comparison; reset behavior/long-term monotonicity not independently stress-tested |
| DP25 session energy | Own schema kWh/scale2; completed segments of 1.59, 0.06 and 35.08 kWh summed to the 36.73 kWh lifetime delta and final DP6 value | Reports the last completed charging segment in this test; differs from DP6 after a local restart; not an Energy source |
| DP24 temperature | Own schema explicitly Fahrenheit; LAN/HA reading | Internal charger temperature, not ambient or battery temperature |
| DP3 status | Full enum from own schema; unplugged, charging, local session-ended and overnight charging → paused transitions observed | Overnight stop cause not established; fault transitions were not induced |
| DP4 current limit/control | 16/32/40/48 A settings produced sustained measured draw; original 40 A restored | Short functional windows, not a long thermal test; 48 A requires suitable hardwiring |
| DP10 fault | Own schema bitmap; no-fault observed; synthetic multi-bit tests | No fault deliberately induced |
| DP13 plug/pilot | Own enum; unplugged and charging reports observed | Bad/unknown pilot produces Unknown, not Connected |
| DP18 request/control | Local stop/restart confirmed with positive power and no vehicle hook; automatic plug-in start observed for five minutes before test commands | Pending DP18 can be optimistic for 5 s; a request alone is not proof of power flow |
| DP14 operating mode | Scheduled → Plug and Charge readback confirmed; Manual Start waiting, local start/stop and return to Plug and Charge verified | Selector becomes unavailable while charging; fixed-energy mode is not offered |
| DP103 hardwired | Own boolean schema; device report observed | Does not verify wiring or permit changing installation current |
| DP6 power |12-byte raw packet, synthetic decoding tests and live power consistent with V/I | DP5/9 absent; DP6 can disappear during charging, including a longer gap in the November 6 capture; independent meter comparison outstanding |
| DP6 voltage/current |12-byte packet prefix compared with app during real charging; synthetic field-isolation tests | Limited to tested firmware/packet length |
| DP6 session energy | Final four bytes decoded as unsigned big-endian /100 kWh; real byte carry at 2.67 kWh; overnight zero-V/I/P packet retained 36.73 kWh, matching lifetime delta and completed-segment sum | Highest two bytes still zero; physical unplug/replug reset unverified; sparse reports prevent a full power integral |
| DP27 online state | Raw reported enum captured | Not used for availability; can say offline during a successful LAN read |

The charging-request switch, supported current selector and operating mode are writable.
All four supported current settings were exercised under load and 40 A was restored.
No protection setting changed. Continuous cloud-blocked operation, Wi-Fi outages
and power failures remain untested. Configured availability is based on actual
local connection health.

The public schema contains only selected manufacturer datapoint definitions.
Private keys, app files, account cache, device IDs/MACs, real energy histories,
network addresses and HA configuration are not part of this repository.

`sensor.lectron_v_box_pro_phase_session_energy` is separate from the DP25 session
sensor and the DP1 lifetime meter. It has no accumulating statistics class and
must not be used as an Energy dashboard source. A stopped packet can retain its
energy while reporting zero V/I/P. If DP6 disappears, this sensor becomes
unavailable rather than returning zero or falling back to DP25.

The sensor's `raw_phase_packet` attribute retains the complete Base64 DP6 value.
Recorder can preserve packet changes under its existing include/exclude and
retention settings, without another charger connection or polling loop. This is
state history, not a record of every identical packet received, and it does not
recover raw packets from charges before this sensor was installed.


The weekday policy/manual override was validated in live HA while unplugged.
Tests execute the real HA script engine for boundary crossings, stale policy,
manual takeover, hook cancellation and recovery. No physical peak-window test
was performed; HA/LAN downtime and raw charger autostart remain limitations.

The November 7 [DP6 refresh trial](telemetry-refresh.md) enables explicit requests
through the existing connection. It is prepared for next-cycle validation;
regular live telemetry has not yet been established with that option.
