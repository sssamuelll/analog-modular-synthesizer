"""Curva CV 1 V/octava y persistencia de la afinación por VCO.

Datos recuperados de la tesis (Capítulo III, *Diseño del Software*, y
Capítulo IV, *Tabla 11*):

- ``settings.note_res = 460`` → cuentas del DAC por semitono. Como el diseño
  es de 1 V/octava, eso implica ``460 * 12 = 5520`` cuentas por voltio y un
  fondo de escala de ``65535 / 5520 ≈ 11.9 V``.
- El rango de notas habilitado es ``35 < note < 109`` (MIDI 36..108, 73 notas).
- La Tabla 11 midió la entrada de CV del VCO1 en 3.34 V para la nota más
  grave y 9.90 V para la más aguda (pendiente real medida: 1.0045 V/oct).

El original guardaba el diccionario nota→valor en ``afinacion.pickle``,
generado a mano con el modo de afinación. Ese archivo no viaja en el PDF, así
que aquí se reconstruye la **curva de diseño** (lineal, 1 V/oct) y el modo
`tune` la corrige contra la realidad del hardware.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# --- constantes recuperadas de la tesis -------------------------------------

COUNTS_PER_SEMITONE = 460
"""Cuentas del DAC por semitono (tesis: ``settings.note_res``)."""

COUNTS_PER_VOLT = COUNTS_PER_SEMITONE * 12
"""5520 cuentas/V, consecuencia directa del estándar 1 V/octava."""

BASE_VOLTS = 3.34
"""CV medido en la entrada del VCO1 para la nota más grave (Tabla 11)."""

DAC_MAX_VALUE = 65535

VCO_NAMES: tuple[str, ...] = ("VCO1", "VCO2", "VCO3")


@dataclass
class VcoTuning:
    """Mapa de nota MIDI (0..127) a valor de 16 bits del DAC."""

    name: str
    note_to_value: dict[int, int]

    def value_for(self, note: int) -> int | None:
        return self.note_to_value.get(note)

    def nudge(self, note: int, delta: int) -> int | None:
        """Ajusta la nota en ``delta`` cuentas y devuelve el valor resultante.

        Devuelve ``None`` si la nota no está en el mapa.
        """
        current = self.note_to_value.get(note)
        if current is None:
            return None
        new = max(0, min(DAC_MAX_VALUE, current + delta))
        self.note_to_value[note] = new
        return new


def counts_for_note(note: int, lowest: int) -> int:
    """Valor de DAC teórico para ``note`` según la curva de diseño 1 V/oct."""
    base = round(BASE_VOLTS * COUNTS_PER_VOLT)
    return min(DAC_MAX_VALUE, base + (note - lowest) * COUNTS_PER_SEMITONE)


def volts_for_counts(value: int) -> float:
    """Voltaje nominal en la salida CV para un valor del DAC."""
    return value / COUNTS_PER_VOLT


def default_tuning(name: str, lowest: int, highest: int) -> VcoTuning:
    """Curva de diseño para un VCO, sin corrección de hardware."""
    return VcoTuning(
        name=name,
        note_to_value={n: counts_for_note(n, lowest) for n in range(lowest, highest + 1)},
    )


def default_tunings(lowest: int, highest: int) -> dict[str, VcoTuning]:
    return {name: default_tuning(name, lowest, highest) for name in VCO_NAMES}


# --- persistencia -----------------------------------------------------------


def load_tunings(path: Path, lowest: int, highest: int) -> dict[str, VcoTuning]:
    """Lee ``tuning.json``; rellena con la curva de diseño lo que falte.

    El JSON tiene la forma ``{"VCO1": {"36": 18437, ...}, ...}``. Las claves
    que empiezan por ``_`` se ignoran (comentarios).
    """
    tunings = default_tunings(lowest, highest)
    if not path.exists():
        return tunings
    raw = json.loads(path.read_text(encoding="utf-8"))
    for vco, mapping in raw.items():
        if vco.startswith("_") or not isinstance(mapping, dict):
            continue
        target = tunings.setdefault(vco, VcoTuning(name=vco, note_to_value={}))
        target.note_to_value.update({int(n): int(v) for n, v in mapping.items()})
    return tunings


def save_tunings(path: Path, tunings: dict[str, VcoTuning]) -> None:
    """Escribe la afinación en JSON, ordenada por nota para diffs legibles."""
    payload: dict[str, object] = {
        "_comment": (
            "Afinación por VCO: nota MIDI → valor de 16 bits del DAC (0..65535). "
            "Base: curva de diseño 1 V/oct (460 cuentas/semitono). Corregir con "
            "`sam17-midicv --mode tune`."
        )
    }
    for name, tuning in tunings.items():
        payload[name] = {str(n): tuning.note_to_value[n] for n in sorted(tuning.note_to_value)}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
