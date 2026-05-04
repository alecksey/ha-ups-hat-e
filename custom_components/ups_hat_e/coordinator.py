"""DataUpdateCoordinator for the Waveshare UPS HAT (E)."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CHARGE_STATE_NAMES,
    DATA_BATTERY_CURRENT,
    DATA_BATTERY_PERCENT,
    DATA_BATTERY_POWER,
    DATA_BATTERY_VOLTAGE,
    DATA_BQ4050_OK,
    DATA_CELL1_VOLTAGE,
    DATA_CELL2_VOLTAGE,
    DATA_CELL3_VOLTAGE,
    DATA_CELL4_VOLTAGE,
    DATA_CHARGE_STATE,
    DATA_CHARGING,
    DATA_FAST_CHARGING,
    DATA_FIRMWARE_REVISION,
    DATA_IP2368_OK,
    DATA_LOW_BATTERY,
    DATA_ONLINE,
    DATA_REMAINING_CAPACITY_MAH,
    DATA_REMAINING_CAPACITY_WH,
    DATA_RUNTIME_MIN,
    DATA_STATUS,
    DATA_TIME_TO_FULL_MIN,
    DATA_VBUS_CURRENT,
    DATA_VBUS_POWER,
    DATA_VBUS_VOLTAGE,
    DOMAIN,
    STATE_CHARGING,
    STATE_DISCHARGING,
    STATE_FAST_CHARGING,
    STATE_FULL,
    STATE_IDLE,
)
from .driver import UpsHatDriver

_LOGGER = logging.getLogger(__name__)


class UpsHatECoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the UPS HAT (E) and exposes a normalized data dict."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        driver: UpsHatDriver,
        scan_interval: int,
        battery_capacity_mah_per_cell: int,
        cells_count: int,
        low_battery_threshold: int,
        entry_id: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry_id}",
            update_interval=timedelta(seconds=int(scan_interval)),
        )
        self._driver = driver
        self._battery_capacity_mah_per_cell = int(battery_capacity_mah_per_cell)
        self._cells_count = int(cells_count)
        self._low_battery_threshold = int(low_battery_threshold)
        self._entry_id = entry_id

    @property
    def driver(self) -> UpsHatDriver:
        return self._driver

    @property
    def total_capacity_mah(self) -> int:
        # 21700 / 18650 cells in this UPS are wired 2S2P -> nominal capacity
        # is `capacity_per_cell * (cells_count / 2)` because two parallel
        # strings double the capacity while two series cells just add voltage.
        # Default 4 cells -> ×2 capacity.
        if self._cells_count <= 0:
            return self._battery_capacity_mah_per_cell
        parallel = max(1, self._cells_count // 2)
        return self._battery_capacity_mah_per_cell * parallel

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.hass.async_add_executor_job(self._read_blocking)
        except Exception as err:  # noqa: BLE001 - surface as UpdateFailed
            raise UpdateFailed(f"UPS HAT (E) read failed: {err}") from err

    def _read_blocking(self) -> dict[str, Any]:
        drv = self._driver
        drv.open()

        charging = drv.read_charging_status()
        comm = drv.read_communication_state()
        vbus = drv.read_vbus()
        battery = drv.read_battery()
        cells = drv.read_cells()
        firmware = drv.read_firmware_revision()

        # Derive a friendly status. We bias charging/fast-charging toward the
        # bus state because some BQ4050 firmwares report `charge_state == full`
        # only after a calibration pass.
        if charging.fast_charging:
            status = STATE_FAST_CHARGING
        elif charging.charging:
            status = STATE_CHARGING
        elif CHARGE_STATE_NAMES.get(charging.charge_state) == "full":
            status = STATE_FULL
        elif battery.current_ma < 0:
            status = STATE_DISCHARGING
        else:
            status = STATE_IDLE

        battery_voltage_v = battery.voltage_mv / 1000.0
        battery_current_a = battery.current_ma / 1000.0
        battery_power_w = round(battery_voltage_v * battery_current_a, 2)

        remaining_capacity_wh = round(
            (battery.remaining_capacity_mah / 1000.0) * battery_voltage_v, 2
        )

        low_battery = battery.percent < self._low_battery_threshold

        # `runtime_min` only meaningful when discharging, `time_to_full_min`
        # only when charging — clamp the other to None for cleaner UI.
        runtime_min: int | None
        time_to_full_min: int | None
        if battery.current_ma < 0:
            runtime_min = battery.runtime_min if battery.runtime_min > 0 else None
            time_to_full_min = None
        elif battery.current_ma > 0:
            runtime_min = None
            time_to_full_min = (
                battery.time_to_full_min if battery.time_to_full_min > 0 else None
            )
        else:
            runtime_min = None
            time_to_full_min = None

        data: dict[str, Any] = {
            # USB-C input
            DATA_VBUS_VOLTAGE: round(vbus.voltage_mv / 1000.0, 3),
            DATA_VBUS_CURRENT: vbus.current_ma,  # mA
            DATA_VBUS_POWER: round(vbus.power_mw / 1000.0, 3),
            # Battery
            DATA_BATTERY_VOLTAGE: round(battery_voltage_v, 3),
            DATA_BATTERY_CURRENT: round(battery_current_a, 3),
            DATA_BATTERY_POWER: battery_power_w,
            DATA_BATTERY_PERCENT: max(0, min(100, int(battery.percent))),
            DATA_REMAINING_CAPACITY_MAH: int(battery.remaining_capacity_mah),
            DATA_REMAINING_CAPACITY_WH: remaining_capacity_wh,
            DATA_RUNTIME_MIN: runtime_min,
            DATA_TIME_TO_FULL_MIN: time_to_full_min,
            # Cells (V)
            DATA_CELL1_VOLTAGE: round(cells.cell1_mv / 1000.0, 3),
            DATA_CELL2_VOLTAGE: round(cells.cell2_mv / 1000.0, 3),
            DATA_CELL3_VOLTAGE: round(cells.cell3_mv / 1000.0, 3),
            DATA_CELL4_VOLTAGE: round(cells.cell4_mv / 1000.0, 3),
            # Status
            DATA_CHARGE_STATE: CHARGE_STATE_NAMES.get(
                charging.charge_state, "unknown"
            ),
            DATA_STATUS: status,
            DATA_ONLINE: charging.vbus_powered,
            DATA_CHARGING: charging.charging,
            DATA_FAST_CHARGING: charging.fast_charging,
            DATA_LOW_BATTERY: low_battery,
            DATA_BQ4050_OK: comm.bq4050_ok,
            DATA_IP2368_OK: comm.ip2368_ok,
            DATA_FIRMWARE_REVISION: f"0x{firmware:02X}",
        }
        return data
