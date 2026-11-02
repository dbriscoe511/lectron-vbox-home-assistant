# OCPP investigation

No configurable native OCPP connection has been established for the tested
V-BOX Pro NACS Wi-Fi, hardwareV1.2/softwareV2.0.1. This does not prove every
hardware/firmware revision lacks OCPP.

Evidence checked:

- The manufacturer Wi-Fi manual documents app pairing, modes and current
  selection, without an OCPP server URL/charge-point identity setup.
- The device settings and complete manufacturer schema expose no named OCPP
  URL, identity, credentials or enable setting.
- The Android app contains a generic `DEV_TYPE_OCPP` path for other charging
  devices. Its presence does not identify this product as an OCPP charger.
- No OCPP session or BootNotification from this charger has been observed.

OCPP chargers normally connect **outward** to a configured central-system
WebSocket URL. A closed listening port does not establish absence of OCPP.
Installing an HA OCPP server does not add OCPP to a charger's firmware.

| Addition | Appropriate upstream |
| --- | --- |
| OCPP interoperability fixes for a device that speaks OCPP | `lbbrhzn/ocpp` |
| A Tuya EVSE datapoint profile | `make-all/tuya-local` |
| Charging optimization / evcc device adapter | `evcc-io/evcc` |
| This overlay, dashboard and history tools | This repository |

Tuya Local currently restricts new issues/PRs to collaborators. Check its current
status before proposing an upstream profile. This profile already reuses its
generic persistent connection, heartbeat and reconnection implementation.

## Higher-level management

The most direct candidate is evcc's **Home Assistant charger adapter**, with
status, charging request, power and energy from this profile, plus a separate
vehicle integration for SOC. A custom HA-to-OCPP translation service is
technically possible, but adds another protocol/state machine and cannot create
new charger hardware capabilities or vehicle SOC data.

**This is not yet a tested drop-in evcc configuration.** The inspected evcc
template requires a writable `number`/`input_number` current entity. This profile
uses a discrete **select**, matching manufacturer choices16/32/40/48A. An adapter
must translate those choices honestly; don't offer arbitrary current values or
a fake helper that only changes its displayed state. The documentation labels
some parameters optional while the template marks them required; validate against
the installed evcc release. The manufacturer's lowest listed setting is16A;
do not assume6A solar-surplus regulation is supported.

Current changes may pause charging, and the car may need time or its own start
request. Complete the [five-minute observation test](charging-control.md) before
automating current changes. No OCPP server, bridge or evcc service was installed
by this investigation; no firmware, cloud endpoint or protection setting changed.

## References

- [Lectron manual index](https://ev-lectron.com/pages/user-manuals), V-BOX Pro NACS with WiFi
- [Manufacturer Wi-Fi manual](https://cdn.shopify.com/s/files/1/2948/6296/files/UM_EV-Charger48A-TSL-Pro-APP_230x170mm_GG_220824_FO_NACS_Mount.pdf?v=1728380023)
- [HA OCPP configuration](https://home-assistant-ocpp.readthedocs.io/en/latest/installation.html)
- [OCPP contribution guidelines](https://github.com/lbbrhzn/ocpp/blob/main/CONTRIBUTING.md)
- [Tuya Local contribution status](https://github.com/make-all/tuya-local#contributing)
- [evcc HA charger adapter](https://docs.evcc.io/en/chargers/home-assistant-charger/)
- [evcc template source](https://github.com/evcc-io/evcc/blob/master/templates/definition/charger/homeassistant.yaml)
