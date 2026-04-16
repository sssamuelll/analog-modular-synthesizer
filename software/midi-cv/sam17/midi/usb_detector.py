"""USB hot-plug detector.

Watches `/sys` events via `pyudev` and notifies the application when a USB
device is added or removed, so the MIDI controller can be re-discovered
without restarting the firmware.
"""

from __future__ import annotations

import threading
from collections.abc import Callable

UsbEventHandler = Callable[[str, str], None]


class UsbDetector:
    """Background thread that calls `on_event(action, device_node)`.

    `action` is one of `"add"` or `"remove"`. The thread is daemonic so it
    will not block process exit.
    """

    def __init__(self, on_event: UsbEventHandler) -> None:
        self._on_event = on_event
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _run(self) -> None:
        import pyudev  # type: ignore[import-not-found]

        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem="usb")
        monitor.start()
        for device in iter(monitor.poll, None):
            if device.action in {"add", "remove"}:
                self._on_event(device.action, device.device_node or "")
