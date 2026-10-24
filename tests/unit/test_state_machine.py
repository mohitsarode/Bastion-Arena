"""Unit tests for round state transitions and lifecycle validation."""

from __future__ import annotations

import pytest

from bastion_arena.core.errors import InvalidPhaseError, RoundClosedError
from bastion_arena.core.schemas import RunPhase
from bastion_arena.core.state import RoundStateMachine


def test_state_machine_valid_progression() -> None:
    sm = RoundStateMachine(RunPhase.COMMIT)
    assert sm.current_phase == RunPhase.COMMIT

    assert sm.transition_to(RunPhase.SEAL) == RunPhase.SEAL
    assert sm.transition_to(RunPhase.RUN) == RunPhase.RUN
    assert sm.transition_to(RunPhase.CLOSE) == RunPhase.CLOSE
    assert sm.transition_to(RunPhase.REVEAL) == RunPhase.REVEAL
    assert sm.transition_to(RunPhase.VERIFY) == RunPhase.VERIFY
    assert sm.current_phase == RunPhase.VERIFY


def test_state_machine_invalid_skipping() -> None:
    sm = RoundStateMachine(RunPhase.COMMIT)

    # Attempting to jump directly from COMMIT to RUN without SEAL must fail
    with pytest.raises(InvalidPhaseError):
        sm.transition_to(RunPhase.RUN)


def test_state_machine_terminal_state() -> None:
    sm = RoundStateMachine(RunPhase.VERIFY)

    with pytest.raises(RoundClosedError):
        sm.transition_to(RunPhase.COMMIT)


def test_assert_phase_check() -> None:
    sm = RoundStateMachine(RunPhase.RUN)
    sm.assert_phase(RunPhase.RUN)

    with pytest.raises(InvalidPhaseError):
        sm.assert_phase(RunPhase.CLOSE)
