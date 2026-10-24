"""Round state lifecycle machine and transition validation."""

from __future__ import annotations

from typing import ClassVar

from bastion_arena.core.errors import InvalidPhaseError, RoundClosedError
from bastion_arena.core.schemas import RunPhase


class RoundStateMachine:
    """Explicit, deterministic state machine governing round lifecycles."""

    # Valid transitions: Current phase -> Set of permissible next phases
    ALLOWED_TRANSITIONS: ClassVar[dict[RunPhase, set[RunPhase]]] = {
        RunPhase.COMMIT: {RunPhase.SEAL},
        RunPhase.SEAL: {RunPhase.RUN},
        RunPhase.RUN: {RunPhase.CLOSE},
        RunPhase.CLOSE: {RunPhase.REVEAL},
        RunPhase.REVEAL: {RunPhase.VERIFY},
        RunPhase.VERIFY: set(),  # Terminal state
    }

    def __init__(self, initial_phase: RunPhase = RunPhase.COMMIT) -> None:
        self._current_phase = initial_phase

    @property
    def current_phase(self) -> RunPhase:
        return self._current_phase

    def transition_to(self, target_phase: RunPhase) -> RunPhase:
        """Advance phase if transition is valid, else raise InvalidPhaseError."""
        if self._current_phase == RunPhase.VERIFY:
            raise RoundClosedError(
                f"Cannot transition from terminal phase '{self._current_phase.value}'"
            )

        allowed = self.ALLOWED_TRANSITIONS.get(self._current_phase, set())
        if target_phase not in allowed:
            raise InvalidPhaseError(
                f"Invalid phase transition: '{self._current_phase.value}' -> "
                f"'{target_phase.value}'. Permitted: {[p.value for p in allowed]}"
            )

        self._current_phase = target_phase
        return self._current_phase

    def assert_phase(self, expected_phase: RunPhase) -> None:
        """Assert current phase matches expected_phase, raising InvalidPhaseError otherwise."""
        if self._current_phase != expected_phase:
            raise InvalidPhaseError(
                f"Action requires phase '{expected_phase.value}', but round is in "
                f"'{self._current_phase.value}'"
            )
