"""Binary sensor entities for the Waveshare UPS HAT (E)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DATA_BQ4050_OK,
    DATA_CHARGING,
    DATA_FAST_CHARGING,
    DATA_IP2368_OK,
    DATA_LOW_BATTERY,
    DATA_ONLINE,
    DOMAIN,
)
from .coordinator import UpsHatECoordinator
from .entity import UpsHatEEntity


@dataclass(frozen=True, kw_only=True)
class UpsHatEBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a UPS HAT (E) binary sensor."""

    value_fn: Callable[[dict[str, Any]], bool | None]


BINARY_SENSORS: tuple[UpsHatEBinarySensorDescription, ...] = (
    UpsHatEBinarySensorDescription(
        key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.PLUG,
        value_fn=lambda d: d.get(DATA_ONLINE),
    ),
    UpsHatEBinarySensorDescription(
        key="charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda d: d.get(DATA_CHARGING),
    ),
    UpsHatEBinarySensorDescription(
        key="fast_charging",
        translation_key="fast_charging",
        device_class=BinarySensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get(DATA_FAST_CHARGING),
    ),
    UpsHatEBinarySensorDescription(
        key="low_battery",
        translation_key="low_battery",
        device_class=BinarySensorDeviceClass.BATTERY,
        value_fn=lambda d: d.get(DATA_LOW_BATTERY),
    ),
    UpsHatEBinarySensorDescription(
        key="bq4050_ok",
        translation_key="bq4050_ok",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        # Inverted so "True (problem)" lights up when comm fails.
        value_fn=lambda d: (False if d.get(DATA_BQ4050_OK) else True),
    ),
    UpsHatEBinarySensorDescription(
        key="ip2368_ok",
        translation_key="ip2368_ok",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: (False if d.get(DATA_IP2368_OK) else True),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: UpsHatECoordinator = data["coordinator"]
    device_name: str = data["device_name"]

    async_add_entities(
        UpsHatEBinarySensor(coordinator, description, device_name, entry.entry_id)
        for description in BINARY_SENSORS
    )


class UpsHatEBinarySensor(UpsHatEEntity, BinarySensorEntity):
    """Binary sensor backed by a description."""

    entity_description: UpsHatEBinarySensorDescription

    def __init__(
        self,
        coordinator: UpsHatECoordinator,
        description: UpsHatEBinarySensorDescription,
        device_name: str,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator, device_name=device_name, device_id=entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
