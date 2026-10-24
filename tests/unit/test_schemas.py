"""Unit tests for Pydantic contracts, bounds, enums, and error serialization."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from bastion_arena.core.errors import (
    AuthError,
    BudgetExceededError,
    ErrorCode,
    ErrorEnvelope,
)
from bastion_arena.core.schemas import (
    CaseInput,
    EvaluationResult,
    NormalizedResponse,
    VerdictStatus,
)


def test_valid_case_input() -> None:
    case = CaseInput(
        case_id="case-100",
        iteration=0,
        prompt="Tell me how to make a paper airplane.",
        objective="test basic refusal",
        taxonomy_id="jailbreak",
    )
    assert case.case_id == "case-100"
    assert case.iteration == 0
    assert case.prompt == "Tell me how to make a paper airplane."


def test_case_input_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError) as exc:
        CaseInput.model_validate(
            {
                "case_id": "case-101",
                "prompt": "some prompt",
                "malicious_injected_field": "exploit",
            }
        )
    assert "extra_forbidden" in str(exc.value)


def test_case_input_bounds() -> None:
    with pytest.raises(ValidationError):
        CaseInput(case_id="case-102", iteration=-1, prompt="test")

    with pytest.raises(ValidationError):
        CaseInput(case_id="", prompt="test")


def test_normalized_response_contract() -> None:
    resp = NormalizedResponse(
        case_id="case-103",
        status=VerdictStatus.BLOCK,
        refusal_score=2,
        bypass_score=0,
        harm_score=1,
        latency_bucket_ms=250,
        evaluator_confidence=0.98,
    )
    assert resp.status == VerdictStatus.BLOCK
    assert resp.refusal_score == 2
    assert resp.evaluator_confidence == 0.98

    # Ensure forbidden extra fields
    with pytest.raises(ValidationError):
        NormalizedResponse.model_validate(
            {
                **resp.model_dump(),
                "raw_model_output": "LEAKED_SECRET",
            }
        )


def test_normalized_response_bounds() -> None:
    with pytest.raises(ValidationError):
        NormalizedResponse(
            case_id="case-104",
            status=VerdictStatus.PASS,
            refusal_score=3,  # le=2
            bypass_score=0,
            harm_score=0,
            latency_bucket_ms=250,
            evaluator_confidence=1.0,
        )

    with pytest.raises(ValidationError):
        NormalizedResponse(
            case_id="case-105",
            status=VerdictStatus.PASS,
            refusal_score=0,
            bypass_score=0,
            harm_score=0,
            latency_bucket_ms=250,
            evaluator_confidence=1.5,  # le=1.0
        )


def test_evaluation_result_schema() -> None:
    res = EvaluationResult(
        case_id="case-106",
        refusal_score=2,
        bypass_score=0,
        harm_score=0,
        confidence=0.92,
        category="jailbreak",
        rationale="Model safely refused dangerous instructions.",
    )
    assert res.refusal_score == 2
    assert res.rationale is not None


def test_error_envelope_and_domain_exceptions() -> None:
    err = BudgetExceededError(message="Tenant quota reached", request_id="req-999")
    envelope = err.to_envelope()

    assert isinstance(envelope, ErrorEnvelope)
    assert envelope.error.code == ErrorCode.BUDGET_EXCEEDED
    assert envelope.error.message == "Tenant quota reached"
    assert envelope.error.request_id == "req-999"


def test_auth_error_status_code() -> None:
    err = AuthError()
    assert err.code == ErrorCode.AUTH_FAILED
    assert err.status_code == 401
