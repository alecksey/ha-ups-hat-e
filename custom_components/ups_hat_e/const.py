"""Constants for the Waveshare UPS HAT (E) integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "ups_hat_e"
MANUFACTURER: Final = "Waveshare"
MODEL: Final = "UPS HAT (E)"

# Configuration keys
CONF_I2C_BUS: Final = "i2c_bus"
CONF_I2C_ADDRESS: Final = "i2c_address"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_BATTERY_TYPE: Final = "battery_type"
CONF_BATTERY_CAPACITY_MAH: Final = "battery_capacity_mah"
CONF_CELLS_COUNT: Final = "cells_count"
CONF_LOW_BATTERY_THRESHOLD: Final = "low_battery_threshold"
CONF_USE_MOCK: Final = "use_mock"

# Defaults
DEFAULT_NAME: Final = "UPS HAT E"
DEFAULT_I2C_BUS: Final = 1
DEFAULT_I2C_ADDRESS: Final = 0x2D
DEFAULT_SCAN_INTERVAL: Final = 30  # seconds
DEFAULT_BATTERY_TYPE: Final = "21700"
DEFAULT_BATTERY_CAPACITY_MAH: Final = 5000  # mAh per cell (21700 typical)
DEFAULT_CELLS_COUNT: Final = 4
DEFAULT_LOW_BATTERY_THRESHOLD: Final = 20  # percent

# Allowed values
BATTERY_TYPES: Final = {
    "21700": {"label": "21700 (5000 mAh)", "default_capacity_mah": 5000},
    "18650": {"label": "18650 (3000 mAh)", "default_capacity_mah": 3000},
    "custom": {"label": "Custom", "default_capacity_mah": 5000},
}

MIN_SCAN_INTERVAL: Final = 5
MAX_SCAN_INTERVAL: Final = 600

# I2C registers (per Waveshare wiki: https://www.waveshare.com/wiki/UPS_HAT_(E)_Register)
REG_POWEROFF: Final = 0x01
REG_CHARGING_STATUS: Final = 0x02
REG_COMMUNICATION: Final = 0x03
REG_VBUS_BLOCK: Final = 0x10  # 6 bytes: voltage (LE), current (LE), power (LE)
REG_BATTERY_BLOCK: Final = 0x20  # 12 bytes
REG_CELL_BLOCK: Final = 0x30  # 8 bytes (4 cells x 2)
REG_SOFTWARE_REVISION: Final = 0x50

# Magic value to write to REG_POWEROFF to initiate shutdown
POWEROFF_MAGIC: Final = 0x55

# Charging state (low 3 bits of register 0x02)
CHARGE_STATE_NAMES: Final = {
    0: "standby",
    1: "trickle",
    2: "constant_current",
    3: "constant_voltage",
    4: "pending",
    5: "full",
    6: "timeout",
}

# Status text (composite, derived) — translated via state attributes
STATE_IDLE: Final = "idle"
STATE_CHARGING: Final = "charging"
STATE_FAST_CHARGING: Final = "fast_charging"
STATE_DISCHARGING: Final = "discharging"
STATE_FULL: Final = "full"

# Data dictionary keys (kept stable for entity wiring)
DATA_VBUS_VOLTAGE: Final = "vbus_voltage"
DATA_VBUS_CURRENT: Final = "vbus_current"
DATA_VBUS_POWER: Final = "vbus_power"
DATA_BATTERY_VOLTAGE: Final = "battery_voltage"
DATA_BATTERY_CURRENT: Final = "battery_current"
DATA_BATTERY_POWER: Final = "battery_power"
DATA_BATTERY_PERCENT: Final = "battery_percent"
DATA_REMAINING_CAPACITY_MAH: Final = "remaining_capacity_mah"
DATA_REMAINING_CAPACITY_WH: Final = "remaining_capacity_wh"
DATA_RUNTIME_MIN: Final = "runtime_min"
DATA_TIME_TO_FULL_MIN: Final = "time_to_full_min"
DATA_RUNTIME_PRETTY: Final = "runtime_pretty"
DATA_TIME_TO_FULL_PRETTY: Final = "time_to_full_pretty"
DATA_CELL1_VOLTAGE: Final = "cell1_voltage"
DATA_CELL2_VOLTAGE: Final = "cell2_voltage"
DATA_CELL3_VOLTAGE: Final = "cell3_voltage"
DATA_CELL4_VOLTAGE: Final = "cell4_voltage"
DATA_CHARGE_STATE: Final = "charge_state"
DATA_STATUS: Final = "status"
DATA_ONLINE: Final = "online"
DATA_CHARGING: Final = "charging"
DATA_FAST_CHARGING: Final = "fast_charging"
DATA_LOW_BATTERY: Final = "low_battery"
DATA_BQ4050_OK: Final = "bq4050_ok"
DATA_IP2368_OK: Final = "ip2368_ok"
DATA_FIRMWARE_REVISION: Final = "firmware_revision"
