# Upstream PR draft

Not submitted. Tuya Local currently has new-device PR submissions paused.
The [November 6 charging test](charging-test-2026-11-06.md) covers the controls.
Remaining passive observations are listed in the [command audit](command-audit.md).

Prepared checkout: `/home/danb/Desktop/code/tuya-local-lectron-upstream`, branch
`lectron-vbox-pro`, commit `2d713c5`. The patch contains the new device YAML and
its supported-device entry, including the dashboard link.

## Title

Add Lectron V-BOX Pro NACS Wi-Fi EV charger

## Description

Turns out these are Tuya chargers. This adds a profile for the Lectron V-BOX Pro
NACS Wi-Fi, tested on HW V1.2 / SW V2.0.1 over local protocol 3.5.

Includes start/stop, the 16/32/40/48 A current settings, operating mode, energy,
voltage/current/power, temperature, plug state and faults. Mode changes are
disabled while charging. The device uses a 12-byte phase packet and reports
temperature in Fahrenheit, so the existing Vevor profiles don't fit.

Tested actual draw at all four current settings, local stop/restart without
vehicle hooks, Manual Start waiting for a request, and return to Plug and Charge.
Automatic plug-in charging worked, with five minutes observed before test
commands. At a stop, phase session energy matched DP25 and the lifetime-meter
increase; a local restart retained the counter. Values above 2.55 kWh and a
physical unplug/replug reset are still being captured. Details and timings are
in the [charging test](charging-test-2026-11-06.md). The same capture exposed a
longer DP6 reporting gap while charging; that remains an open telemetry issue.

The schema includes a kWh-charge mode that doesn't show up in my Lectron app.
Its command units aren't confirmed, so it isn't exposed. Alarm/protection blobs,
counter resets and undocumented schedule payloads are also left alone.

There's an optional [custom dashboard](https://github.com/dbriscoe511/lectron-vbox-home-assistant#4-add-energy-helpers-and-the-dashboard)
with charging controls and energy charts. The profile doesn't need it.

AI-assisted config, checked against the device's own schema and local reports.
No transport/runtime changes.

## Validation to attach

- Shared product ID: `xoiejlwg1pq0ehpk`.
- [Original SDK field definitions](manufacturer-schema.json), as an alternative
  data-model source. This is not a QueryThingsDataModel API response.
- Local HA diagnostics/status evidence, with identifiers and keys removed.
  The original discovery warning is no longer in the rotated HA logs; label
  this evidence accurately rather than fabricating a LOCAL DPS warning.
- Pinned-overlay tests: 107 passed, including exact DP14 writes and rejecting
  mode changes during charging.
- Current-upstream config tests: 33 passed.
- `uv run untranslated_entities` passed.
- `uv run duplicates lectron_vboxpro_evcharger`: no 100% duplicate. Closest
  synthetic matches were the Vevor portable profiles at 81%; original local
  reports match the new profile, while the Vevor L2 layout does not match.
- Ruff checks, import-order check, format check and device YAML lint passed.
  YAML lint reports one existing warning in an unrelated Marpou profile.

There is no separate PR template in the upstream repository. Follow its
[agent instructions](https://github.com/make-all/tuya-local/blob/main/AGENTS.md)
and [new-device evidence requirements](https://github.com/make-all/tuya-local/blob/main/.github/ISSUE_TEMPLATE/new-device.yaml).
Update the pending passive checks as reports arrive; do not mark them tested
without a matching local report or physical observation.
