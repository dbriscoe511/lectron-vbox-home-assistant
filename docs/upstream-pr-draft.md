# Upstream PR draft

Not submitted. Tuya Local currently has new-device PR submissions paused.
The [November 6 charging test](charging-test-2026-11-06.md) covers the controls.
The completed overnight capture and remaining gaps are listed in the
[command audit](command-audit.md).

Prepared checkout: `/home/danb/Desktop/code/tuya-local-lectron-upstream`, branch
`lectron-vbox-pro`, commit `71a19c0`. The branch is rebased on upstream main `ec004a5`. The patch contains only the new device YAML. Its header and the description
link to the custom dashboard; the generated device catalog is left to upstream.

## Title

Add Lectron V-BOX Pro NACS Wi-Fi EV charger

## Description

Turns out these are Tuya chargers. This adds the Lectron V-BOX Pro NACS Wi-Fi,
tested on HW V1.2 / SW V2.0.1 over local protocol 3.5.

Includes start/stop, 16/32/40/48 A current settings, operating mode, energy,
voltage/current/power, Fahrenheit temperature, plug state and faults. Mode
changes are disabled while charging. The 12-byte phase packet differs from
the existing Vevor profiles.

Tested actual draw at all four settings, local stop/restart without vehicle
hooks, Manual Start and automatic plug-in charging. Phase session energy
matched the completed-segment sum and lifetime increase at 36.73 kWh, and all
three energy readings matched at 15.18 kWh on the next charge. Phase energy
survives local pauses and resets at physical unplug.

Phase reports settled around two minutes apart. The profile uses normal
retention between reports and charging-status guards for power/current/voltage.
Cache behavior is tested against the actual transport; another physical charge
with the final retention setting is still pending. Unconfirmed fixed-energy,
protection, reset and schedule-payload writes aren't exposed.

There's an optional [custom dashboard](https://github.com/dbriscoe511/lectron-vbox-home-assistant#4-add-energy-helpers-and-the-dashboard).
[Charging evidence](https://github.com/dbriscoe511/lectron-vbox-home-assistant/blob/main/docs/verification.md)
is documented separately. AI-assisted device config; no runtime changes.

## Validation to attach

- Shared product ID: `xoiejlwg1pq0ehpk`.
- [Original SDK field definitions](manufacturer-schema.json), as an alternative
  data-model source. This is not a QueryThingsDataModel API response.
- Local HA diagnostics/status evidence, with identifiers and keys removed.
  The original discovery warning is no longer in the rotated HA logs; label
  this evidence accurately rather than fabricating a LOCAL DPS warning.
- Pinned-overlay tests: 114 passed, including exact DP14 writes and rejecting
  mode changes during charging.
- Current-upstream config tests: 33 passed.
- `uv run untranslated_entities` passed.
- `uv run duplicates lectron_vboxpro_evcharger`: no 100% duplicate. Closest
  synthetic matches were the Vevor portable profiles at 81%; original local
  reports match the new profile, while the Vevor L2 layout does not match.
- Ruff checks, import-order check, format check and device YAML lint passed.
  YAML lint reports one existing warning in an unrelated Marpou profile.

Follow the [PR template](https://github.com/make-all/tuya-local/blob/main/.github/pull_request_template.md),
[agent instructions](https://github.com/make-all/tuya-local/blob/main/AGENTS.md)
and [new-device evidence requirements](https://github.com/make-all/tuya-local/blob/main/.github/ISSUE_TEMPLATE/new-device.yaml).
The PR template requires one device per branch, no changes to `DEVICES.md` or
`ACKNOWLEDGEMENTS.md`, and a short description. AI-assisted contributors must
understand the changes and handle requested fixes. A separate bug report is
required for runtime code changes; this patch adds only device YAML.

Pre-submission review, November 8: the live new-device form still says PRs are
temporarily paused. The original LOCAL DPS discovery warning is still missing;
the saved SDK schema is an alternative data-model source, not the preferred
original QueryThingsDataModel response. A normal charge with final retention
is recommended; do not repeat the full current/mode tests just for that check.
Update the pending passive checks as reports arrive; do not mark them tested
without a matching local report or physical observation.
