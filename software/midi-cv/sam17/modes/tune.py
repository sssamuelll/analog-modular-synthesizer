"""Modo de afinación interactiva.

Reproduce el *Modo de Afinación* de la tesis (páginas 54-55 del PDF): suena
como el modo estándar pero enruta el CV a un solo VCO y permite corregir, con
los botones UP/DOWN, el valor de DAC asociado a la nota que se está tocando.
ENTER persiste la corrección en ``tuning.json``.

Los textos de la guía son los del original (``settings.helptune_list``).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sam17.calibration import VcoTuning, save_tunings, volts_for_counts
from sam17.hardware.dac import Dac
from sam17.hardware.gpio import Gpio
from sam17.hardware.lcd import Lcd
from sam17.modes.base import Mode
from sam17.settings import DacChannelMap, MidiRange

HELP_STEPS: tuple[str, ...] = (
    "Select the \nVCO Channel",
    "Use an external\ntuner like ->",
    "Vocal Pitch  \nMonitor.     ->",
    "Press C3 on the\nController ->",
    "use the knobs \ntune in panel->",
    "press enter to\nstart",
    "use up or down \narrows to tune",
    "activate guide",
)
"""Guía paso a paso, recuperada literalmente de la tesis."""

NUDGE_COUNTS = 4
"""Paso de ajuste por pulsación. ~1 cent (460 cuentas/semitono ÷ 100).

Súbelo si afinar a oído resulta lento; bájalo si el VCO es muy sensible.
"""

REFERENCE_NOTE = 60
"""C3 en la nomenclatura de la tesis (C4 en la estándar). Nota de arranque."""


class TuneMode(Mode):
    """Afina un VCO nota por nota contra un afinador externo."""

    name = "tune"

    def __init__(
        self,
        dac: Dac,
        gpio: Gpio,
        lcd: Lcd,
        gate_pin: int,
        channels: DacChannelMap,
        tunings: dict[str, VcoTuning],
        target_vco: str,
        midi_range: MidiRange,
        tuning_file: Path,
        note_names: dict[int, str] | None = None,
        on_save: Callable[[], None] | None = None,
    ) -> None:
        self._dac = dac
        self._gpio = gpio
        self._lcd = lcd
        self._gate_pin = gate_pin
        self._channels = channels
        self._tunings = tunings
        self._target = target_vco
        self._range = midi_range
        self._tuning_file = tuning_file
        self._note_names = note_names or {}
        self._on_save = on_save
        self._note_under_test: int | None = None
        self._dirty = False

    # -- ciclo de vida -------------------------------------------------------

    def on_enter(self) -> None:
        self._lcd.print(f"Tune {self._target}\n{HELP_STEPS[3]}")

    def on_exit(self) -> None:
        self._gpio.write(self._gate_pin, False)
        if self._dirty:
            self.save()

    # -- MIDI ----------------------------------------------------------------

    def handle_message(self, message: object) -> None:
        msg_type = getattr(message, "type", None)
        if msg_type == "note_off":
            self._gpio.write(self._gate_pin, False)
            return
        if msg_type != "note_on":
            return
        note = int(getattr(message, "note", -1))
        if not self._range.lowest <= note <= self._range.highest:
            return
        self._note_under_test = note
        self._send(note)
        self._gpio.write(self._gate_pin, False)
        self._gpio.write(self._gate_pin, True)
        if note == REFERENCE_NOTE:
            self._lcd.print("Push enter when\nC3 gets in tune")
        else:
            self._render()

    # -- botones -------------------------------------------------------------

    def handle_button(self, name: str) -> bool:
        if name == "up":
            self._nudge(NUDGE_COUNTS)
        elif name == "down":
            self._nudge(-NUDGE_COUNTS)
        elif name == "enter":
            self.save()
        else:
            return False  # `back` sale del modo, lo maneja la app
        return True

    def _nudge(self, delta: int) -> None:
        note = self._note_under_test
        tuning = self._tunings.get(self._target)
        if note is None or tuning is None:
            self._lcd.print(HELP_STEPS[3])
            return
        if tuning.nudge(note, delta) is None:
            return
        self._dirty = True
        self._send(note)
        self._render()

    def save(self) -> None:
        save_tunings(self._tuning_file, self._tunings)
        self._dirty = False
        self._lcd.print(f"Saved {self._target}\nto tuning.json")
        if self._on_save is not None:
            self._on_save()

    # -- internos ------------------------------------------------------------

    def _send(self, note: int) -> None:
        tuning = self._tunings.get(self._target)
        address = self._address_for(self._target)
        if tuning is None or address is None:
            return
        value = tuning.value_for(note)
        if value is not None:
            self._dac.send(address, value)

    def _render(self) -> None:
        note = self._note_under_test
        tuning = self._tunings.get(self._target)
        if note is None or tuning is None:
            return
        value = tuning.value_for(note)
        if value is None:
            self._lcd.print(f"No tuning for\nnote {note}")
            return
        label = self._note_names.get(note, str(note))
        self._lcd.print(f"Tuning {label}\n{value} {volts_for_counts(value):.3f}V")

    def _address_for(self, vco_name: str) -> int | None:
        return {
            "VCO1": self._channels.vco1,
            "VCO2": self._channels.vco2,
            "VCO3": self._channels.vco3,
        }.get(vco_name)
