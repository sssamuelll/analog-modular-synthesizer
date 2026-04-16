"""USB MIDI controller discovery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class MidiInPort(Protocol):
    name: str

    def receive(self, block: bool = True) -> object | None: ...
    def close(self) -> None: ...


@dataclass(frozen=True)
class MidiController:
    """Connected MIDI controller. Empty `port` means no controller available."""

    name: str
    port: MidiInPort | None

    @property
    def is_connected(self) -> bool:
        return self.port is not None


def find_controller() -> MidiController:
    """Return the first non-default MIDI input port present on the system.

    Mirrors the original thesis logic (the first port is the system through-port,
    so we pick `puertos[1]`). Falls back to a disconnected controller if none
    is available, so the rest of the program can still boot.
    """
    import mido  # type: ignore[import-not-found]

    ports = mido.get_input_names()
    if len(ports) <= 1:
        return MidiController(name="(none)", port=None)
    name = ports[1]
    return MidiController(name=name.split(":", 1)[0], port=mido.open_input(name))
