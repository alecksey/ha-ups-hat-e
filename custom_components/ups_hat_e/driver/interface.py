"""Abstract interface and data classes for the UPS HAT (E) driver."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ChargingStatusReading:
    """Decoded byte from register 0x02."""

    raw: int
    charging: bool  # bit 7
    fast_charging: bool  # bit 6
    vbus_powered: bool  # bit 5
    charge_state: int  # bits 0..2 (0..6)


@dataclass(frozen=True)
class CommunicationReading:
    """Decoded byte from register 0x03."""

    raw: int
    ip2368_ok: bool  # bit 0
    bq4050_ok: bool  # bit 1


@dataclass(frozen=True)
class VbusReading:
    """USB-C input bus values from register block 0x10 (6 bytes)."""

    voltage_mv: int
    current_ma: int
    power_mw: int


@dataclass(frozen=True)
class BatteryReading:
    """Battery values from register block 0x20 (12 bytes).

    `current_ma` is signed: positive => charging, negative => discharging.
    """

    voltage_mv: int
    current_ma: int  # signed
    percent: int
    remaining_capacity_mah: int
    runtime_min: int  # valid while discharging
    time_to_full_min: int  # valid while charging


@dataclass(frozen=True)
class CellVoltagesReading:
    """Per-cell voltages from register block 0x30 (8 bytes)."""

    cell1_mv: int
    cell2_mv: int
    cell3_mv: int
    cell4_mv: int


class UpsHatDriver(ABC):
    """Abstract driver interface for the Waveshare UPS HAT (E)."""

    @abstractmethod
    def open(self) -> None:
        """Open the I2C bus / prepare resources."""

    @abstractmethod
    def close(self) -> None:
        """Close the I2C bus and release resources."""

    @abstractmethod
    def read_charging_status(self) -> ChargingStatusReading:
        """Read register 0x02."""

    @abstractmethod
    def read_communication_state(self) -> CommunicationReading:
        """Read register 0x03."""

    @abstractmethod
    def read_vbus(self) -> VbusReading:
        """Read register block 0x10 (6 bytes)."""

    @abstractmethod
    def read_battery(self) -> BatteryReading:
        """Read register block 0x20 (12 bytes)."""

    @abstractmethod
    def read_cells(self) -> CellVoltagesReading:
        """Read register block 0x30 (8 bytes)."""

    @abstractmethod
    def read_firmware_revision(self) -> int:
        """Read register 0x50."""

    @abstractmethod
    def shutdown(self) -> None:
        """Initiate UPS-side shutdown sequence (write 0x55 to reg 0x01)."""

    # ----- helpers -------------------------------------------------------

    @staticmethod
    def _u16(low: int, high: int) -> int:
        return (low & 0xFF) | ((high & 0xFF) << 8)

    @staticmethod
    def _i16(low: int, high: int) -> int:
        value = (low & 0xFF) | ((high & 0xFF) << 8)
        if value & 0x8000:
            value -= 0x10000
        return value
