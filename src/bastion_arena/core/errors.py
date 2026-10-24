"""Standard domain errors and API error envelope for Bastion Arena."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorCode(StrEnum):
    """Standard error codes defined in API.md."""

    AUTH_FAILED = "AUTH_FAILED"
    CAPABILITY_DENIED = "CAPABILITY_DENIED"
    TENANT_MISMATCH = "TENANT_MISMATCH"
    INVALID_PHASE = "INVALID_PHASE"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    INPUT_TOO_LARGE = "INPUT_TOO_LARGE"
    MODEL_TIMEOUT = "MODEL_TIMEOUT"
    EVALUATOR_INVALID_OUTPUT = "EVALUATOR_INVALID_OUTPUT"
    LEDGER_WRITE_FAILED = "LEDGER_WRITE_FAILED"
    LEDGER_VERIFY_FAILED = "LEDGER_VERIFY_FAILED"
    ROUND_CLOSED = "ROUND_CLOSED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    """Inner error payload for the standard API error envelope."""

    model_config = ConfigDict(extra="forbid")

    code: ErrorCode
    message: str = Field(..., max_length=1000)
    request_id: str | None = Field(default=None, max_length=128)
    details: dict[str, Any] | None = None


class ErrorEnvelope(BaseModel):
    """Standard API error response wrapper defined in API.md."""

    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail


class BastionError(Exception):
    """Base class for all Bastion Arena domain exceptions."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.request_id = request_id
        self.details = details

    def to_envelope(self) -> ErrorEnvelope:
        return ErrorEnvelope(
            error=ErrorDetail(
                code=self.code,
                message=self.message,
                request_id=self.request_id,
                details=self.details,
            )
        )


class AuthError(BastionError):
    def __init__(
        self, message: str = "Authentication failed", request_id: str | None = None
    ) -> None:
        super().__init__(
            message, code=ErrorCode.AUTH_FAILED, status_code=401, request_id=request_id
        )


class CapabilityDeniedError(BastionError):
    def __init__(
        self,
        message: str = "Required capability token missing or denied",
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message, code=ErrorCode.CAPABILITY_DENIED, status_code=403, request_id=request_id
        )


class TenantMismatchError(BastionError):
    def __init__(
        self,
        message: str = "Resource does not belong to the authenticated tenant",
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message, code=ErrorCode.TENANT_MISMATCH, status_code=403, request_id=request_id
        )


class InvalidPhaseError(BastionError):
    def __init__(
        self,
        message: str = "Operation not allowed in current round phase",
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message, code=ErrorCode.INVALID_PHASE, status_code=409, request_id=request_id
        )


class ReplayDetectedError(BastionError):
    def __init__(
        self,
        message: str = "Case ID or token nonce replay detected",
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message, code=ErrorCode.REPLAY_DETECTED, status_code=409, request_id=request_id
        )


class BudgetExceededError(BastionError):
    def __init__(
        self, message: str = "Case budget exhausted", request_id: str | None = None
    ) -> None:
        super().__init__(
            message, code=ErrorCode.BUDGET_EXCEEDED, status_code=429, request_id=request_id
        )


class InputTooLargeError(BastionError):
    def __init__(
        self,
        message: str = "Payload exceeds maximum allowable bounds",
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message, code=ErrorCode.INPUT_TOO_LARGE, status_code=413, request_id=request_id
        )


class ModelTimeoutError(BastionError):
    def __init__(
        self, message: str = "Model invocation timed out", request_id: str | None = None
    ) -> None:
        super().__init__(
            message, code=ErrorCode.MODEL_TIMEOUT, status_code=504, request_id=request_id
        )


class EvaluatorInvalidOutputError(BastionError):
    def __init__(
        self,
        message: str = "Evaluator produced invalid or malformed output",
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message, code=ErrorCode.EVALUATOR_INVALID_OUTPUT, status_code=502, request_id=request_id
        )


class LedgerWriteError(BastionError):
    def __init__(
        self,
        message: str = "Failed to write event to append-only ledger",
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message, code=ErrorCode.LEDGER_WRITE_FAILED, status_code=500, request_id=request_id
        )


class LedgerVerifyError(BastionError):
    def __init__(
        self,
        message: str = "Ledger verification failed; tampering or corruption detected",
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message, code=ErrorCode.LEDGER_VERIFY_FAILED, status_code=500, request_id=request_id
        )


class RoundClosedError(BastionError):
    def __init__(
        self,
        message: str = "Round is closed; new cases cannot be accepted",
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message, code=ErrorCode.ROUND_CLOSED, status_code=409, request_id=request_id
        )


class InternalError(BastionError):
    def __init__(
        self, message: str = "Internal server error", request_id: str | None = None
    ) -> None:
        super().__init__(
            message, code=ErrorCode.INTERNAL_ERROR, status_code=500, request_id=request_id
        )
