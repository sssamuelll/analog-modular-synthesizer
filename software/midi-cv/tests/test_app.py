from __future__ import annotations

from dataclasses import dataclass, replace

from sam17.app import App
from sam17.calibration import default_tunings
from sam17.hardware.dac import Dac
from sam17.settings import SETTINGS


@dataclass
class FakeMessage:
    type: str
    note: int = 0
    pitch: int = 0


class FakePort:
    """Puerto MIDI que entrega una cola y luego `None`, como `receive(block=False)`."""

    def __init__(self, messages=()):
        self.queue = list(messages)

    def receive(self, block: bool = True):
        return self.queue.pop(0) if self.queue else None


def _build(fake_spi, gpio, lcd, tmp_path, messages=()):
    settings = replace(SETTINGS, tuning_file=tmp_path / "tuning.json")
    return App(
        dac=Dac(fake_spi),
        gpio=gpio,
        lcd=lcd,
        tunings=default_tunings(settings.midi_range.lowest, settings.midi_range.highest),
        settings=settings,
        midi_port=FakePort(messages),
    )


def test_starts_in_standard_mode_with_gate_low(fake_spi, gpio, lcd, tmp_path):
    app = _build(fake_spi, gpio, lcd, tmp_path)
    assert app.mode.name == "standard"
    assert gpio.read(SETTINGS.gpio.gate_out) is False


def test_step_drains_the_port_and_dispatches(fake_spi, gpio, lcd, tmp_path):
    app = _build(fake_spi, gpio, lcd, tmp_path, [
        FakeMessage(type="note_on", note=60),
        FakeMessage(type="note_off", note=60),
    ])
    assert app.step() == 2
    assert app.step() == 0  # cola vacía
    assert fake_spi.writes, "note_on debería haber escrito al DAC"


def test_step_without_port_is_a_noop(fake_spi, gpio, lcd, tmp_path):
    app = _build(fake_spi, gpio, lcd, tmp_path)
    app.set_midi_port(None)
    assert app.step() == 0
    assert "No controller" in lcd.last_message


def test_menu_selection_enters_tune_mode(fake_spi, gpio, lcd, tmp_path):
    app = _build(fake_spi, gpio, lcd, tmp_path)
    app.press("enter")  # baja al submenú "Tune"
    app.press("enter")  # selecciona VCO1
    assert app.mode.name == "tune"


def test_back_returns_from_tune_to_standard(fake_spi, gpio, lcd, tmp_path):
    app = _build(fake_spi, gpio, lcd, tmp_path)
    app.select("tune:VCO1")
    app.press("back")
    assert app.mode.name == "standard"


def test_unimplemented_mode_is_refused_not_crashed(fake_spi, gpio, lcd, tmp_path):
    app = _build(fake_spi, gpio, lcd, tmp_path)
    app.select("mode:arp")
    assert app.mode.name == "standard"
    assert "not implemented" in lcd.last_message


def test_tune_mode_swallows_up_before_the_menu_sees_it(fake_spi, gpio, lcd, tmp_path):
    app = _build(fake_spi, gpio, lcd, tmp_path, [FakeMessage(type="note_on", note=60)])
    app.select("tune:VCO1")
    app.step()
    app.press("up")
    assert app.mode.name == "tune"  # el menú no navegó a otra rama


def test_run_stops_and_leaves_gate_low(fake_spi, gpio, lcd, tmp_path):
    app = _build(fake_spi, gpio, lcd, tmp_path, [FakeMessage(type="note_on", note=60)])
    app.step()
    assert gpio.read(SETTINGS.gpio.gate_out) is True
    app.stop()
    app.run()
    assert gpio.read(SETTINGS.gpio.gate_out) is False
