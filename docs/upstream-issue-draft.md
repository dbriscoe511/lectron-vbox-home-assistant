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

**Still to capture. Do not submit without it.** The form says reports without
the integration's own local log are closed immediately.

What to paste: the two Warning lines Tuya Local writes at the device-type step,
`Device matches <type> with quality of N%. LOCAL DPS: {...}` and the line after
it, copied verbatim from Settings → System → Logs.

How it will be captured: Tuya Local aborts a second add flow for a device that's
already configured before it reaches that step, so the live HA can't produce the
line without removing the charger. The plan is a temporary, separate HA
instance running unmodified upstream Tuya Local (without this profile), with the
charger added manually there and the flow cancelled at the type step. The live
charger entry is disabled during the capture, since the charger may accept only one
local client, then re-enabled. Do it while the car isn't charging. This needs
Dan's go-ahead first; it hasn't been done. The log contains no local key; check
it for the device ID before pasting.

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
> voltage/current/power go unavailable when charging stops. Closest existing
> profiles are the Vevor chargers at 81%.
>
> Config written with AI assistance. I understand it and will make requested
> changes. Test write-ups:
> https://github.com/dbriscoe511/lectron-vbox-home-assistant

## Evidence to attach or link

| Evidence | Where it goes | Status |
| --- | --- | --- |
| LOCAL DPS warning lines from Tuya Local | Log message | **To capture** (see above) |
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
- Paste the real log; never write or reconstruct one.
- Opening the issue posts publicly under Dan's account; Dan opens it.
