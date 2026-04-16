"""Driver for the AD5686R 16-bit quad DAC over SPI.

Trama de 24 bits:

    DB23..DB20  : command (C3..C0)
    DB19..DB16  : DAC address (A3..A0)
    DB15..DB0   : data word (0..65535)

The helper below assumes the caller passes an already-composed address byte
(command nibble + address nibble), which matches the constants exposed in
`sam17.settings.DacChannelMap` for the typical "write and update channel n"
command (0011).
"""

from __future__ import annotations

from typing import Protocol

DAC_RESOLUTION_BITS = 16
DAC_MAX_VALUE = (1 << DAC_RESOLUTION_BITS) - 1  # 65535


class SpiBus(Protocol):
    """Subset of `spidev.SpiDev` we actually need. Lets us mock in tests."""

    def writebytes(self, data: list[int]) -> None: ...
    def close(self) -> None: ...


class Dac:
    """Thin wrapper around an SPI bus that talks to the AD5686R."""

    def __init__(self, spi: SpiBus) -> None:
        self._spi = spi

    def send(self, address: int, value: int) -> None:
        """Send a single 24-bit write-and-update frame.

        Args:
            address: byte combining the 4-bit command nibble and the 4-bit
                channel-selection nibble (see `DacChannelMap`).
            value: 16-bit sample in the range 0..65535.

        Raises:
            ValueError: if `value` is out of range.
        """
        if not 0 <= value <= DAC_MAX_VALUE:
            raise ValueError(
                f"DAC value must be in 0..{DAC_MAX_VALUE}, got {value}"
            )
        msb = (value >> 8) & 0xFF
        lsb = value & 0xFF
        self._spi.writebytes([address & 0xFF, msb, lsb])

    def close(self) -> None:
        self._spi.close()


def open_spi_bus(bus: int, device: int, max_speed_hz: int, mode: int) -> SpiBus:
    """Open the kernel SPI device via `spidev`. Only callable on a Raspberry Pi."""
    import spidev  # type: ignore[import-not-found]

    spi = spidev.SpiDev()
    spi.open(bus, device)
    spi.max_speed_hz = max_speed_hz
    spi.mode = mode
    return spi
