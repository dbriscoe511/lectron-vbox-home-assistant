# Weekday charging policy and manual Charge now

The supplied HA package uses **America/Denver**:

| Local time | Automatic charging |
| --- | --- |
| Monday-Friday,17:00 inclusive to21:00 exclusive | Blocked |
| Other weekday hours and all weekend hours | Allowed |

Set HA's timezone accordingly, or deliberately adapt the policy templates for
another installation. A timezone mismatch or unknown policy state denies
automatic starts. The policy does not change charging current or the vehicle's
AC/DC target percentage.

## Entry points

- **Dashboard Start charging now / `script.lectron_charge_now`:** an explicit
  manual override for the current session, including the blocked window.
- **Automations / `script.lectron_start_charging`:** schedule-respecting start.
  Omit `manual_request`; it defaults false. This is the Ski/workflow entry point.
- **`script.lectron_stop_charging`:** cancel pending starts/hooks, clear a manual
  override, and stop. Use this instead of directly toggling the low-level switch
  when coordinating with a vehicle hook.
- **`binary_sensor.lectron_charging_allowed`:** automatic permission only. It
  stays Off during peak hours even while a manually requested charge is running.
- **`binary_sensor.lectron_manual_override_active`:** reports the separate manual
  session exception.

A manual request sets the override first, cancels any old enforcement/start/hook,
then creates a fresh coordinator request. It retains the **five-minute local-only
observation window** before an optional vehicle-start fallback. An automatic
caller cannot borrow the override merely because the flag is On. Both the
explicit request flag and active manual-session flag are needed to bypass time.

The manual exception clears on Stop, unplugging, a completed/idle session held
for30seconds, a failed manual attempt, or HA restart/helper reload. Completion
cleanup waits until both start scripts are idle, avoiding cancellation of a new
manual attempt replacing an older ended session. Already dispatched cloud
commands cannot be recalled.

## Boundaries and recovery

Starts check both the helper and the **current clock** immediately before DP18
and vehicle actions. A permission calculated five minutes earlier is not reused.
The private vehicle hook must repeat the same guard; use the guarded
[hook example](../home-assistant/vehicle-hooks.example.yaml).

Local enforcement runs at17:00, startup, plug/request/charging-on events and
blocked-only periodic checks. It cancels pending starts and requests a local
stop, without repeatedly calling the vehicle cloud. Stop feedback is checked;
unconfirmed enforcement produces a local HA notification.

Automatic reconciliation runs at weekday21:00, startup, policy opening, plug-in
and full telemetry recovery. It does **not** periodically restart an already
stopped/completed session. Duplicate events during one coordinator run coalesce.
After restart, a new allowed request starts a fresh five-minute observation;
old delayed requests and manual overrides are not restored.

## Workflow integration, including Ski

Check `binary_sensor.lectron_charging_allowed == on` before setting trip-specific
AC targets and before requesting an automatic start. Recheck the clock if a long
workflow wait can span17:00. Call `script.lectron_start_charging` without a manual
flag; never set the manual helper or call the manual wrapper from an automatic
workflow. A policy-opening event can resume a trip waiting for21:00.

Save/restore a prior AC target separately, preserve a later manual change, and
leave DC targets untouched. This generic repository does not bundle a personal
Ski workflow, vehicle identifiers, or vehicle-account credentials.

## Native schedules and limitations

Disable a conflicting vehicle charging schedule in its native app so it does
not independently delay an HA-authorized charge. Preserve unrelated departure,
climate and target settings. The tested US Hyundai library did not implement
schedule writes, so no unsupported endpoint was guessed. A stored off-peak
window can remain in cached vehicle data when the master reservation flag is
off; do not infer activation from that stored preference alone.

This is **HA-dependent software enforcement**, not a hardware cutoff. HA/LAN
outages prevent it from stopping the charger. Charger-native plug-and-charge
and administrative raw-switch calls can only be stopped reactively, with some
latency. Normal dashboard controls use guarded scripts; the raw DP18 switch is
not a policy-aware entry point. No OCPP capability, firmware mode or protection
setting is changed by this policy.
