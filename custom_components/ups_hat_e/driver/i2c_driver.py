"""Real I2C driver for the Waveshare UPS HAT (E) using smbus2."""

from __future__ import annotations

import logging
import threading
from typing import Optional

from ..const import (
    POWEROFF_MAGIC,
    REG_BATTERY_BLOCK,
    REG_CELL_BLOCK,
    REG_CHARGING_STATUS,
    REG_COMMUNICATION,
    REG_POWEROFF,
    REG_SOFTWARE_REVISION,
    REG_VBUS_BLOCK,
)
from .interface import (
    BatteryReading,
    CellVoltagesReading,
    ChargingStatusReading,
    CommunicationReading,
    UpsHatDriver,
    VbusReading,
)

_LOGGER = logging.getLogger(__name__)


class I2CUpsHatDriver(UpsHatDriver):
    """Driver that talks to the UPS HAT (E) over the Linux I2C bus."""

    def __init__(self, bus: int, address: int) -> None:
        self._bus_number = int(bus)
        self._address = int(address)
        self._bus = None  # type: Optional[object]
        self._lock = threading.Lock()

    # -- lifecycle --------------------------------------------------------

    def open(self) -> None:
        if self._bus is not None:
            return
        # Imported here so the integration can load on platforms without smbus2
        # (e.g. when only running mock mode in unit tests).
        from smbus2 import SMBus  # type: ignore

        _LOGGER.debug(
            "Opening I2C bus=%s for UPS HAT (E) at address 0x%02X",
            self._bus_number,
            self._address,
        )
        self._bus = SMBus(self._bus_number)

    def close(self) -> None:
        if self._bus is None:
            return
        try:
            self._bus.close()  # type: ignore[union-attr]
        except Exception:  # pragma: no cover - defensive
            _LOGGER.exception("Error closing I2C bus")
        finally:
            self._bus = None

    # -- low-level helpers -----------------------------------------------

    def _read_block(self, register: int, length: int) -> list[int]:
        if self._bus is None:
            self.open()
        with self._lock:
            data = self._bus.read_i2c_block_data(  # type: ignore[union-attr]
                self._address, register, length
            )
        if len(data) < length:
            raise OSError(
                f"Short read from UPS HAT (E) reg=0x{register:02X}: "
                f"{len(data)} of {length} bytes"
            )
        return list(data)

    def _read_byte(self, register: int) -> int:
        data = self._read_block(register, 1)
        return data[0] & 0xFF

    def _write_byte(self, register: int, value: int) -> None:
        if self._bus is None:
            self.open()
        with self._lock:
            self._bus.write_byte_data(  # type: ignore[union-attr]
                self._address, register, value & 0xFF
            )

    # -- public reads -----------------------------------------------------

    def read_charging_status(self) -> ChargingStatusReading:
        byte = self._read_byte(REG_CHARGING_STATUS)
        return ChargingStatusReading(
            raw=byte,
            charging=bool(byte & 0x80),
            fast_charging=bool(byte & 0x40),
            vbus_powered=bool(byte & 0x20),
            charge_state=byte & 0x07,
        )

    def read_communication_state(self) -> CommunicationReading:
        byte = self._read_byte(REG_COMMUNICATION)
        return CommunicationReading(
            raw=byte,
            ip2368_ok=bool(byte & 0x01),
            bq4050_ok=bool(byte & 0x02),
        )

    def read_vbus(self) -> VbusReading:
        d = self._read_block(REG_VBUS_BLOCK, 6)
        return VbusReading(
            voltage_mv=self._u16(d[0], d[1]),
            current_ma=self._u16(d[2], d[3]),
            power_mw=self._u16(d[4], d[5]),
        )

    def read_battery(self) -> BatteryReading:
        d = self._read_block(REG_BATTERY_BLOCK, 12)
        current = self._i16(d[2], d[3])
        return BatteryReading(
            voltage_mv=self._u16(d[0], d[1]),
            current_ma=current,
            percent=self._u16(d[4], d[5]),
            remaining_capacity_mah=self._u16(d[6], d[7]),
            runtime_min=self._u16(d[8], d[9]),
            time_to_full_min=self._u16(d[10], d[11]),
        )

    def read_cells(self) -> CellVoltagesReading:
        d = self._read_block(REG_CELL_BLOCK, 8)
        return CellVoltagesReading(
            cell1_mv=self._u16(d[0], d[1]),
            cell2_mv=self._u16(d[2], d[3]),
            cell3_mv=self._u16(d[4], d[5]),
            cell4_mv=self._u16(d[6], d[7]),
        )

    def read_firmware_revision(self) -> int:
        return self._read_byte(REG_SOFTWARE_REVISION)

    def shutdown(self) -> None:
        _LOGGER.warning("Sending shutdown command (0x55) to UPS HAT (E)")
        self._write_byte(REG_POWEROFF, POWEROFF_MAGIC)
