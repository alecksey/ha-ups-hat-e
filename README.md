# Waveshare UPS HAT (E) — Home Assistant Integration

[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=alecksey&repository=ha-ups-hat-e&category=integration)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
![hass version](https://img.shields.io/badge/HA-2024.6%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

<p align="center">
  <img src="https://www.waveshare.com/media/catalog/product/cache/1/image/800x800/9df78eab33525d08d6e5fb8d27136e95/u/p/ups-hat-e-3.jpg" alt="Waveshare UPS HAT (E)" width="420">
</p>

A modern, async Home Assistant custom integration for the
[Waveshare UPS HAT (E)](https://www.waveshare.com/wiki/UPS_HAT_(E))
(4× 21700 / 18650 cells, USB-C PD input, BQ4050 fuel gauge + IP2368
charger). Reads the UPS over I2C and exposes battery voltage / current /
power / percentage / runtime, USB-C input metrics, per-cell voltages,
charge stage, fault flags, and AC-power / charging binary sensors.

Released under the [**MIT License**](LICENSE).

## Quick install via HACS

1. Click the **Open in HACS** badge above (or copy the link below).
2. HACS will open the repo dialog — confirm install.
3. Restart Home Assistant.
4. Settings → Devices & Services → **Add Integration** → "Waveshare UPS HAT (E)".

[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=alecksey&repository=ha-ups-hat-e&category=integration)

If the badge doesn't work, in HACS → Integrations → ⋮ → **Custom
repositories**, paste `https://github.com/alecksey/ha-ups-hat-e` and
choose category **Integration**.

### Manual install

Copy `custom_components/ups_hat_e/` to `<config>/custom_components/` and
restart Home Assistant.

## References & inspiration

This integration was built from scratch, but it stands on the shoulders
of several existing projects and the official Waveshare documentation.
Many thanks to the authors of:

**Documentation**

- [Waveshare Wiki — UPS HAT (E)](https://www.waveshare.com/wiki/UPS_HAT_(E)) — overall device documentation, schematics, sample code.
- [Waveshare Wiki — UPS HAT (E) Register Map](https://www.waveshare.com/wiki/UPS_HAT_(E)_Register) — authoritative I2C register reference (address `0x2D`, register blocks `0x02` / `0x10` / `0x20` / `0x30`).
- [Product page — `waveshare.com/ups-hat-e.htm`](https://www.waveshare.com/ups-hat-e.htm).

**Reference implementations**

- [`odya/hass-ina219-ups-hat`](https://github.com/odya/hass-ina219-ups-hat) — Home Assistant integration architecture pattern (DataUpdateCoordinator, entity layout, HACS metadata) for the older INA219-based UPS HAT, used as a structural template.
- [`Orgjvr/ups_hat_e`](https://github.com/Orgjvr/ups_hat_e) — original (currently broken) HACS attempt for the (E) variant; supplied the initial register-decoding pseudocode.
- [`int08h/waveshare-ups-hat-e`](https://github.com/int08h/waveshare-ups-hat-e) — a Rust library that documents the register layout, charger states, and PD/VBUS bit fields cleanly. Great cross-reference.
- [`maaad/ups-hat-controller`](https://github.com/maaad/ups-hat-controller) — C++ daemon implementing low-voltage shutdown and journald logging; confirmed signed/unsigned conversions and cell-voltage handling.

> Note: the (E) device is **not** an INA219. It speaks a higher-level
> register protocol exposed by the on-board UPS MCU at I2C address
> `0x2D`, which talks to the BQ4050 fuel gauge and IP2368 charger
> internally.

## Features

- Native **Config Flow (UI setup)** with options flow for runtime tweaks.
- Battery type selector — `21700`, `18650`, or `custom` capacity.
- Configurable I2C bus number, address, scan interval, and low-battery
  threshold.
- Sensors (auto-grouped under one device):
  - Battery: percentage, voltage, current (signed), power, remaining
    capacity (Wh / mAh), time-to-empty / time-to-full.
  - USB-C input (VBUS): voltage, current, power.
  - Per-cell voltages (×4) — diagnostic category.
  - Status (`idle` / `charging` / `fast_charging` / `discharging` /
    `full`) + Charge stage (CC / CV / Trickle / …).
  - Firmware revision (diagnostic, disabled by default).
- Binary sensors: AC power, charging, USB-C PD active, low battery,
  BQ4050 / IP2368 communication faults.
- Pretty duration formatting: `45m` / `5h 30m` / `1d 2h 15m` (raw
  minutes still available as an entity attribute).
- Service `ups_hat_e.shutdown` — issues the UPS-side shutdown sequence
  (write `0x55` to register `0x01`).
- Translations: English + Ukrainian.
- Mock driver flag for development on a non-Pi host.

## ⚠️ Prerequisite: I2C must be enabled on the Pi

Home Assistant runs inside a container, so two things have to be true:
1. The kernel exposes `/dev/i2c-1`.
2. The HA Core container has access to it.

The easiest path on Home Assistant OS is to use the community
[**HassOS I2C Configurator**](https://github.com/adamoutler/HassOSConfigurator/tree/main/Pi4EnableI2C)
add-on:

1. Settings → Add-ons → Add-on Store → ⋮ → **Repositories**.
2. Add `https://github.com/adamoutler/HassOSConfigurator`.
3. Install **Pi4EnableI2C** (despite the name, it works on Pi3/4/5).
4. Start it once. It edits `/boot/config.txt` (`dtparam=i2c_arm=on`),
   loads `i2c-dev`, and survives reboots.
5. Reboot the host.
6. *(Optional)* Uninstall the add-on — its job is done after the first
   run.

After the reboot, `/dev/i2c-1` will appear inside the HA container and
this integration will be able to open it.

If you're not on HAOS, see the next section.

## I2C access in other HA installs

### Home Assistant Container (Docker)

Pass the device to the container and add the right capabilities:

```bash
docker run -d --name homeassistant \
  --restart=unless-stopped \
  --privileged \
  -v /PATH_TO_YOUR_CONFIG:/config \
  --device=/dev/i2c-1 \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

If you'd rather avoid `--privileged`, the minimum is:

```bash
--device=/dev/i2c-1 \
--cap-add=SYS_RAWIO \
--group-add 998   # whatever GID the host's `i2c` group has
```

(Find the GID with `getent group i2c`.)

### Home Assistant Supervised

The Supervisor manages add-on device mappings, but the **Core
container** itself still needs `/dev/i2c-1`. If you see
`permission_denied` during setup, edit `/etc/docker/daemon.json` (or
your override compose) and pass the device through.

### Home Assistant Core (venv on Raspberry Pi OS)

Add the OS user to the `i2c` group:

```bash
sudo usermod -aG i2c homeassistant
sudo systemctl restart home-assistant@homeassistant
```

### Quick I2C sanity check on the host

```bash
sudo apt install i2c-tools
sudo i2cdetect -y 1
# expect to see address 2d in the grid
```

If `i2cdetect` doesn't see `0x2D`, Home Assistant won't either — fix
the wiring or the OS-level config first.

## Sensors exposed

| Sensor | Unit | Class | Notes |
| --- | --- | --- | --- |
| Battery | % | `battery` | State-of-charge from the BQ4050. |
| Battery voltage | V | `voltage` | Pack voltage (4S). |
| Battery current | A | `current` | Signed: + charging, − discharging. |
| Battery power | W | `power` | Computed (V × I). |
| Remaining capacity | Wh | `energy_storage` | Computed (mAh × V). |
| Remaining capacity (mAh) | mAh | – | Raw from BQ4050. |
| Time to empty | – | – | Pretty: `45m` / `5h 30m` / `1d 2h`. Raw minutes in `raw_minutes` attr. |
| Time to full | – | – | Same format, while charging. |
| Time to empty / full (minutes) | min | `duration` | Numeric, disabled by default — enable for graphs. |
| USB-C voltage / current / power | V / mA / W | – | From IP2368. |
| Cell N voltage (×4) | V | `voltage` | Diagnostic. |
| Status | – | `enum` | Composite: `idle`/`charging`/`fast_charging`/`discharging`/`full`. |
| Charge stage | – | `enum` | Diagnostic: CC / CV / trickle / etc. |
| Firmware revision | – | – | Diagnostic, disabled by default. |

| Binary sensor | Class | Notes |
| --- | --- | --- |
| AC power | `plug` | USB-C input is providing power. |
| Charging | `battery_charging` | Battery is being charged. |
| USB-C PD | `power` | Power Delivery negotiated. |
| Low battery | `battery` | Below the configured threshold. |
| BQ4050 / IP2368 fault | `problem` | Diagnostic — internal comm fault. |

## Service: `ups_hat_e.shutdown`

Sends the shutdown command to the UPS. The UPS will cut its 5V output
~30 seconds later — orchestrate this with a Home Assistant automation
that **first** triggers a clean OS shutdown of the Pi.

```yaml
service: ups_hat_e.shutdown
data:
  entry_id: 01H... # find in Settings → Devices → UPS HAT (E) → ⋮ → "View configuration entry"
```

## Suggested automation: shut down on power loss

```yaml
alias: UPS — clean shutdown on AC loss
trigger:
  - platform: state
    entity_id: binary_sensor.ups_hat_e_ac_power
    to: "off"
    for: "00:05:00"   # tolerate brief outages
condition:
  - condition: numeric_state
    entity_id: sensor.ups_hat_e_battery
    below: 25
action:
  - service: notify.persistent_notification
    data:
      message: "AC down + battery <25%, shutting down."
  - service: hassio.host_shutdown   # or shell_command equivalent
```

## Troubleshooting

- **`permission_denied`** during setup → see the I2C-access section
  above. Try `sudo i2cdetect -y 1` on the host first. On HAOS, install
  the [HassOS I2C Configurator add-on](https://github.com/adamoutler/HassOSConfigurator/tree/main/Pi4EnableI2C).
- **`device_not_responding`** → wrong address, the UPS isn't powered, or
  the chip is held in reset. Verify with `i2cdetect`.
- **Battery percentage / runtime stuck or weird** → the BQ4050 needs a
  full charge/discharge cycle (or two) to calibrate. This is normal.
- **Want to test on a laptop?** Toggle the *Use simulated data* switch
  in setup or options. The integration uses a mock driver that produces
  plausible values for development.
- **OptionsFlow throws 500 Internal Server Error** → make sure you're on
  the latest version (≥ 0.1.1); HA 2024.11+ requires a different
  options-flow signature than older releases.

## Development

The driver layer is pure Python (no Home Assistant imports) and can be
exercised in isolation:

```python
from custom_components.ups_hat_e.driver import create_driver

drv = create_driver(bus=1, address=0x2D, use_mock=False)
drv.open()
print(drv.read_battery())
print(drv.read_charging_status())
drv.close()
```

Pull requests welcome.

## License

MIT — see the [`LICENSE`](LICENSE) file for the full text.

## Credits

See the [References & inspiration](#references--inspiration) section
above for the projects that informed this integration.
