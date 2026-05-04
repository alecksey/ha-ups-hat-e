"""Base entity for the UPS HAT (E) integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import UpsHatECoordinator


class UpsHatEEntity(CoordinatorEntity[UpsHatECoordinator]):
    """Base class for UPS HAT (E) entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UpsHatECoordinator,
        device_name: str,
        device_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        firmware = (
            coordinator.data.get("firmware_revision")
            if coordinator.data
            else None
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=firmware,
        )

    def _get(self, key: str):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(key)
