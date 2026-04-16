"""Button abstraction for the four-button menu."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sam17.hardware.gpio import Gpio
from sam17.settings import GpioPins

ButtonHandler = Callable[[], None]


@dataclass
class ButtonBindings:
    on_back: ButtonHandler
    on_enter: ButtonHandler
    on_up: ButtonHandler
    on_down: ButtonHandler


class Buttons:
    """Polled button driver. For interrupts, replace with `RPi.GPIO.add_event_detect`."""

    def __init__(self, gpio: Gpio, pins: GpioPins, bindings: ButtonBindings) -> None:
        self._gpio = gpio
        self._pins = pins
        self._bindings = bindings
        self._last: dict[int, bool] = {}
        for pin in (pins.button_back, pins.button_enter, pins.button_up, pins.button_down):
            gpio.setup_input(pin, pull_up=False)
            self._last[pin] = False

    def poll(self) -> None:
        """Call once per main-loop iteration. Triggers handlers on rising edges."""
        mapping = {
            self._pins.button_back: self._bindings.on_back,
            self._pins.button_enter: self._bindings.on_enter,
            self._pins.button_up: self._bindings.on_up,
            self._pins.button_down: self._bindings.on_down,
        }
        for pin, handler in mapping.items():
            now = self._gpio.read(pin)
            if now and not self._last[pin]:
                handler()
            self._last[pin] = now
