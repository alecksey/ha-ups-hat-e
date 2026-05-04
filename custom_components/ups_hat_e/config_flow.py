"""Config & options flow for the Waveshare UPS HAT (E)."""

from __future__ import annotations

import logging
import os
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    BATTERY_TYPES,
    CONF_BATTERY_CAPACITY_MAH,
    CONF_BATTERY_TYPE,
    CONF_CELLS_COUNT,
    CONF_I2C_ADDRESS,
    CONF_I2C_BUS,
    CONF_LOW_BATTERY_THRESHOLD,
    CONF_SCAN_INTERVAL,
    CONF_USE_MOCK,
    DEFAULT_BATTERY_CAPACITY_MAH,
    DEFAULT_BATTERY_TYPE,
    DEFAULT_CELLS_COUNT,
    DEFAULT_I2C_ADDRESS,
    DEFAULT_I2C_BUS,
    DEFAULT_LOW_BATTERY_THRESHOLD,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .driver import create_driver

_LOGGER = logging.getLogger(__name__)


def _parse_address(value):
    """Accept ``0x2D`` / ``45`` / ``0X2d`` / ``2D``."""
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        raise ValueError("Empty I2C address")
    lower = text.lower()
    if lower.startswith("0x"):
        return int(text, 16)
    if any(c in lower for c in "abcdef"):
        return int(text, 16)
    return int(text, 10)


def _format_address(value):
    addr = _parse_address(value)
    return f"0x{addr:02X}"


def _battery_type_options():
    return [{"value": k, "label": v["label"]} for k, v in BATTERY_TYPES.items()]


def _common_schema(defaults, *, include_user_only_fields):
    """Build the schema shared by config and options flows.

    ``include_user_only_fields=True`` adds the fields that only make sense
    in the initial setup (name + bus + address).
    """
    fields = {}

    if include_user_only_fields:
        fields[vol.Required(
            CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)
        )] = str
        fields[vol.Required(
            CONF_I2C_BUS, default=defaults.get(CONF_I2C_BUS, DEFAULT_I2C_BUS),
        )] = NumberSelector(
            NumberSelectorConfig(min=0, max=20, step=1, mode=NumberSelectorMode.BOX)
        )
        fields[vol.Required(
            CONF_I2C_ADDRESS,
            default=_format_address(
                defaults.get(CONF_I2C_ADDRESS, DEFAULT_I2C_ADDRESS)
            ),
        )] = str

    fields[vol.Required(
        CONF_BATTERY_TYPE,
        default=defaults.get(CONF_BATTERY_TYPE, DEFAULT_BATTERY_TYPE),
    )] = SelectSelector(
        SelectSelectorConfig(
            options=_battery_type_options(),
            mode=SelectSelectorMode.DROPDOWN,
            translation_key="battery_type",
        )
    )
    fields[vol.Required(
        CONF_BATTERY_CAPACITY_MAH,
        default=defaults.get(
            CONF_BATTERY_CAPACITY_MAH, DEFAULT_BATTERY_CAPACITY_MAH
        ),
    )] = NumberSelector(
        NumberSelectorConfig(
            min=500, max=10000, step=100,
            unit_of_measurement="mAh",
            mode=NumberSelectorMode.BOX,
        )
    )
    fields[vol.Required(
        CONF_CELLS_COUNT,
        default=defaults.get(CONF_CELLS_COUNT, DEFAULT_CELLS_COUNT),
    )] = NumberSelector(
        NumberSelectorConfig(min=1, max=4, step=1, mode=NumberSelectorMode.BOX)
    )
    fields[vol.Required(
        CONF_LOW_BATTERY_THRESHOLD,
        default=defaults.get(
            CONF_LOW_BATTERY_THRESHOLD, DEFAULT_LOW_BATTERY_THRESHOLD
        ),
    )] = NumberSelector(
        NumberSelectorConfig(
            min=1, max=99, step=1,
            unit_of_measurement="%",
            mode=NumberSelectorMode.SLIDER,
        )
    )
    fields[vol.Required(
        CONF_SCAN_INTERVAL,
        default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )] = NumberSelector(
        NumberSelectorConfig(
            min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL, step=1,
            unit_of_measurement="s",
            mode=NumberSelectorMode.BOX,
        )
    )
    fields[vol.Optional(
        CONF_USE_MOCK, default=defaults.get(CONF_USE_MOCK, False)
    )] = bool
    return vol.Schema(fields)


class UpsHatEConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Initial setup flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                address = _parse_address(user_input[CONF_I2C_ADDRESS])
                if not 0x03 <= address <= 0x77:
                    raise ValueError("address out of I2C range")
                bus = int(user_input[CONF_I2C_BUS])
                use_mock = bool(user_input.get(CONF_USE_MOCK, False))

                if not use_mock:
                    await self.hass.async_add_executor_job(_probe_bus, bus, address)
            except FileNotFoundError:
                errors[CONF_I2C_BUS] = "i2c_bus_not_found"
            except PermissionError:
                errors["base"] = "permission_denied"
            except OSError as err:
                _LOGGER.warning("I2C probe failed: %s", err)
                errors["base"] = "device_not_responding"
            except ValueError:
                errors[CONF_I2C_ADDRESS] = "invalid_address"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow probe")
                errors["base"] = "unknown"

            if not errors:
                uid = f"{bus}:0x{address:02X}"
                await self.async_set_unique_id(uid)
                self._abort_if_unique_id_configured()

                battery_type = user_input.get(CONF_BATTERY_TYPE, DEFAULT_BATTERY_TYPE)
                default_capacity = BATTERY_TYPES.get(battery_type, {}).get(
                    "default_capacity_mah", DEFAULT_BATTERY_CAPACITY_MAH
                )

                data = {
                    CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME),
                    CONF_I2C_BUS: bus,
                    CONF_I2C_ADDRESS: address,
                    CONF_BATTERY_TYPE: battery_type,
                    CONF_BATTERY_CAPACITY_MAH: int(
                        user_input.get(CONF_BATTERY_CAPACITY_MAH, default_capacity)
                    ),
                    CONF_CELLS_COUNT: int(
                        user_input.get(CONF_CELLS_COUNT, DEFAULT_CELLS_COUNT)
                    ),
                    CONF_LOW_BATTERY_THRESHOLD: int(
                        user_input.get(
                            CONF_LOW_BATTERY_THRESHOLD,
                            DEFAULT_LOW_BATTERY_THRESHOLD,
                        )
                    ),
                    CONF_SCAN_INTERVAL: int(
                        user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                    ),
                    CONF_USE_MOCK: use_mock,
                }
                return self.async_create_entry(title=data[CONF_NAME], data=data)

        defaults = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=_common_schema(defaults, include_user_only_fields=True),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return UpsHatEOptionsFlow()


class UpsHatEOptionsFlow(config_entries.OptionsFlow):
    """Options flow.

    HA 2024.11+ assigns ``self.config_entry`` automatically via a read-only
    descriptor — assigning it ourselves causes 500 Internal Server Error.
    The framework calls ``async_get_options_flow(config_entry)`` and wires the
    entry up before our first step runs, so we just rely on
    ``self.config_entry``.
    """

    async def async_step_init(self, user_input=None):
        entry = self.config_entry
        current = {**entry.data, **(entry.options or {})}
        errors = {}

        if user_input is not None:
            try:
                data = {
                    CONF_BATTERY_TYPE: user_input.get(
                        CONF_BATTERY_TYPE,
                        current.get(CONF_BATTERY_TYPE, DEFAULT_BATTERY_TYPE),
                    ),
                    CONF_BATTERY_CAPACITY_MAH: int(
                        user_input.get(
                            CONF_BATTERY_CAPACITY_MAH,
                            current.get(
                                CONF_BATTERY_CAPACITY_MAH,
                                DEFAULT_BATTERY_CAPACITY_MAH,
                            ),
                        )
                    ),
                    CONF_CELLS_COUNT: int(
                        user_input.get(
                            CONF_CELLS_COUNT,
                            current.get(CONF_CELLS_COUNT, DEFAULT_CELLS_COUNT),
                        )
                    ),
                    CONF_LOW_BATTERY_THRESHOLD: int(
                        user_input.get(
                            CONF_LOW_BATTERY_THRESHOLD,
                            current.get(
                                CONF_LOW_BATTERY_THRESHOLD,
                                DEFAULT_LOW_BATTERY_THRESHOLD,
                            ),
                        )
                    ),
                    CONF_SCAN_INTERVAL: int(
                        user_input.get(
                            CONF_SCAN_INTERVAL,
                            current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                        )
                    ),
                    CONF_USE_MOCK: bool(
                        user_input.get(
                            CONF_USE_MOCK,
                            current.get(CONF_USE_MOCK, False),
                        )
                    ),
                }
                return self.async_create_entry(title="", data=data)
            except (TypeError, ValueError):
                _LOGGER.exception("Invalid options input")
                errors["base"] = "invalid_value"

        return self.async_show_form(
            step_id="init",
            data_schema=_common_schema(current, include_user_only_fields=False),
            errors=errors,
        )


def _probe_bus(bus, address):
    """Open the bus and read register 0x50 (firmware) to verify communication."""
    device_path = f"/dev/i2c-{bus}"
    if not os.path.exists(device_path):
        raise FileNotFoundError(f"{device_path} does not exist")

    driver = create_driver(bus=bus, address=address, use_mock=False)
    try:
        driver.open()
        driver.read_firmware_revision()
    finally:
        try:
            driver.close()
        except Exception:
            pass
