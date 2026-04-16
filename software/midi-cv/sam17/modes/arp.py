"""Arpeggiator mode.

Cycles through the currently held notes at a configurable rate. Stub for
future implementation.
"""

from __future__ import annotations

from sam17.modes.base import Mode


class ArpMode(Mode):
    name = "arp"

    def handle_message(self, message: object) -> None:
        raise NotImplementedError("ArpMode is not implemented yet")
