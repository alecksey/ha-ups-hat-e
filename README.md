# Waveshare UPS HAT (E) — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
![hass version](https://img.shields.io/badge/HA-2024.6%2B-blue)

A modern, async Home Assistant custom integration for the
[Waveshare UPS HAT (E)](https://www.waveshare.com/wiki/UPS_HAT_(E))
(4×21700 / 4×18650 cells, USB-C PD input, BQ4050 + IP2368 chipset).
Reads the UPS over I2C and exposes battery voltage / current / power /
percentage / runtime, USB-C input metrics, per-cell voltages, charge
stage, fault flags, and AC-power / charging binary sensors.

Released under the [**MIT License**](LICENSE).

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
- Service `ups_hat_e.shutdown` to issue the UPS-side shutdown sequence
  (write `0x55` to register `0x01`).
- Translations: English + Ukrainian.
- Mock driver flag for development on a non-Pi host.

## Installation

### Via HACS (recommended)

1. In HACS → Integrations → ⋮ → **Custom repositories**, add
   `https://github.com/delphiworld/hacs-ups-hat-e` as type
   **Integration**.
2. Install **Waveshare UPS HAT (E)**, then restart Home Assistant.
3. Go to **Settings → Devices & Services → + Add integration → Waveshare
   UPS HAT (E)**.

### Manual

Copy `custom_components/ups_hat_e/` to `<config>/custom_components/` and
restart Home Assistant.

## ⚠️ Container & I2C permissions

Home Assistant runs inside a container (HA OS / Supervised / Container /
Core in venv). Reading `/dev/i2c-*` requires the container to have **(a)
the device file mounted in** and **(b) read/write access** to it.

### Home Assistant OS (HAOS) on Raspberry Pi

I2C is enabled by default. The Supervisor mounts `/dev/i2c-1` into
the `homeassistant` container, but `smbus2` still needs root inside the
container to open it. With HAOS this works out-of-the-box because the
HA Core container runs as root.

If `/dev/i2c-1` is missing, edit `/boot/config.txt` (or use the
[i2c-tools add-on](https://github.com/home-assistant/addons-development/tree/master/i2c-tools)
once for diagnostics):

```ini
dtparam=i2c_arm=on
```

…and reboot.

### Home Assistant Container (Docker)

The container needs the device passed in and elevated capabilities:

```bash
docker run -d --name homeassistant \
  --restart=unless-stopped \
  --privileged \
  -e TZ=Europe/Kyiv \
  -v /PATH_TO_YOUR_CONFIG:/config \
  -v /run/dbus:/run/dbus:ro \
  --device=/dev/i2c-1 \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

If you prefer not to use `--privileged`, the minimum required is the
device mapping plus `--cap-add=SYS_RAWIO` **and** the host’s `i2c` group
GID (look it up with `getent group i2c`):

```bash
--device=/dev/i2c-1 \
--cap-add=SYS_RAWIO \
--group-add 998   # whatever GID `i2c` group has on the host
```

### Home Assistant Supervised

Same as Container — the Supervisor manages device mappings via the
add-on model, but the **Core container itself** needs `/dev/i2c-1`. If
you’re seeing `permission_denied` errors during setup, edit
`/etc/docker/daemon.json` or your override compose file and pass the
device through.

### Home Assistant Core (venv on Raspberry Pi OS)

The OS user (typically `homeassistant`) must be in the `i2c` group:

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

If `i2cdetect` doesn't see `0x2D`, Home Assistant won't either — fix the
hardware or wiring first.

## Sensors exposed

| Sensor | Unit | Class | Notes |
| --- | --- | --- | --- |
| Battery | % | `battery` | Battery state-of-charge from the BQ4050. |
| Battery voltage | V | `voltage` | Pack voltage (4S). |
| Battery current | A | `current` | Signed: + charging, − discharging. |
| Battery power | W | `power` | Computed (V × I). |
| Remaining capacity | Wh | `energy_storage` | Computed (mAh × V). |
| Remaining capacity (mAh) | mAh | – | Raw from BQ4050. |
| Time to empty | min | `duration` | Available when discharging. |
| Time to full | min | `duration` | Available when charging. |
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

- **`permission_denied`** during setup → see the container section
  above. Try `sudo i2cdetect -y 1` on the host first.
- **`device_not_responding`** → wrong address, the UPS isn't powered, or
  the chip is held in reset. Verify with `i2cdetect`.
- **Battery percentage / runtime stuck or weird** → the BQ4050 needs a
  full charge/discharge cycle (or two) to calibrate. This is normal.
- **Want to test on a laptop?** Toggle the *Use simulated data* switch
  in setup or options. The integration will use a mock driver that
  generates plausible values.

## Development

The driver layer is pure Python (no Home Assistant imports) so it can be
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

This project is licensed under the **MIT License** — see the
[`LICENSE`](LICENSE) file for the full text. In short: do whatever you
want with the code, just keep the copyright + license notice.

## Credits

See the [References & inspiration](#references--inspiration) section
above for the projects that informed this integration. Issues and pull
requests are welcome.
