# Upstream new-device issue draft

Not submitted. This is a draft for Tuya Local's
[New Device form](https://github.com/make-all/tuya-local/issues/new?template=new-device.yaml),
laid out field by field. New-device PRs are paused upstream, and the form says
only two kinds of request are being worked on:

1. well-written pull requests (paused);
2. well-written issues with the **LOCAL DPS warning log** and **QueryThingsDataModel
   output in original format**.

A tested config by itself is the lowest priority. So this issue leads with the log
and DPS data and offers the profile as a ready-made PR.

Profile: [`dbriscoe511/tuya-local`, branch `lectron-vbox-pro`](https://github.com/dbriscoe511/tuya-local/tree/lectron-vbox-pro),
one commit adding `custom_components/tuya_local/devices/lectron_vboxpro_evcharger.yaml`
on top of upstream main `bdd47ec`. Pinned tag: `lectron-vbox-pro-2026.11.11`.

---

## Title

Request support for Lectron V-BOX Pro NACS Wi-Fi EV charger

## Log message (required)

Captured November 11, 2026 from unmodified upstream Tuya Local 2026.10.0 (the
latest release, without this profile) in a temporary HA 2026.11.0, by adding the
charger manually and cancelling at the device-type step. The charger was
plugged in and paused. Paste verbatim except DP22, which is the charger's MAC
address; say it was redacted.

```text
2026-11-11 09:55:40.778-07:00 WARNING (MainThread) [custom_components.tuya_local.config_flow] Device matches afyeev_16a_evcharger with quality of 80%. LOCAL DPS: {"updated_at": 1794416139.5188913, "1": 235936, "3": "charger_pause", "4": 40, "10": 0, "13": "controlpi_9v_pwm", "14": "charge_now", "15": 0, "17": 10, "18": true, "22": "<MAC redacted>", "23": "HW V1.2,SW V2.0.1", "24": 68, "25": 2436, "27": "offline", "103": true}
2026-11-11 09:55:40.778-07:00 WARNING (MainThread) [custom_components.tuya_local.config_flow] Include the previous log messages with any new device request to https://github.com/make-all/tuya-local/issues/
```

DP6 (phase report) is absent because the charger only sends it while charging;
mention that under DPS information. The best existing match, at 80%, is
`afyeev_16a_evcharger`.

## Product ID

```
xoiejlwg1pq0ehpk
```

This is the shared product key reported by the charger, not a device ID.

## Product Name

Lectron V-BOX Pro NACS Wi-Fi (HW V1.2, SW V2.0.1, Tuya protocol 3.5)

## DPS information (required)

The form's preferred source, QueryThingsDataModel from iot.tuya.com, isn't
available: the charger is paired to Lectron's own app, not Smart Life/Tuya
Smart, so it can't be linked to a Tuya IoT project. Say so plainly, then attach
the closest original-format source:

- **Attach:** the Tuya SDK schema map read from the signed-in Lectron Android app
  (`getSchemaMap`), unmodified: all 25 DPs with id, code, mode, type and
  `property` ranges/enum lists. Public copy:
  [`manufacturer-schema.json`](manufacturer-schema.json). Label it as the app
  SDK's schema map, **not** a QueryThingsDataModel response. The SDK's raw
  `getSchema` string can be pasted instead if preferred; it's the same
  definitions in the SDK's original string form.
- **Mention:** DP6 is a 12-byte raw phase report (voltage /10 V, current /1000 A,
  power /1000 kW, session energy /100 kWh, all big-endian), which differs from
  the existing Vevor layouts. Decoding was confirmed against DP1/DP25 on real
  charges. Names in the schema are Chinese; codes are the useful part.

## Information about how the device functions

Draft text (keep it short):

> Turns out these are Tuya chargers. Lectron V-BOX Pro NACS Wi-Fi, a 48 A
> Level 2 charger, local protocol 3.5. I have a working, tested config and can
> open a PR as soon as PRs reopen:
> https://github.com/dbriscoe511/tuya-local/tree/lectron-vbox-pro (one new device
> YAML on current main).
>
> It covers start/stop (DP18), current 16/32/40/48 A (DP4), operating mode
> (DP14, disabled while charging), status, faults, energy, temperature (°F),
> plug state and live voltage/current/power from the DP6 phase report.
>
> Tested on real charges since November 6: all four current settings under load, local
> stop/restart, Manual Start and plug-in charging. On the latest charge, DP6
> session energy, DP25 and the lifetime meter all matched at 24.36 kWh. DP6
> reports arrive about every 120 s; the profile uses default retention, and
> voltage/current/power go unavailable when charging stops. The closest
> existing profile in the log is afyeev_16a_evcharger at 80%.
>
> Config written with AI assistance. I understand it and will make requested
> changes. Test write-ups:
> https://github.com/dbriscoe511/lectron-vbox-home-assistant

## Evidence to attach or link

| Evidence | Where it goes | Status |
| --- | --- | --- |
| LOCAL DPS warning lines from Tuya Local | Log message | Ready, captured November 11 (MAC redacted) |
| Product ID `xoiejlwg1pq0ehpk` | Product ID | Ready |
| Lectron app SDK schema map, unmodified | DPS information (attached file) | Ready, [public copy](manufacturer-schema.json) |
| Fork branch with the profile | Information | Ready, pushed |
| Charging tests: [Nov 6](charging-test-2026-11-06.md), [Nov 7](charging-test-2026-11-07.md), [Nov 10](charging-test-2026-11-10.md) | Information (link) | Ready |
| Upstream checks on the fork: 33 device-config tests, full suite 431 passed, Ruff, yamllint, `untranslated_entities`, `duplicates` (no 100% match) | Information, one line | Ready, run November 11 |
| Profile tests against the fork's parser: 118 passed | Information, one line | Ready |

Don't attach HA diagnostics, the TinyTuya status dump or anything with the
device ID, local key, MAC or IP. If the maintainer asks for diagnostics, run
`tools/sanitize_diagnostics.py` first.

## Before submitting

- Recheck the live form; the priority note or required fields may have changed.
- Rebase the fork branch if upstream has moved, rerun the checks above and
  update the tag/installer pin together.
- Paste the captured log above as is, apart from the redacted MAC.
- Opening the issue posts publicly under Dan's account; Dan opens it.
