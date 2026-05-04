"""In-memory mock driver for the UPS HAT (E)."""

from __future__ import annotations

import logging
import random

from .interface import (
    BatteryReading,
    CellVoltagesReading,
    ChargingStatusReading,
    CommunicationReading,
    UpsHatDriver,
    VbusReading,
)

_LOGGER = logging.getLogger(__name__)


class MockUpsHatDriver(UpsHatDriver):
    """Generates plausible UPS HAT (E) data for development on non-Pi hosts."""

    def __init__(self, bus: int = 1, address: int = 0x2D) -> None:
        self._bus_number = int(bus)
        self._address = int(address)
        self._tick = 0
        self._on_mains = True

    def open(self) -> None:
        _LOGGER.info(
            "Mock UPS HAT (E) driver started (bus=%s, addr=0x%02X)",
            self._bus_number,
            self._address,
        )

    def close(self) -> None:
        return None

    def _next_tick(self) -> int:
        self._tick += 1
        # Toggle simulated power loss every 30 reads
        if self._tick % 30 == 0:
            self._on_mains = not self._on_mains
        return self._tick

    def read_charging_status(self) -> ChargingStatusReading:
        self._next_tick()
        if self._on_mains:
            return ChargingStatusReading(
                raw=0xC2,
                charging=True,
                fast_charging=True,
                vbus_powered=True,
                charge_state=2,  # Constant Current
            )
        return ChargingStatusReading(
            raw=0x00, charging=False, fast_charging=False, vbus_powered=False, charge_state=0
        )

    def read_communication_state(self) -> CommunicationReading:
        return CommunicationReading(raw=0b11, ip2368_ok=True, bq4050_ok=True)

    def read_vbus(self) -> VbusReading:
        if self._on_mains:
            return VbusReading(
                voltage_mv=random.randint(4900, 5100),
                current_ma=random.randint(1500, 2500),
                power_mw=random.randint(7000, 12000),
            )
        return VbusReading(voltage_mv=0, current_ma=0, power_mw=0)

    def read_battery(self) -> BatteryReading:
        if self._on_mains:
            current = random.randint(500, 1500)  # charging
        else:
            current = -random.randint(500, 1500)  # discharging

        return BatteryReading(
            voltage_mv=random.randint(15600, 16400),
            current_ma=current,
            percent=random.randint(60, 90),
            remaining_capacity_mah=random.randint(3500, 4800),
            runtime_min=random.randint(30, 240),
            time_to_full_min=random.randint(20, 90),
        )

    def read_cells(self) -> CellVoltagesReading:
        base = random.randint(3900, 4100)
        return CellVoltagesReading(
            cell1_mv=base + random.randint(-30, 30),
            cell2_mv=base + random.randint(-30, 30),
            cell3_mv=base + random.randint(-30, 30),
            cell4_mv=base + random.randint(-30, 30),
        )

    def read_firmware_revision(self) -> int:
        return 0x10

    def shutdown(self) -> None:
        _LOGGER.warning("[MOCK] shutdown command issued")
