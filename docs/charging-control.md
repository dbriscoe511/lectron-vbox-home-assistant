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
for coordinated requests. The dashboard's **Start charging now** uses
`script.lectron_charge_now`, an explicit session override of the weekday block.
The following automatic entry point respects that block:

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
no vehicle retry loop. The schedule reconciles allowed charging on startup and
permission opening; it does not restore an old delayed request. Stop cancels the pending start script first,
also cancels a running vehicle-start hook, then sends DP18off without requiring plug/fault states; it can also call a
vehicle-stop hook. No delayed DP18on is sent after the vehicle hook. A cloud
command already dispatched cannot be recalled; the charger stop remains separate.

## Charger mode

`select.lectron_v_box_pro_operating_mode` writes DP14:

| HA option | Charger value |
| --- | --- |
| Plug and charge | `charge_now` |
| Manual start | `charge_manual` |
| Scheduled charge | `charge_schedule` |

The control is available only for known stopped states, and rejects changes
while charging. Switching Scheduled charge back to Plug and charge was verified
with local charger feedback and no pending write. Manual Start waiting, local
start/stop and return to Plug and Charge were verified in the
[November 6 charging test](charging-test-2026-11-06.md). Native schedule entries
stay in the Lectron app; choosing a mode does not create or delete schedules or
disable the HA weekday policy.

The schema also lists `charge_energy`, but that mode is absent from the tested
app UI and DP17's kWh scaling is unverified. It is not offered by this selector.
See [the command audit](command-audit.md) for the remaining fields and test plan.

## Optional vehicle hooks

Copy [vehicle-hooks.example.yaml](../home-assistant/vehicle-hooks.example.yaml)
to a **separate private HA package** and adapt the vehicle binding. Its start
guards are mandatory for the schedule, including the explicit manual-request
field. Include the copied guarded file alongside the charger package:

```yaml
homeassistant:
  packages:
    lectron_vehicle: !include lectron_vehicle.yaml
```

Replace `YOUR_VEHICLE_DEVICE_ID` inside the copied file and adapt its vehicle
service actions. Keep its permission, connection and fault guards intact.


Hooks must send only vehicle commands; do not turn the charger on or add retry
loops. The package works without hooks but cannot wake a car that independently
refuses charging. Vehicle schedules, battery targets and limits still apply.

## Battery target percentage

The local Lectron interface provides charging requests, current selection and
charger telemetry. It does not provide vehicle state of charge or a battery
percentage cutoff. The car enforces its own AC charge target, including when
HA starts charging or overrides the weekday schedule.

The optional [vehicle target card](../home-assistant/vehicle-card.example.yaml)
puts your vehicle integration's AC target number, reported battery percentage
and vehicle report time on the charging dashboard. Replace all three example
entity IDs before adding it. The number control uses the vehicle integration's
supported range and step; it does not write a Lectron datapoint. Cloud commands
and cached reports can lag, so a successful service call alone does not confirm
the target reached the car. This card does not change the DC target or request
periodic vehicle wake-ups.

Disable conflicting native charging schedules while preserving the desired
AC target. For example, a car set to 100% will continue past 80% even when HA is
responsible for start/stop times. Optional trip workflows may temporarily raise
the target and restore the prior value; the normal Charge now button does not.

## Physical evidence

The [November 6 charging test](charging-test-2026-11-06.md) confirmed measured
draw at 16/32/40/48 A, local stop/restart without vehicle hooks, Manual Start
waiting for a request, and restoration to 40 A/Plug and Charge. The automatic
plug-in start worked without a manual vehicle query or wake; five full minutes
were observed before test commands.

Session energy retained its value through a local pause/restart. Larger values,
natural completion and a physical unplug/replug reset remain passive checks.
Future tests should still allow five full minutes before manual vehicle queries,
refreshes or wake commands. Existing background integrations are separate from
manual test calls. Preserve the user's current battery target.

See [the weekday policy](scheduling.md) for manual-session clearing, exact boundaries,
restart behavior and the stable automatic-permission helper. In package YAML,
boolean selectors use `boolean: null` so the HA package merger preserves the type.
