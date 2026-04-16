from __future__ import annotations

from dataclasses import dataclass

from sam17.hardware.dac import Dac
from sam17.modes.standard import StandardMode, VcoTuning
from sam17.settings import DacChannelMap, MidiRange, PitchBend


@dataclass
class FakeMessage:
    type: str
    note: int = 0
    pitch: int = 0


def _build(fake_spi, gpio):
    dac = Dac(fake_spi)
    channels = DacChannelMap()
    tunings = {
        "VCO1": VcoTuning(name="VCO1", note_to_value={60: 30000, 72: 35000}),
        "VCO2": VcoTuning(name="VCO2", note_to_value={60: 30050, 72: 35050}),
        "VCO3": VcoTuning(name="VCO3", note_to_value={60: 30100}),
    }
    gate_pin = 27
    gpio.setup_output(gate_pin)
    mode = StandardMode(
        dac=dac,
        gpio=gpio,
        gate_pin=gate_pin,
        channels=channels,
        tunings=tunings,
        midi_range=MidiRange(),
        pitch_bend=PitchBend(),
    )
    return mode, channels, gate_pin


def test_note_on_sends_three_dac_writes_and_raises_gate(fake_spi, gpio):
    mode, channels, gate_pin = _build(fake_spi, gpio)
    mode.handle_message(FakeMessage(type="note_on", note=60))
    addresses = [w[0] for w in fake_spi.writes]
    assert addresses == [channels.vco1, channels.vco2, channels.vco3]
    assert gpio.read(gate_pin) is True


def test_note_off_drops_gate_when_no_notes_held(fake_spi, gpio):
    mode, _, gate_pin = _build(fake_spi, gpio)
    mode.handle_message(FakeMessage(type="note_on", note=60))
    mode.handle_message(FakeMessage(type="note_off", note=60))
    assert gpio.read(gate_pin) is False


def test_note_off_keeps_gate_when_other_notes_held(fake_spi, gpio):
    mode, _, gate_pin = _build(fake_spi, gpio)
    mode.handle_message(FakeMessage(type="note_on", note=60))
    mode.handle_message(FakeMessage(type="note_on", note=72))
    fake_spi.writes.clear()
    mode.handle_message(FakeMessage(type="note_off", note=72))
    assert gpio.read(gate_pin) is True
    assert any(w[1:] == [30000 >> 8, 30000 & 0xFF] for w in fake_spi.writes)


def test_out_of_range_notes_are_ignored(fake_spi, gpio):
    mode, _, gate_pin = _build(fake_spi, gpio)
    mode.handle_message(FakeMessage(type="note_on", note=10))
    assert fake_spi.writes == []
    assert gpio.read(gate_pin) is False


def test_pitchwheel_offsets_subsequent_writes(fake_spi, gpio):
    mode, _, _ = _build(fake_spi, gpio)
    mode.handle_message(FakeMessage(type="note_on", note=60))
    fake_spi.writes.clear()
    mode.handle_message(FakeMessage(type="pitchwheel", pitch=8192))
    assert fake_spi.writes, "pitchwheel should re-send the held note"
    expected_offset = PitchBend().per_step
    msb_lsb = fake_spi.writes[0][1:]
    sent = (msb_lsb[0] << 8) | msb_lsb[1]
    assert sent == 30000 + expected_offset
