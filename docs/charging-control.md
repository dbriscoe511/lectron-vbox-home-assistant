# Charging requests and automations

`switch.lectron_v_box_pro_charging_request` sends **only DP18** (`true`/`false`).
Use normal `switch.turn_on` / `switch.turn_off` actions in HA automations.
The package also provides `script.lectron_start_charging` (requires a known
vehicle connection and no reported fault) and `script.lectron_stop_charging`
(does not require a known plug/fault state).

```yaml
actions:
  - action: script.lectron_start_charging
```

```yaml
actions:
  - action: script.lectron_stop_charging
```

Choose the schedule/trigger in HA's automation editor. No charging schedule,
startup resume, or automatic retries are installed by this repository. Existing
charger/vehicle schedules and limits still apply; avoid competing schedules.

Tuya Local can temporarily overlay pending writes for about five seconds. The
request switch and diagnostic DP18 binary sensor can therefore show a requested
value before the charger echoes it. Use **DP3 Charging**, power and increasing
energy to assess actual charging. An accepted service call is not proof of a
physical start or stop. A car may decline a start because it is full, sleeping,
scheduled, or otherwise not ready.

The manufacturer marks DP18 writable, and the LAN protocol supports it. Whether
it controls only the current session or also blocks charging after unplug/replug
must be checked with a connected vehicle. The initial installation was verified
while unplugged; a physical charging-cycle test is still needed. Current-limit,
charging-mode, protection, energy-reset and schedule DPs are not writable here.
