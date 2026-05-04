"""I2C driver layer for the Waveshare UPS HAT (E)."""

from __future__ import annotations

from .interface import (
    BatteryReading,
    CellVoltagesReading,
    ChargingStatusReading,
    CommunicationReading,
    UpsHatDriver,
    VbusReading,
)

__all__ = [
    "BatteryReading",
    "CellVoltagesReading",
    "ChargingStatusReading",
    "CommunicationReading",
    "UpsHatDriver",
    "VbusReading",
    "create_driver",
]


def create_driver(bus: int, address: int, use_mock: bool = False) -> UpsHatDriver:
    """Build a real or mock driver depending on the environment."""
    if use_mock:
        from .mock_driver import MockUpsHatDriver

        return MockUpsHatDriver(bus=bus, address=address)

    from .i2c_driver import I2CUpsHatDriver

    return I2CUpsHatDriver(bus=bus, address=address)
