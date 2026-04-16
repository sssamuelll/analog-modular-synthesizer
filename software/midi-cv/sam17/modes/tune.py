"""Interactive tuning mode.

Lets the user step through MIDI notes on the connected controller and
fine-tune the DAC value associated with each note for a chosen VCO. The
adjusted values are persisted back to ``tuning.json`` so the calibration
survives reboots.

This is a skeleton that mirrors the behaviour of the original thesis;
the full UI (LCD prompts, save dialog) and external tuner integration are
left as `# TODO` markers for future work.
"""

from __future__ import annotations

from sam17.hardware.dac import Dac
from sam17.hardware.lcd import Lcd
from sam17.modes.base import Mode
from sam17.modes.standard import VcoTuning
from sam17.settings import DacChannelMap


class TuneMode(Mode):
    name = "tune"

    def __init__(
        self,
        dac: Dac,
        lcd: Lcd,
        channels: DacChannelMap,
        tuning: VcoTuning,
        target_vco: str,
    ) -> None:
        self._dac = dac
        self._lcd = lcd
        self._channels = channels
        self._tuning = tuning
        self._target = target_vco
        self._note_under_test: int | None = None

    def on_enter(self) -> None:
        self._lcd.print(f"Tune {self._target}\nPress C3 (note 60)")

    def handle_message(self, message: object) -> None:
        msg_type = getattr(message, "type", None)
        if msg_type != "note_on":
            return
        note = int(message.note)  # type: ignore[attr-defined]
        self._note_under_test = note
        value = self._tuning.note_to_value.get(note)
        if value is None:
            self._lcd.print(f"No tuning for {note}")
            return
        address = self._address_for(self._target)
        if address is None:
            return
        self._dac.send(address, value)
        self._lcd.print(f"Tuning note {note}\nValue {value}")

    def _address_for(self, vco_name: str) -> int | None:
        return {
            "VCO1": self._channels.vco1,
            "VCO2": self._channels.vco2,
            "VCO3": self._channels.vco3,
        }.get(vco_name)

    # TODO: handle UP/DOWN button events to nudge the value, and ENTER to save.
