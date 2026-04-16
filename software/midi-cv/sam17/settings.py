"""Global configuration for the SAM17 MIDI/CV firmware.

Values mirror the original thesis pinout and SPI settings unless explicitly
documented otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR: Path = Path(__file__).parent / "data"


@dataclass(frozen=True)
class GpioPins:
    """BCM GPIO numbering used on the Raspberry Pi 3B+."""

    button_back: int = 16
    button_enter: int = 26
    button_up: int = 4
    button_down: int = 17
    gate_out: int = 27
    dac_reset: int = 6
    lcd_rs: int = 25
    lcd_en: int = 24
    lcd_d4: int = 23
    lcd_d5: int = 18
    lcd_d6: int = 15
    lcd_d7: int = 14


@dataclass(frozen=True)
class SpiSettings:
    """SPI configuration for the AD5686R DAC."""

    bus: int = 0
    device: int = 1
    max_speed_hz: int = 50_000_000
    mode: int = 0b01


@dataclass(frozen=True)
class DacChannelMap:
    """AD5686R address bytes for the write-and-update command (0011 nnnn)."""

    vco1: int = 0x14  # DAC C
    vco2: int = 0x12  # DAC B
    vco3: int = 0x11  # DAC A
    aux: int = 0x18   # DAC D (unused, available for expansion)


@dataclass(frozen=True)
class MidiRange:
    """Notes considered playable by the synth (35 < note < 109 in the thesis)."""

    lowest: int = 36   # C2
    highest: int = 108  # C8


@dataclass(frozen=True)
class PitchBend:
    """Pitch-wheel scaling settings."""

    note_resolution: int = 460
    pitch_max: int = 8192
    pitch_min: int = -8192
    semitones: int = 2

    @property
    def per_step(self) -> int:
        return self.semitones * self.note_resolution


@dataclass(frozen=True)
class Settings:
    gpio: GpioPins = field(default_factory=GpioPins)
    spi: SpiSettings = field(default_factory=SpiSettings)
    channels: DacChannelMap = field(default_factory=DacChannelMap)
    midi_range: MidiRange = field(default_factory=MidiRange)
    pitch_bend: PitchBend = field(default_factory=PitchBend)
    notes_file: Path = DATA_DIR / "notes.json"
    tuning_file: Path = DATA_DIR / "tuning.json"


SETTINGS = Settings()

MODES: tuple[str, ...] = ("standard", "tune", "glide", "arp", "step_sequencer")
