"""Base interface for execution modes."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Mode(ABC):
    """A mode receives MIDI messages and translates them into DAC + GPIO state."""

    name: str = "base"

    @abstractmethod
    def handle_message(self, message: object) -> None:
        """Process a single MIDI message (a `mido.Message` at runtime)."""

    def on_enter(self) -> None:  # noqa: B027 — empty hook by design
        """Hook called when the mode becomes active."""

    def on_exit(self) -> None:  # noqa: B027 — empty hook by design
        """Hook called when leaving the mode."""
