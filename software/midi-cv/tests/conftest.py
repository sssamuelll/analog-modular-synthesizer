"""Test fixtures shared across the suite.

Tests are designed to run on any developer machine, so they never import
`RPi.GPIO`, `spidev` or `pyudev`. Anything that needs them is mocked.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from sam17.hardware.gpio import InMemoryGpio
from sam17.hardware.lcd import InMemoryLcd


class FakeSpiBus:
    def __init__(self) -> None:
        self.writes: list[list[int]] = []
        self.closed = False

    def writebytes(self, data: list[int]) -> None:
        self.writes.append(list(data))

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_spi() -> Iterator[FakeSpiBus]:
    yield FakeSpiBus()


@pytest.fixture
def gpio() -> Iterator[InMemoryGpio]:
    g = InMemoryGpio()
    try:
        yield g
    finally:
        g.cleanup()


@pytest.fixture
def lcd() -> Iterator[InMemoryLcd]:
    yield InMemoryLcd()
