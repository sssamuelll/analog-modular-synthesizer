"""Minimal GPIO abstraction.

Provides a small protocol so the rest of the code doesn't import `RPi.GPIO`
directly. In tests, swap in `InMemoryGpio`.
"""

from __future__ import annotations

from typing import Protocol


class Gpio(Protocol):
    def setup_input(self, pin: int, pull_up: bool = False) -> None: ...
    def setup_output(self, pin: int, initial_high: bool = False) -> None: ...
    def read(self, pin: int) -> bool: ...
    def write(self, pin: int, high: bool) -> None: ...
    def cleanup(self) -> None: ...


class InMemoryGpio:
    """Deterministic in-memory GPIO used by tests and dry-runs."""

    def __init__(self) -> None:
        self._pins: dict[int, bool] = {}

    def setup_input(self, pin: int, pull_up: bool = False) -> None:
        self._pins[pin] = pull_up

    def setup_output(self, pin: int, initial_high: bool = False) -> None:
        self._pins[pin] = initial_high

    def read(self, pin: int) -> bool:
        return self._pins.get(pin, False)

    def write(self, pin: int, high: bool) -> None:
        self._pins[pin] = high

    def cleanup(self) -> None:
        self._pins.clear()


class RPiGpio:
    """Real-hardware GPIO. Instantiate only on the Raspberry Pi."""

    def __init__(self) -> None:
        import RPi.GPIO as GPIO  # type: ignore[import-not-found]

        self._gpio = GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

    def setup_input(self, pin: int, pull_up: bool = False) -> None:
        pud = self._gpio.PUD_UP if pull_up else self._gpio.PUD_DOWN
        self._gpio.setup(pin, self._gpio.IN, pull_up_down=pud)

    def setup_output(self, pin: int, initial_high: bool = False) -> None:
        self._gpio.setup(
            pin,
            self._gpio.OUT,
            initial=self._gpio.HIGH if initial_high else self._gpio.LOW,
        )

    def read(self, pin: int) -> bool:
        return bool(self._gpio.input(pin))

    def write(self, pin: int, high: bool) -> None:
        self._gpio.output(pin, self._gpio.HIGH if high else self._gpio.LOW)

    def cleanup(self) -> None:
        self._gpio.cleanup()
