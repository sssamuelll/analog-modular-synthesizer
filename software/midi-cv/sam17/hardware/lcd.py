"""LCD 16x2 abstraction.

Real hardware uses RPLCD over GPIO. Tests use `InMemoryLcd` which records the
last printed message.
"""

from __future__ import annotations

from typing import Protocol

from sam17.settings import GpioPins


class Lcd(Protocol):
    def print(self, message: str) -> None: ...
    def clear(self) -> None: ...


class InMemoryLcd:
    def __init__(self) -> None:
        self.last_message: str = ""

    def print(self, message: str) -> None:
        self.last_message = message

    def clear(self) -> None:
        self.last_message = ""


class RPLcd:
    """RPLCD-backed driver for the HD44780-compatible 16x2 LCD."""

    def __init__(self, pins: GpioPins, cols: int = 16, rows: int = 2) -> None:
        from RPLCD.gpio import CharLCD  # type: ignore[import-not-found]

        self._lcd = CharLCD(
            numbering_mode=11,  # BCM
            cols=cols,
            rows=rows,
            pin_rs=pins.lcd_rs,
            pin_e=pins.lcd_en,
            pins_data=[pins.lcd_d4, pins.lcd_d5, pins.lcd_d6, pins.lcd_d7],
        )

    def print(self, message: str) -> None:
        self._lcd.clear()
        self._lcd.write_string(message)

    def clear(self) -> None:
        self._lcd.clear()
