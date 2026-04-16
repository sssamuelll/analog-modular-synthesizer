"""Portamento / glide mode.

Smoothly interpolates the DAC value from the previous note to the new one
over a configurable time. Stub for future implementation.
"""

from __future__ import annotations

from sam17.modes.base import Mode


class GlideMode(Mode):
    name = "glide"

    def handle_message(self, message: object) -> None:
        raise NotImplementedError("GlideMode is not implemented yet")
