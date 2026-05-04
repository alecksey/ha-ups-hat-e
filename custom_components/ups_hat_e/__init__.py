"""The Waveshare UPS HAT (E) integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import (
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
)
from .coordinator import UpsHatECoordinator
from .driver import create_driver

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

SERVICE_SHUTDOWN = "shutdown"
SERVICE_SHUTDOWN_SCHEMA = vol.Schema({vol.Required("entry_id"): cv.string})


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration (no YAML — config flow only)."""
    hass.data.setdefault(DOMAIN, {})

    async def _handle_shutdown(call: ServiceCall) -> None:
        entry_id = call.data["entry_id"]
        store = hass.data[DOMAIN].get(entry_id)
        if not store:
            raise HomeAssistantError(
                f"UPS HAT (E) entry '{entry_id}' is not loaded"
            )
        coordinator: UpsHatECoordinator = store["coordinator"]
        await hass.async_add_executor_job(coordinator.driver.shutdown)

    hass.services.async_register(
        DOMAIN, SERVICE_SHUTDOWN, _handle_shutdown, schema=SERVICE_SHUTDOWN_SCHEMA
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Waveshare UPS HAT (E) from a config entry."""
    options = {**entry.data, **entry.options}

    bus = int(options.get(CONF_I2C_BUS, DEFAULT_I2C_BUS))
    address = int(options.get(CONF_I2C_ADDRESS, DEFAULT_I2C_ADDRESS))
    use_mock = bool(options.get(CONF_USE_MOCK, False))

    driver = create_driver(bus=bus, address=address, use_mock=use_mock)

    coordinator = UpsHatECoordinator(
        hass,
        driver=driver,
        scan_interval=int(
            options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        ),
        battery_capacity_mah_per_cell=int(
            options.get(CONF_BATTERY_CAPACITY_MAH, DEFAULT_BATTERY_CAPACITY_MAH)
        ),
        cells_count=int(options.get(CONF_CELLS_COUNT, DEFAULT_CELLS_COUNT)),
        low_battery_threshold=int(
            options.get(CONF_LOW_BATTERY_THRESHOLD, DEFAULT_LOW_BATTERY_THRESHOLD)
        ),
        entry_id=entry.entry_id,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        # async_config_entry_first_refresh() raises ConfigEntryNotReady itself
        # for UpdateFailed, but PermissionError / FileNotFoundError on /dev/i2c-*
        # surfaces here on the very first open() attempt.
        _LOGGER.error("UPS HAT (E) failed first refresh: %s", err)
        await hass.async_add_executor_job(driver.close)
        raise ConfigEntryNotReady(str(err)) from err

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "device_name": options.get(CONF_NAME, DEFAULT_NAME),
        "battery_type": options.get(CONF_BATTERY_TYPE, DEFAULT_BATTERY_TYPE),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        store = hass.data[DOMAIN].pop(entry.entry_id, None)
        if store:
            coordinator: UpsHatECoordinator = store["coordinator"]
            await hass.async_add_executor_job(coordinator.driver.close)
    return unload_ok
