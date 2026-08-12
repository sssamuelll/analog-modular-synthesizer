"""Entry point for the MIDI/CV firmware."""

from __future__ import annotations

import argparse
import logging

from sam17.app import App, load_note_names
from sam17.calibration import default_tunings, load_tunings, save_tunings
from sam17.hardware.dac import Dac, open_spi_bus
from sam17.hardware.gpio import Gpio, InMemoryGpio, RPiGpio
from sam17.hardware.lcd import InMemoryLcd, Lcd, RPLcd
from sam17.settings import MODES, SETTINGS

log = logging.getLogger("sam17")


class NullSpi:
    """SPI de mentira para `--dry-run`: registra las tramas y no toca hardware."""

    def __init__(self) -> None:
        self.writes: list[list[int]] = []

    def writebytes(self, data: list[int]) -> None:
        self.writes.append(list(data))

    def close(self) -> None:
        pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SAM17 MIDI/CV firmware")
    parser.add_argument("--mode", choices=MODES, default="standard")
    parser.add_argument("--vco", choices=("VCO1", "VCO2", "VCO3"), default="VCO1",
                        help="Target VCO when --mode=tune")
    parser.add_argument("--dry-run", action="store_true",
                        help="Wire everything with in-memory stubs and exit (smoke test)")
    parser.add_argument("--generate-tuning", action="store_true",
                        help="Write the 1 V/oct design curve to tuning.json and exit")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


def build_app(*, dry_run: bool) -> App:
    gpio: Gpio
    lcd: Lcd
    if dry_run:
        gpio, lcd, spi = InMemoryGpio(), InMemoryLcd(), NullSpi()
    else:
        gpio, lcd = RPiGpio(), RPLcd(SETTINGS.gpio)
        spi = open_spi_bus(  # type: ignore[assignment]
            SETTINGS.spi.bus, SETTINGS.spi.device,
            SETTINGS.spi.max_speed_hz, SETTINGS.spi.mode,
        )
    tunings = load_tunings(SETTINGS.tuning_file, SETTINGS.midi_range.lowest,
                           SETTINGS.midi_range.highest)
    return App(
        dac=Dac(spi),
        gpio=gpio,
        lcd=lcd,
        tunings=tunings,
        settings=SETTINGS,
        note_names=load_note_names(SETTINGS.notes_file),
    )


def attach_midi(app: App) -> None:
    """Busca el controlador y arranca el watcher de hot-plug USB."""
    from sam17.midi.controller import find_controller
    from sam17.midi.usb_detector import UsbDetector

    def reconnect(action: str, _node: str) -> None:
        controller = find_controller()
        app.set_midi_port(controller.port, controller.name)
        log.info("USB %s → controller: %s", action, controller.name)

    controller = find_controller()
    app.set_midi_port(controller.port, controller.name)
    UsbDetector(reconnect).start()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    if args.generate_tuning:
        tunings = default_tunings(SETTINGS.midi_range.lowest, SETTINGS.midi_range.highest)
        save_tunings(SETTINGS.tuning_file, tunings)
        log.info("Wrote design curve for %s to %s", ", ".join(tunings), SETTINGS.tuning_file)
        return 0

    app = build_app(dry_run=args.dry_run)
    if args.mode == "tune":
        app.select(f"tune:{args.vco}")
    else:
        app.select(f"mode:{args.mode}")

    if args.dry_run:
        app.step()
        log.info("Dry-run OK: wiring built, mode=%s vco=%s", app.mode.name, args.vco)
        return 0

    attach_midi(app)
    try:
        app.run()
    except KeyboardInterrupt:
        log.info("Stopped by user")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
