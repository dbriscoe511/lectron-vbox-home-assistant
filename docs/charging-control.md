# Charging controls and vehicle coordination

`switch.lectron_v_box_pro_charging_request` writes **only DP18**. Standard HA
`switch.turn_on`/`switch.turn_off` actions address the charger directly.
Tuya Local can overlay pending writes for about five seconds; DP18 feedback is
not proof of energy flow. Check DP3 Charging and reported power/current.

`select.lectron_v_box_pro_charging_current` writes **only DP4**, offering the
manufacturer's settings **16 A, 32 A, 40 A, 48 A**. The48A setting requires a
suitable hardwired installation; the NEMA-plug default is40A. Choose within your
installation's limit. The schema's255A maximum is not a supported product limit.
The existing Current limit sensor remains read-only.

```yaml
actions:
  - action: select.select_option
    target:
      entity_id: select.lectron_v_box_pro_charging_current
    data:
      option: "32 A"
```

Changing current can pause charging. Use the package scripts/dashboard buttons
for coordinated requests:

```yaml
actions:
  - action: script.turn_on
    target:
      entity_id: script.lectron_start_charging
```

```yaml
actions:
  - action: script.turn_on
    target:
      entity_id: script.lectron_stop_charging
```

Start requires a known vehicle connection, no fault and an available switch.
An already charging device with positive power exits without another request.
Otherwise it sends DP18 once and allows a **five-minute charger-only observation
window** before any optional vehicle wake request. Positive reported power and
DP3 charging confirm reported operation. If charging is reported but power is
unavailable, a notification describes that uncertainty without waking the car.

After five minutes, if plug/fault guards remain satisfied, an optional vehicle
hook can run **once**. It waits up to another minute and checks after a short
settling interval. Unconfirmed requests create a local HA notification. There is
no retry loop or startup resume. Stop cancels the pending start script first,
also cancels a running vehicle-start hook, then sends DP18off without requiring plug/fault states; it can also call a
vehicle-stop hook. No delayed DP18on is sent after the vehicle hook. A cloud
command already dispatched cannot be recalled; the charger stop remains separate.

## Optional vehicle hooks

Keep these in a **separate private HA package**, adapted to your integration:

```yaml
script:
  lectron_vehicle_start_charging:
    sequence:
      - action: kia_uvo.start_charge
        data:
          device_id: YOUR_VEHICLE_DEVICE_ID
  lectron_vehicle_stop_charging:
    sequence:
      - action: kia_uvo.stop_charge
        data:
          device_id: YOUR_VEHICLE_DEVICE_ID
```

Hooks must send only vehicle commands; do not turn the charger on or add retry
loops. The package works without hooks but cannot wake a car that independently
refuses charging. Vehicle schedules, battery targets and limits still apply.

## Physical evidence and next test

The installed test confirmed an actual stop and accepted a32A setting. The
vehicle briefly reported charging, then paused. Restoring40A and sending a
Hyundai start request resumed reported charging with positive measured current
and power. Sustained32A draw was not verified;48A was not tested. Persistence
across unplug/replug remains unverified.

Next time, observe the local charger for **five full minutes** after its start
request before any manual vehicle query, refresh or command. Record DP3/pilot,
DP18 and measured current/power. This tests whether the car resumes on its own;
the earlier short test does not prove a vehicle wake is always necessary.
Existing background integrations are separate from manual test calls. Preserve
other schedules and protection settings.
