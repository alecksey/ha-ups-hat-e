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
    DATA_RUNTIME_PRETTY,
    DATA_STATUS,
    DATA_TIME_TO_FULL_MIN,
    DATA_TIME_TO_FULL_PRETTY,
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


def format_duration_minutes(minutes):
    """Render a duration in minutes as a compact, dynamic human string.

    Output rules:
    - ``None``           -> ``None``
    - ``< 60 min``       -> ``"45m"``
    - ``< 24h``          -> ``"5h 30m"`` / ``"10h"``
    - ``>= 24h``         -> ``"2d"`` / ``"1d 1h 30m"`` / ``"1d 0h 1m"``

    Trailing zero parts are dropped, but a middle zero part is kept
    (e.g. ``1d 0h 1m``) to make the value unambiguous.
    """
    if minutes is None:
        return None
    try:
        total = int(minutes)
    except (TypeError, ValueError):
        return None
    if total < 0:
        total = 0
    if total < 60:
        return f"{total}m"

    days, rem = divmod(total, 1440)
    hours, mins = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or (days and mins):
        parts.append(f"{hours}h")
    if mins:
        parts.append(f"{mins}m")
    return " ".join(parts) if parts else "0m"


class UpsHatECoordinator(DataUpdateCoordinator):
    """Polls the UPS HAT (E) and exposes a normalized data dict."""

    def __init__(
        self,
        hass,
        *,
        driver,
        scan_interval,
        battery_capacity_mah_per_cell,
        cells_count,
        low_battery_threshold,
        entry_id,
    ):
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
    def driver(self):
        return self._driver

    @property
    def total_capacity_mah(self):
        if self._cells_count <= 0:
            return self._battery_capacity_mah_per_cell
        parallel = max(1, self._cells_count // 2)
        return self._battery_capacity_mah_per_cell * parallel

    async def _async_update_data(self):
        try:
            return await self.hass.async_add_executor_job(self._read_blocking)
        except Exception as err:
            raise UpdateFailed(f"UPS HAT (E) read failed: {err}") from err

    def _read_blocking(self):
        drv = self._driver
        drv.open()

        charging = drv.read_charging_status()
        comm = drv.read_communication_state()
        vbus = drv.read_vbus()
        battery = drv.read_battery()
        cells = drv.read_cells()
        firmware = drv.read_firmware_revision()

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

        return {
            DATA_VBUS_VOLTAGE: round(vbus.voltage_mv / 1000.0, 3),
            DATA_VBUS_CURRENT: vbus.current_ma,
            DATA_VBUS_POWER: round(vbus.power_mw / 1000.0, 3),
            DATA_BATTERY_VOLTAGE: round(battery_voltage_v, 3),
            DATA_BATTERY_CURRENT: round(battery_current_a, 3),
            DATA_BATTERY_POWER: battery_power_w,
            DATA_BATTERY_PERCENT: max(0, min(100, int(battery.percent))),
            DATA_REMAINING_CAPACITY_MAH: int(battery.remaining_capacity_mah),
            DATA_REMAINING_CAPACITY_WH: remaining_capacity_wh,
            DATA_RUNTIME_MIN: runtime_min,
            DATA_TIME_TO_FULL_MIN: time_to_full_min,
            DATA_RUNTIME_PRETTY: format_duration_minutes(runtime_min),
            DATA_TIME_TO_FULL_PRETTY: format_duration_minutes(time_to_full_min),
            DATA_CELL1_VOLTAGE: round(cells.cell1_mv / 1000.0, 3),
            DATA_CELL2_VOLTAGE: round(cells.cell2_mv / 1000.0, 3),
            DATA_CELL3_VOLTAGE: round(cells.cell3_mv / 1000.0, 3),
            DATA_CELL4_VOLTAGE: round(cells.cell4_mv / 1000.0, 3),
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
