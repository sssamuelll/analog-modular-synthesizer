from __future__ import annotations

import json

from sam17.calibration import (
    COUNTS_PER_SEMITONE,
    DAC_MAX_VALUE,
    default_tunings,
    load_tunings,
    save_tunings,
    volts_for_counts,
)

LOW, HIGH = 36, 108


def test_design_curve_is_one_volt_per_octave():
    tuning = default_tunings(LOW, HIGH)["VCO1"]
    low = tuning.note_to_value[LOW]
    octave_up = tuning.note_to_value[LOW + 12]
    assert volts_for_counts(octave_up) - volts_for_counts(low) == 1.0


def test_design_curve_covers_the_thesis_note_range():
    tuning = default_tunings(LOW, HIGH)["VCO1"]
    assert set(tuning.note_to_value) == set(range(LOW, HIGH + 1))
    assert all(0 <= v <= DAC_MAX_VALUE for v in tuning.note_to_value.values())


def test_semitone_step_matches_thesis_note_res():
    tuning = default_tunings(LOW, HIGH)["VCO1"]
    assert tuning.note_to_value[60] - tuning.note_to_value[59] == COUNTS_PER_SEMITONE


def test_nudge_clamps_and_reports():
    tuning = default_tunings(LOW, HIGH)["VCO1"]
    before = tuning.note_to_value[60]
    assert tuning.nudge(60, 10) == before + 10
    assert tuning.nudge(0, 10) is None  # nota fuera del mapa
    tuning.note_to_value[60] = DAC_MAX_VALUE
    assert tuning.nudge(60, 10) == DAC_MAX_VALUE


def test_save_then_load_roundtrips(tmp_path):
    path = tmp_path / "tuning.json"
    tunings = default_tunings(LOW, HIGH)
    tunings["VCO2"].note_to_value[60] = 12345
    save_tunings(path, tunings)

    reloaded = load_tunings(path, LOW, HIGH)
    assert reloaded["VCO2"].note_to_value[60] == 12345
    assert reloaded["VCO1"].note_to_value == tunings["VCO1"].note_to_value


def test_load_ignores_comments_and_fills_missing_notes(tmp_path):
    path = tmp_path / "tuning.json"
    path.write_text(json.dumps({"_comment": "hola", "VCO1": {"60": 999}}), encoding="utf-8")

    tunings = load_tunings(path, LOW, HIGH)
    assert "_comment" not in tunings
    assert tunings["VCO1"].note_to_value[60] == 999
    # el resto de las notas cae de vuelta en la curva de diseño
    assert tunings["VCO1"].note_to_value[61] == default_tunings(LOW, HIGH)["VCO1"].note_to_value[61]


def test_load_without_file_returns_design_curve(tmp_path):
    tunings = load_tunings(tmp_path / "missing.json", LOW, HIGH)
    assert tunings["VCO3"].note_to_value == default_tunings(LOW, HIGH)["VCO3"].note_to_value
