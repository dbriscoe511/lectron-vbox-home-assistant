# Verification and known limits

Verified against one Lectron V-BOX Pro NACS Wi-Fi, hardware V1.2/software V2.0.1,
Tuya 3.5, HA 2026.10.4 and Tuya Local 2026.10.0 on 2026-11-01.

| Data | Evidence | Limitation |
| --- | --- | --- |
| DP1 total energy | Own schema kWh/scale2; authenticated LAN and HA reading | Reset behavior/long-term monotonicity not independently stress-tested |
| DP25 session energy | Own schema kWh/scale2; authenticated LAN and HA reading | Retains last session while idle; not an Energy source |
| DP24 temperature | Own schema explicitly Fahrenheit; LAN/HA reading | Internal charger temperature, not ambient or battery temperature |
| DP3 status | Full enum from own schema; idle state observed | Other physical charge/fault transitions remain to be observed |
| DP4 current limit | Own schema A/scale0; existing setting read back | Read-only; schema max255 is not a hardware/install limit |
| DP10 fault | Own schema bitmap; no-fault observed; synthetic multi-bit tests | No fault deliberately induced |
| DP13 plug/pilot | Own enum; unplugged idle observed | Bad/unknown pilot produces Unknown, not Connected |
| DP18 request/control | Own writable boolean schema; idle readback and local request switch loaded | Pending feedback can be optimistic for5s; physical start/stop still needs a connected-vehicle test |
| DP103 hardwired | Own boolean schema; device report observed | Does not verify wiring or permit changing installation current |
| DP5/9 power | Own schema kW/scale3 | Absent in idle reply; charging measurement not yet verified |
| DP6 voltage/current | Raw phase_a schema; related Tuya layout and synthetic decoder tests | Exact byte layout unverified during real charging; disabled by default |
| DP27 online state | Raw reported enum captured | Not used for availability; can say offline during a successful LAN read |

Only the charging-request switch is writable; other entities are telemetry.
No current/protection setting was changed. Continuous cloud-blocked operation,
Wi-Fi outages, power failures and real charging transitions still need field
testing. Configured availability is based on actual local connection health.

The public schema contains only selected manufacturer datapoint definitions.
Private keys, app files, account cache, device IDs/MACs, real energy histories,
network addresses and HA configuration are not part of this repository.

