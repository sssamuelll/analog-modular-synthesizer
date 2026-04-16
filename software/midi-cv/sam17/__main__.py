"""Entry point for the MIDI/CV firmware."""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

from sam17.modes.standard import VcoTuning
from sam17.settings import MODES, SETTINGS

log = logging.getLogger("sam17")


def load_tunings(path: Path) -> dict[str, VcoTuning]:
    """Load per-VCO note→DAC mappings from JSON.

    The JSON shape is `{ "VCO1": { "60": 12345, ... }, "VCO2": {...}, ... }`.
    """
    if not path.exists():
        log.warning("Tuning file %s not found, using empty tunings", path)
        return {}
    raw = json.loads(path.read_text())
    return {
        vco: VcoTuning(name=vco, note_to_value={int(n): int(v) for n, v in mapping.items()})
        for vco, mapping in raw.items()
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SAM17 MIDI/CV firmware")
    parser.add_argument("--mode", choices=MODES, default="standard")
    parser.add_argument("--vco", choices=("VCO1", "VCO2", "VCO3"), default="VCO1",
                        help="Target VCO when --mode=tune")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without touching real hardware (uses in-memory stubs)")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    tunings = load_tunings(SETTINGS.tuning_file)
    log.info("Loaded tunings for: %s", ", ".join(tunings) or "(none)")

    if args.dry_run:
        log.info("Dry-run mode: no GPIO/SPI/MIDI access. Configured mode=%s vco=%s",
                 args.mode, args.vco)
        return 0

    # The actual wiring (open SPI, GPIO, MIDI port, build the selected mode and
    # dispatch a poll loop) is intentionally left out of this skeleton until the
    # hardware is on the bench. See `tests/` for the contracts each component must
    # satisfy.
    log.error("Hardware bring-up not implemented yet. Run with --dry-run for now.")
    time.sleep(0)  # placeholder to keep import-time side-effects minimal
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
