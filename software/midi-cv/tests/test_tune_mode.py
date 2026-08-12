from __future__ import annotations

from dataclasses import dataclass

from sam17.calibration import default_tunings, load_tunings
from sam17.hardware.dac import Dac
from sam17.modes.tune import NUDGE_COUNTS, TuneMode
from sam17.settings import DacChannelMap, MidiRange

LOW, HIGH = 36, 108
GATE = 27


@dataclass
class FakeMessage:
    type: str
    note: int = 0


def _build(fake_spi, gpio, lcd, tmp_path, target="VCO2"):
    gpio.setup_output(GATE)
    tunings = default_tunings(LOW, HIGH)
    mode = TuneMode(
        dac=Dac(fake_spi),
        gpio=gpio,
        lcd=lcd,
        gate_pin=GATE,
        channels=DacChannelMap(),
        tunings=tunings,
        target_vco=target,
        midi_range=MidiRange(),
        tuning_file=tmp_path / "tuning.json",
        note_names={60: "C4"},
    )
    return mode, tunings


def test_note_on_sends_only_to_target_vco(fake_spi, gpio, lcd, tmp_path):
    mode, _ = _build(fake_spi, gpio, lcd, tmp_path)
    mode.handle_message(FakeMessage(type="note_on", note=60))
    assert [w[0] for w in fake_spi.writes] == [DacChannelMap().vco2]
    assert gpio.read(GATE) is True


def test_out_of_range_note_is_ignored(fake_spi, gpio, lcd, tmp_path):
    mode, _ = _build(fake_spi, gpio, lcd, tmp_path)
    mode.handle_message(FakeMessage(type="note_on", note=12))
    assert fake_spi.writes == []


def test_note_off_drops_gate(fake_spi, gpio, lcd, tmp_path):
    mode, _ = _build(fake_spi, gpio, lcd, tmp_path)
    mode.handle_message(FakeMessage(type="note_on", note=60))
    mode.handle_message(FakeMessage(type="note_off", note=60))
    assert gpio.read(GATE) is False


def test_up_and_down_adjust_the_note_under_test(fake_spi, gpio, lcd, tmp_path):
    mode, tunings = _build(fake_spi, gpio, lcd, tmp_path)
    original = tunings["VCO2"].note_to_value[60]
    mode.handle_message(FakeMessage(type="note_on", note=60))

    assert mode.handle_button("up") is True
    assert tunings["VCO2"].note_to_value[60] == original + NUDGE_COUNTS
    mode.handle_button("down")
    mode.handle_button("down")
    assert tunings["VCO2"].note_to_value[60] == original - NUDGE_COUNTS
    assert "C4" in lcd.last_message


def test_nudge_without_a_note_shows_the_prompt(fake_spi, gpio, lcd, tmp_path):
    mode, tunings = _build(fake_spi, gpio, lcd, tmp_path)
    mode.handle_button("up")
    assert tunings["VCO2"].note_to_value[60] == default_tunings(LOW, HIGH)["VCO2"].note_to_value[60]
    assert "Press C3" in lcd.last_message


def test_enter_persists_to_disk(fake_spi, gpio, lcd, tmp_path):
    mode, tunings = _build(fake_spi, gpio, lcd, tmp_path)
    mode.handle_message(FakeMessage(type="note_on", note=60))
    mode.handle_button("up")
    mode.handle_button("enter")

    saved = load_tunings(tmp_path / "tuning.json", LOW, HIGH)
    assert saved["VCO2"].note_to_value[60] == tunings["VCO2"].note_to_value[60]
    assert "Saved" in lcd.last_message


def test_exit_saves_pending_changes_and_drops_gate(fake_spi, gpio, lcd, tmp_path):
    mode, tunings = _build(fake_spi, gpio, lcd, tmp_path)
    mode.handle_message(FakeMessage(type="note_on", note=60))
    mode.handle_button("up")
    mode.on_exit()

    assert gpio.read(GATE) is False
    saved = load_tunings(tmp_path / "tuning.json", LOW, HIGH)
    assert saved["VCO2"].note_to_value[60] == tunings["VCO2"].note_to_value[60]


def test_back_is_not_consumed(fake_spi, gpio, lcd, tmp_path):
    mode, _ = _build(fake_spi, gpio, lcd, tmp_path)
    assert mode.handle_button("back") is False
