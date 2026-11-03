# Lectron V-BOX Pro in Home Assistant

Local monitoring for the **Lectron V-BOX Pro NACS Wi-Fi** EV charger using an
exact device profile for [Tuya Local](https://github.com/make-all/tuya-local).
Includes a charging dashboard, energy helpers, optional flat-rate cost estimates,
and tools for preparing historical energy statistics.

**Unofficial. This repository is vibe coded: written with AI assistance (Codex),
with an Astra architecture/code review and automated tests. It is not a Lectron
product or an upstream Tuya Local release.** Tests and one installed charger do
not establish compatibility with every product revision.

## What works

- Local charging start/stop requests usable in HA automations.
- Local charger status, plug/charging indicators and fault reporting.
- Cumulative energy, reported session/checkpoint energy, internal temperature,
  live voltage/current/power and the configured current limit.
- Current selector:16/32/40/48A (48A requires suitable hardwiring).
- Charging mode, firmware, pilot state, charge request and hardwired detection.
- Home Assistant Energy-compatible cumulative energy statistics.
- Daily/monthly live energy meters and a native dashboard with no custom cards.
- Weekday17:00–21:00 automatic block (America/Denver), with a manual session override.
- Optional power readings when the charger actually reports them.

This release writes only **charging request DP18** and the manufacturer-supported
**current settings DP4**. The generic schema's255A maximum is not a hardware or
installation limit. Charging mode, protection, schedule and energy reset DPs
remain unwritable. See [charging controls](docs/charging-control.md) for bounded
start/stop scripts, optional vehicle hooks and the five-minute observation window.

This firmware sends a **12-byte phase packet**:2-byte voltage,3-byte current,
3-byte power, then4 unidentified bytes. Voltage/current were compared with the
Lectron app during an actual charge. Power uses the same packet and is consistent
with voltage/current; an independent power-meter comparison remains outstanding.
The trailing bytes are not exposed as energy or time without a verified meaning.
Voltage/current/power require a present packet and reported charging state;
missing data is not converted to zero or carried indefinitely from another session.

DP25 can retain the last completed session or checkpoint during a new charge;
it is not a continuously updated session counter. `Session ended` does not mean
`Battery full`. Vehicle battery percentage/range/ETA come from a separate vehicle
integration. See [OCPP and reusable framework findings](docs/ocpp.md) and
[charging schedule/manual override behavior](docs/scheduling.md).

## Tested setup

| Item | Tested version |
| --- | --- |
| Charger | Lectron V-BOX Pro NACS **Wi-Fi** |
| Hardware / firmware | V1.2 / V2.0.1 |
| Manufacturer product ID | `xoiejlwg1pq0ehpk` (shared product identifier) |
| Local protocol | Tuya 3.5 |
| Home Assistant | 2026.10.4 Container |
| Tuya Local | 2026.10.0 |

The unit's own manufacturer schema confirms energy scale 2 (raw /100 kWh),
power scale 3 (raw /1000 kW), and internal temperature in **Fahrenheit**, not
Celsius. See [the datapoint specification](docs/datapoints.json) and
[verification notes](docs/verification.md). Other EVSE profiles are useful
references, but do not select an approximate one: their fault bits, units and
writable controls can differ.

## Setup

### 1. Get the local connection information

You need the charger's **LAN address**, **Tuya device/Virtual ID**, **local key**,
and protocol version. The IP shown in Lectron's app may be the home's public WAN
address. Match local discovery to the MAC in Device Information.

[TinyTuya](https://github.com/jasonacox/tinytuya#network-scanner) can discover
devices with `python -m tinytuya scan`. Discovery does not reveal the local key.
The key is private and changes if you re-pair the charger. Keep it out of Git,
screenshots, issues and command-line arguments.

Smart Life/Tuya Smart users can use their supported key-retrieval flows. A
Lectron-only account is a separate case: the tested Lectron app did not expose a
User Code. This installation recovered the key from the owner's logged-in Android
app SDK in a backed-up emulator. That is an advanced, version-dependent process;
this repo does not bundle Android APKs, login sessions or a promise that Lectron
works with Smart Life QR authorization. Do not reset a working charger merely to
try a key-retrieval guide.

### 2. Install the profile and transport

First back up your Home Assistant configuration. This is a **profile overlay
repository**, not a separately installable HACS integration.

**Existing Tuya Local installation:** copy `devices/lectron_vbox_pro.yaml` into
`<HA config>/custom_components/tuya_local/devices/`, then restart Home Assistant.
You can install Tuya Local normally through HACS before doing this.

**New manual installation:** the optional installer downloads the pinned official
Tuya Local release, checks its SHA-256, installs it without modifying upstream
runtime code, and adds this profile. Run it on the machine that can write your
HA configuration directory (Python 3.12+ and PyYAML required):

```bash
git clone https://github.com/dbriscoe511/lectron-vbox-home-assistant.git
cd lectron-vbox-home-assistant
python3 -m venv .venv
.venv/bin/pip install 'PyYAML>=6,<7'
.venv/bin/python tools/install_profile.py --config-dir /path/to/ha/config --bootstrap
```

The installer never replaces an existing Tuya Local installation. It prints the
installed version, stages a fresh transport atomically and backs up a differing
existing Lectron profile. If you already have Tuya Local, omit `--bootstrap`.
Do not install a second local Tuya integration against this same charger.

### 3. Add the charger

1. Restart HA after installing the files.
2. **Settings → Devices & services → Add integration → Tuya Local**.
3. Choose manual/local setup; enter the LAN host, Virtual ID, local key and `3.5`.
4. Keep persistent connection mode (`poll_only: false`) unless troubleshooting.
5. Select **Lectron V-BOX Pro NACS Wi-Fi (`lectron_vbox_pro`)**.
6. Name it **Lectron V-BOX Pro** to use the example entity IDs unchanged, and
   assign it to your Garage area.

Close Lectron's app while diagnosing local connection contention. Some Tuya
devices accept only one local client. This profile needs no cloud credentials or
emulator after setup. Operation with Internet access blocked has not been tested.

### 4. Add energy helpers and the dashboard

Copy `home-assistant/lectron_charging.yaml` into your HA config directory. Merge
this entry into your existing configuration; do not replace other packages:

```yaml
homeassistant:
  packages:
    lectron_charging: !include lectron_charging.yaml
```

Check configuration and restart, or reload supported integrations if already
loaded. The package adds the documented weekday schedule and manual Charge now override,
guarded start/stop scripts with optional vehicle coordination,
live daily/monthly meters, all-active-bit fault details
and an optional flat electricity rate. Leave the rate at zero to keep the cost
estimate unavailable. Costs exclude time-of-use pricing, taxes and fees.

Create a new dashboard using `home-assistant/dashboard.yaml` in its raw editor.
It uses native HA cards. Adapt the entity IDs if you chose a different device
name. Daily/monthly helper values initially cover only live collection; an
imported statistics chart and a utility-meter state are different things.

To control the car's AC battery target from this dashboard, add
[`home-assistant/vehicle-card.example.yaml`](home-assistant/vehicle-card.example.yaml)
as a card and replace its three placeholder entity IDs with those from your
vehicle integration. The charger itself does not report battery percentage.
Turning off a vehicle schedule does not set its AC target; retain your desired
normal target (for example 80%). See [battery target behavior](docs/charging-control.md#battery-target-percentage).

For Home Assistant's **Energy → Individual devices**, select
`sensor.lectron_v_box_pro_total_energy`. It has energy/kWh/total_increasing
semantics. Do not select session energy: it resets or retains a previous session.
HA needs a statistics cycle before a new energy sensor becomes selectable.

## Historical energy

See [history/backfill instructions](docs/history.md). Backfill must preserve
source granularity, units, timezone, gaps and a nonoverlapping cutoff. Imported
statistics are not a fabricated raw power trace. This project does not require
SQL edits or a permanently running cloud-history integration.

The dashboard's **Start charging now** bypasses the time block for one manual
session. Automations and Ski workflows use `script.lectron_start_charging`
without a manual flag and check `binary_sensor.lectron_charging_allowed`.
See [policy and recovery details](docs/scheduling.md).

## Updates and removal

If upgrading from the initial profile, enable Voltage and Current in their HA
entity settings if they remain disabled. Existing entity names/identities are
preserved; the power sensor now uses the tested DP6 packet instead of absent DP9.
The new current selector may require adapting its entity ID if HA includes an
area name. Configure optional vehicle hooks separately as documented.

Tuya Local updates can overwrite or remove this custom profile. After each
transport update, reapply it, validate and reload/restart. Until upstream accepts
the profile, this manual step remains necessary. Do not assume this repo is part
of upstream. Keep entity names stable: Tuya Local derives entity identities from
the profile's names, and changing them can split history.

To remove, delete the device entry in HA first. Remove the package include and
its optional helpers/dashboard, then remove this profile. Remove Tuya Local's
runtime only if no other configured device uses it. Existing Recorder history is
not deleted by removing the integration. Restore your backup if rollback is
needed; never overwrite the entire HA config with this repository.

## Architecture and references

The runtime is maintained Tuya Local: a single persistent device connection,
push updates, heartbeats, periodic full refreshes and reconnection. The profile
only maps data into HA entities; it does not implement a second poller.

- [Tuya Local profile format](https://github.com/make-all/tuya-local/blob/main/custom_components/tuya_local/devices/README.md)
- [Related Vevor EVSE profile](https://github.com/make-all/tuya-local/blob/main/custom_components/tuya_local/devices/vevor_l2_ev_charger.yaml)
- [Wallbox entity/energy presentation](https://www.home-assistant.io/integrations/wallbox/)
- [OCPP integration](https://github.com/lbbrhzn/ocpp) — useful EVSE modeling reference;
  this charger has not been shown to expose OCPP.
- [HA coordinator/data guidance](https://contributors.home-assistant.io/core/integrations/fetching-data/)
- [HA sensor/statistics semantics](https://contributors.home-assistant.io/core/entities/sensor/)

The profile borrows the established Tuya Local configuration conventions and is
distributed under MIT. Tuya Local and its dependencies retain their own licenses
and authorship. No upstream runtime is vendored here.

## Development

Use Python 3.14 for the tested HA release:

```bash
.venv/bin/pip install -r requirements-test.txt
TUYA_LOCAL_SOURCE=/path/to/tuya-local-checkout .venv/bin/pytest -q
```

Tests exercise the actual pinned upstream parser, including energy scaling,
unknown states, all-bit faults, missing instantaneous data, and synthetic packed
telemetry. Fixtures contain fabricated values and no real account/device IDs.
Do not upload raw Tuya/HA diagnostics; use the allowlist sanitizer first.

