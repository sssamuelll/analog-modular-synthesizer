"""Step sequencer mode.

Plays a programmed sequence of notes synchronized to the GATE output.
Stub for future implementation.
"""

from __future__ import annotations

from sam17.modes.base import Mode


class StepSequencerMode(Mode):
    name = "step_sequencer"

    def handle_message(self, message: object) -> None:
        raise NotImplementedError("StepSequencerMode is not implemented yet")
