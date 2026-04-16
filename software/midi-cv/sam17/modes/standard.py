"""Standard monophonic MIDI-to-CV conversion with pitch-bend."""

from __future__ import annotations

from dataclasses import dataclass

from sam17.hardware.dac import Dac
from sam17.hardware.gpio import Gpio
from sam17.modes.base import Mode
from sam17.settings import DacChannelMap, MidiRange, PitchBend


@dataclass
class VcoTuning:
    """Per-VCO mapping from MIDI note (0..127) to 16-bit DAC value."""

    name: str
    note_to_value: dict[int, int]


class StandardMode(Mode):
    """Maps every received `note_on` to the DAC and raises GATE.

    Multi-note press/release is handled with a small LIFO (last-note priority,
    with up to eight nested presses like in the original thesis).
    """

    name = "standard"

    def __init__(
        self,
        dac: Dac,
        gpio: Gpio,
        gate_pin: int,
        channels: DacChannelMap,
        tunings: dict[str, VcoTuning],
        midi_range: MidiRange,
        pitch_bend: PitchBend,
    ) -> None:
        self._dac = dac
        self._gpio = gpio
        self._gate_pin = gate_pin
        self._channels = channels
        self._tunings = tunings
        self._range = midi_range
        self._pitch = pitch_bend
        self._pitchbend_offset: int = 0
        self._held_notes: list[int] = []

    def handle_message(self, message: object) -> None:
        msg_type = getattr(message, "type", None)
        if msg_type == "note_on":
            self._on_note(int(message.note), pressed=True)  # type: ignore[attr-defined]
        elif msg_type == "note_off":
            self._on_note(int(message.note), pressed=False)  # type: ignore[attr-defined]
        elif msg_type == "pitchwheel":
            self._on_pitch(int(message.pitch))  # type: ignore[attr-defined]

    def _on_note(self, note: int, *, pressed: bool) -> None:
        if not self._range.lowest <= note <= self._range.highest:
            return
        if pressed:
            if note not in self._held_notes:
                self._held_notes.append(note)
            self._send_note(note)
            self._gpio.write(self._gate_pin, True)
        else:
            if note in self._held_notes:
                self._held_notes.remove(note)
            if self._held_notes:
                self._send_note(self._held_notes[-1])
            else:
                self._gpio.write(self._gate_pin, False)

    def _on_pitch(self, raw: int) -> None:
        self._pitchbend_offset = int(self._pitch.per_step * raw / self._pitch.pitch_max)
        if self._held_notes:
            self._send_note(self._held_notes[-1])

    def _send_note(self, note: int) -> None:
        for address, tuning in self._iter_channels():
            value = tuning.note_to_value.get(note)
            if value is None:
                continue
            adjusted = max(0, min(65535, value + self._pitchbend_offset))
            self._dac.send(address, adjusted)

    def _iter_channels(self) -> list[tuple[int, VcoTuning]]:
        out: list[tuple[int, VcoTuning]] = []
        for key, address in (
            ("VCO1", self._channels.vco1),
            ("VCO2", self._channels.vco2),
            ("VCO3", self._channels.vco3),
        ):
            tuning = self._tunings.get(key)
            if tuning is not None:
                out.append((address, tuning))
        return out
