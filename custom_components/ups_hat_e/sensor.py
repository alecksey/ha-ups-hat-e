"""Sensor entities for the Waveshare UPS HAT (E)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DATA_BATTERY_CURRENT,
    DATA_BATTERY_PERCENT,
    DATA_BATTERY_POWER,
    DATA_BATTERY_VOLTAGE,
    DATA_CELL1_VOLTAGE,
    DATA_CELL2_VOLTAGE,
    DATA_CELL3_VOLTAGE,
    DATA_CELL4_VOLTAGE,
    DATA_CHARGE_STATE,
    DATA_FIRMWARE_REVISION,
    DATA_REMAINING_CAPACITY_MAH,
    DATA_REMAINING_CAPACITY_WH,
    DATA_RUNTIME_MIN,
    DATA_RUNTIME_PRETTY,
    DATA_STATUS,
    DATA_TIME_TO_FULL_MIN,
    DATA_TIME_TO_FULL_PRETTY,
    DATA_VBUS_CURRENT,
    DATA_VBUS_POWER,
    DATA_VBUS_VOLTAGE,
    DOMAIN,
)
from .coordinator import UpsHatECoordinator
from .entity import UpsHatEEntity


@dataclass(frozen=True, kw_only=True)
class UpsHatESensorDescription(SensorEntityDescription):
    """Describes a UPS HAT (E) sensor."""

    value_fn: Callable[[dict], Any]
    extra_attrs_fn: Callable[[dict], dict] | None = None


SENSORS: tuple[UpsHatESensorDescription, ...] = (
    # ---- Battery primary ------------------------------------------------
    UpsHatESensorDescription(
        key="battery_percent",
        translation_key="battery_percent",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda d: d.get(DATA_BATTERY_PERCENT),
    ),
    UpsHatESensorDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=2,
        value_fn=lambda d: d.get(DATA_BATTERY_VOLTAGE),
    ),
    UpsHatESensorDescription(
        key="battery_current",
        translation_key="battery_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda d: d.get(DATA_BATTERY_CURRENT),
    ),
    UpsHatESensorDescription(
        key="battery_power",
        translation_key="battery_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=2,
        value_fn=lambda d: d.get(DATA_BATTERY_POWER),
    ),
    UpsHatESensorDescription(
        key="remaining_capacity_wh",
        translation_key="remaining_capacity_wh",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=1,
        value_fn=lambda d: d.get(DATA_REMAINING_CAPACITY_WH),
    ),
    UpsHatESensorDescription(
        key="remaining_capacity_mah",
        translation_key="remaining_capacity_mah",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="mAh",
        suggested_display_precision=0,
        value_fn=lambda d: d.get(DATA_REMAINING_CAPACITY_MAH),
    ),
    # ---- Pretty duration sensors (default UI) ---------------------------
    # Render as "45m" / "5h 30m" / "2d 5h 30m". Raw minutes go in the
    # ``raw_minutes`` attribute for templates / graphs.
    UpsHatESensorDescription(
        key="runtime",
        translation_key="runtime",
        icon="mdi:battery-clock",
        value_fn=lambda d: d.get(DATA_RUNTIME_PRETTY),
        extra_attrs_fn=lambda d: {"raw_minutes": d.get(DATA_RUNTIME_MIN)},
    ),
    UpsHatESensorDescription(
        key="time_to_full",
        translation_key="time_to_full",
        icon="mdi:battery-clock-outline",
        value_fn=lambda d: d.get(DATA_TIME_TO_FULL_PRETTY),
        extra_attrs_fn=lambda d: {"raw_minutes": d.get(DATA_TIME_TO_FULL_MIN)},
    ),
    # Raw numeric versions — disabled by default but available for graphs
    # and statistics (state_class MEASUREMENT).
    UpsHatESensorDescription(
        key="runtime_min",
        translation_key="runtime_min",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get(DATA_RUNTIME_MIN),
    ),
    UpsHatESensorDescription(
        key="time_to_full_min",
        translation_key="time_to_full_min",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get(DATA_TIME_TO_FULL_MIN),
    ),
    # ---- USB-C input ----------------------------------------------------
    UpsHatESensorDescription(
        key="vbus_voltage",
        translation_key="vbus_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=2,
        value_fn=lambda d: d.get(DATA_VBUS_VOLTAGE),
    ),
    UpsHatESensorDescription(
        key="vbus_current",
        translation_key="vbus_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        suggested_display_precision=0,
        value_fn=lambda d: d.get(DATA_VBUS_CURRENT),
    ),
    UpsHatESensorDescription(
        key="vbus_power",
        translation_key="vbus_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=2,
        value_fn=lambda d: d.get(DATA_VBUS_POWER),
    ),
    # ---- Per-cell voltages (diagnostic) --------------------------------
    UpsHatESensorDescription(
        key="cell1_voltage",
        translation_key="cell1_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=3,
        value_fn=lambda d: d.get(DATA_CELL1_VOLTAGE),
    ),
    UpsHatESensorDescription(
        key="cell2_voltage",
        translation_key="cell2_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=3,
        value_fn=lambda d: d.get(DATA_CELL2_VOLTAGE),
    ),
    UpsHatESensorDescription(
        key="cell3_voltage",
        translation_key="cell3_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=3,
        value_fn=lambda d: d.get(DATA_CELL3_VOLTAGE),
    ),
    UpsHatESensorDescription(
        key="cell4_voltage",
        translation_key="cell4_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=3,
        value_fn=lambda d: d.get(DATA_CELL4_VOLTAGE),
    ),
    # ---- Status (textual) ----------------------------------------------
    UpsHatESensorDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=[
            "idle",
            "charging",
            "fast_charging",
            "discharging",
            "full",
        ],
        value_fn=lambda d: d.get(DATA_STATUS),
    ),
    UpsHatESensorDescription(
        key="charge_state",
        translation_key="charge_state",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        options=[
            "standby",
            "trickle",
            "constant_current",
            "constant_voltage",
            "pending",
            "full",
            "timeout",
            "unknown",
        ],
        value_fn=lambda d: d.get(DATA_CHARGE_STATE),
    ),
    UpsHatESensorDescription(
        key="firmware_revision",
        translation_key="firmware_revision",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get(DATA_FIRMWARE_REVISION),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: UpsHatECoordinator = data["coordinator"]
    device_name: str = data["device_name"]

    async_add_entities(
        UpsHatESensor(coordinator, description, device_name, entry.entry_id)
        for description in SENSORS
    )


class UpsHatESensor(UpsHatEEntity, SensorEntity):
    """Sensor backed by a description."""

    entity_description: UpsHatESensorDescription

    def __init__(
        self,
        coordinator: UpsHatECoordinator,
        description: UpsHatESensorDescription,
        device_name: str,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator, device_name=device_name, device_id=entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None
        if self.entity_description.extra_attrs_fn is None:
            return None
        attrs = self.entity_description.extra_attrs_fn(self.coordinator.data)
        return {k: v for k, v in attrs.items() if v is not None} or None
