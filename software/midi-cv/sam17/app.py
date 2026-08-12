"""Bucle principal y cableado de la aplicación.

La tesis (páginas 51-55) describe un ``while True`` que consulta el puerto MIDI
sin bloquear, identifica el tipo de mensaje y despacha según el modo activo,
mientras cuatro botones con interrupción navegan el menú del LCD. Ese bucle
nunca aparece completo en el PDF; aquí se reconstruye con la misma semántica
pero con el estado explícito en vez de globales.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Protocol

from sam17.calibration import VcoTuning
from sam17.hardware.buttons import ButtonBindings, Buttons
from sam17.hardware.dac import Dac
from sam17.hardware.gpio import Gpio
from sam17.hardware.lcd import Lcd
from sam17.modes.base import Mode
from sam17.modes.standard import StandardMode
from sam17.modes.tune import TuneMode
from sam17.settings import Settings
from sam17.ui.menu import Menu

log = logging.getLogger("sam17.app")

MAX_MESSAGES_PER_STEP = 32
"""Tope de mensajes MIDI drenados por iteración, para no matar de hambre a los
botones si el controlador vomita eventos."""

IMPLEMENTED_MODES: frozenset[str] = frozenset({"standard", "tune"})
"""La tesis declara cinco modos pero sólo dejó dos escritos."""


class MidiPort(Protocol):
    def receive(self, block: bool = True) -> object | None: ...


class App:
    """Estado del firmware: modo activo, menú, afinación y periféricos."""

    def __init__(
        self,
        dac: Dac,
        gpio: Gpio,
        lcd: Lcd,
        tunings: dict[str, VcoTuning],
        settings: Settings,
        note_names: dict[int, str] | None = None,
        midi_port: MidiPort | None = None,
        menu: Menu | None = None,
        poll_interval: float = 0.001,
    ) -> None:
        self._dac = dac
        self._gpio = gpio
        self._lcd = lcd
        self._tunings = tunings
        self._settings = settings
        self._note_names = note_names or {}
        self._midi_port = midi_port
        self._poll_interval = poll_interval
        self._stop = False

        gpio.setup_output(settings.gpio.gate_out, initial_high=False)
        self._buttons = Buttons(
            gpio,
            settings.gpio,
            ButtonBindings(
                on_back=lambda: self.press("back"),
                on_enter=lambda: self.press("enter"),
                on_up=lambda: self.press("up"),
                on_down=lambda: self.press("down"),
            ),
        )
        self._menu = menu if menu is not None else Menu(lcd)
        self._mode: Mode = self._build_standard()
        self._mode.on_enter()

    # -- construcción de modos ----------------------------------------------

    def _build_standard(self) -> StandardMode:
        return StandardMode(
            dac=self._dac,
            gpio=self._gpio,
            gate_pin=self._settings.gpio.gate_out,
            channels=self._settings.channels,
            tunings=self._tunings,
            midi_range=self._settings.midi_range,
            pitch_bend=self._settings.pitch_bend,
        )

    def _build_tune(self, target_vco: str) -> TuneMode:
        return TuneMode(
            dac=self._dac,
            gpio=self._gpio,
            lcd=self._lcd,
            gate_pin=self._settings.gpio.gate_out,
            channels=self._settings.channels,
            tunings=self._tunings,
            target_vco=target_vco,
            midi_range=self._settings.midi_range,
            tuning_file=self._settings.tuning_file,
            note_names=self._note_names,
        )

    @property
    def mode(self) -> Mode:
        return self._mode

    def _switch(self, mode: Mode) -> None:
        self._mode.on_exit()
        self._mode = mode
        self._mode.on_enter()

    def select(self, action: str) -> None:
        """Ejecuta una acción del menú (`mode:x`, `tune:VCOn`, `help:x`)."""
        kind, _, value = action.partition(":")
        if kind == "tune":
            self._switch(self._build_tune(value))
        elif kind == "mode" and value == "standard":
            self._switch(self._build_standard())
        elif kind == "mode" and value == "tune":
            self._switch(self._build_tune("VCO1"))
        elif kind == "mode" and value not in IMPLEMENTED_MODES:
            self._lcd.print(f"{value}\nnot implemented")
        elif kind == "help":
            self._lcd.print(f"{value}\nsee docs/")
        else:
            log.warning("Unknown menu action: %s", action)

    # -- entrada -------------------------------------------------------------

    def press(self, name: str) -> None:
        """Botón pulsado. El modo activo tiene prioridad sobre el menú."""
        if name == "back" and self._mode.name != "standard":
            self._switch(self._build_standard())
            self._menu.refresh()
            return
        if self._mode.handle_button(name):
            return
        if name == "up":
            self._menu.up()
        elif name == "down":
            self._menu.down()
        elif name == "back":
            self._menu.back()
        elif name == "enter":
            leaf = self._menu.enter()
            if leaf is not None and leaf.action:
                self.select(leaf.action)

    def set_midi_port(self, port: MidiPort | None, name: str = "") -> None:
        """Conecta o desconecta el controlador (llamado por el watcher USB)."""
        self._midi_port = port
        self._lcd.print(f"MIDI: {name}" if port is not None else "No controller\nconnected")

    # -- bucle ---------------------------------------------------------------

    def step(self) -> int:
        """Una iteración: botones + mensajes MIDI. Devuelve cuántos despachó."""
        self._buttons.poll()
        if self._midi_port is None:
            return 0
        handled = 0
        while handled < MAX_MESSAGES_PER_STEP:
            msg = self._midi_port.receive(block=False)
            if msg is None:
                break
            self._mode.handle_message(msg)
            handled += 1
        return handled

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        # `_stop` no se resetea aquí: un `stop()` previo (o desde otro hilo, como
        # el watcher USB) tiene que poder cortar el bucle antes de que arranque.
        try:
            while not self._stop:
                if self.step() == 0:
                    time.sleep(self._poll_interval)
        finally:
            self._mode.on_exit()
            self._gpio.write(self._settings.gpio.gate_out, False)


def load_note_names(path: Path) -> dict[int, str]:
    """Lee ``notes.json`` (nota MIDI → nombre), ignorando claves ``_comment``."""
    import json

    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {int(k): str(v) for k, v in raw.items() if not k.startswith("_")}
