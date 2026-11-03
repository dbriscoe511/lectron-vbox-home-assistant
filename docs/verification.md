# Verification and known limits

Verified against one Lectron V-BOX Pro NACS Wi-Fi, hardware V1.2/software V2.0.1,
Tuya 3.5, HA 2026.10.4 and Tuya Local 2026.10.0 on 2026-11-01.

| Data | Evidence | Limitation |
| --- | --- | --- |
| DP1 total energy | Own schema kWh/scale2; authenticated LAN and HA reading | Reset behavior/long-term monotonicity not independently stress-tested |
| DP25 session energy | Own schema kWh/scale2; authenticated LAN and HA reading | Retains last session while idle; not an Energy source |
| DP24 temperature | Own schema explicitly Fahrenheit; LAN/HA reading | Internal charger temperature, not ambient or battery temperature |
| DP3 status | Full enum from own schema; idle state observed | Other physical charge/fault transitions remain to be observed |
| DP4 current limit/control | Manufacturer settings16/32/40/48A;32A setting accepted and40A restored | Sustained32A draw and48A operation not tested;48A requires suitable hardwiring |
| DP10 fault | Own schema bitmap; no-fault observed; synthetic multi-bit tests | No fault deliberately induced |
| DP13 plug/pilot | Own enum; unplugged idle observed | Bad/unknown pilot produces Unknown, not Connected |
| DP18 request/control | Actual DP3/pilot stop observed; restart with positive power after vehicle start request | Pending DP18 can be optimistic for5s; five-minute self-resume test remains outstanding |
| DP103 hardwired | Own boolean schema; device report observed | Does not verify wiring or permit changing installation current |
| DP6 power |12-byte raw packet, synthetic decoding tests and live power consistent with V/I | Independent power-meter/app power comparison outstanding;DP5/9 were absent |
| DP6 voltage/current |12-byte packet prefix compared with app during real charging; synthetic field-isolation tests | Limited to tested firmware/packet length |
| DP6 session energy | Final four bytes interpreted as unsigned big-endian /100 kWh; short-charge stop matched DP25 and lifetime-meter increase | Four saved packets, two distinct values; reset timing and upper bytes still need a larger-session capture |
| DP27 online state | Raw reported enum captured | Not used for availability; can say offline during a successful LAN read |

Only the charging-request switch and supported current selector are writable.
Current was briefly set to32A, then restored to40A; no protection setting changed. Continuous cloud-blocked operation,
Wi-Fi outages, power failures and real charging transitions still need field
testing. Configured availability is based on actual local connection health.

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
