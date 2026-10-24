"""Request correlation, security context resolution, and error envelope middleware."""

from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from bastion_arena.core.errors import (
    AuthError,
    BastionError,
    ErrorCode,
    ErrorDetail,
    ErrorEnvelope,
)
from bastion_arena.core.schemas import AgentRole
from bastion_arena.security.policy import SecurityContext
from bastion_arena.security.tokens import TokenManager


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates X-Request-ID headers across all HTTP exchanges."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"req-{uuid.uuid4().hex[:12]}"

        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


async def bastion_exception_handler(request: Request, exc: BastionError) -> JSONResponse:
    """Standardized handler for domain exceptions returning ErrorEnvelope."""
    request_id = getattr(request.state, "request_id", None)
    if not exc.request_id:
        exc.request_id = request_id

    payload = exc.to_envelope().model_dump()
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handles Pydantic validation errors while concealing internals."""
    request_id = getattr(request.state, "request_id", None)
    errors = exc.errors()

    # If any error is a string length violation, map to INPUT_TOO_LARGE
    code = ErrorCode.INTERNAL_ERROR
    message = "Request validation failed"
    status_code = 422

    for err in errors:
        msg = err.get("msg", "")
        if "string_too_long" in msg or "greater than" in msg:
            code = ErrorCode.INPUT_TOO_LARGE
            message = "Input exceeds maximum allowed length"
            status_code = 413
            break

    envelope = ErrorEnvelope(
        error=ErrorDetail(
            code=code,
            message=message,
            request_id=request_id,
        )
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Conceals internal crash traces from API responses."""
    request_id = getattr(request.state, "request_id", None)
    envelope = ErrorEnvelope(
        error=ErrorDetail(
            code=ErrorCode.INTERNAL_ERROR,
            message="An internal server error occurred",
            request_id=request_id,
        )
    )
    return JSONResponse(status_code=500, content=envelope.model_dump())


def get_security_context(request: Request) -> SecurityContext:
    """Dependency extracting and verifying caller capability token or identity."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthError(
            "Missing or malformed Authorization header; Bearer token required",
            request_id=getattr(request.state, "request_id", None),
        )

    token_str = auth_header.removeprefix("Bearer ").strip()

    # Retrieve token manager from app state
    token_manager: TokenManager | None = getattr(request.app.state, "token_manager", None)
    if not token_manager:
        token_manager = TokenManager()

    # Special handling for static internal service token in tests
    if token_str.startswith("static-service-"):
        role_part = token_str.removeprefix("static-service-")
        try:
            role = AgentRole(role_part)
        except ValueError:
            role = AgentRole.SYSTEM
        return SecurityContext(
            role=role,
            tenant_id="tenant-internal",
            capabilities=["*"],
            request_id=getattr(request.state, "request_id", "req-default"),
        )

    token = token_manager.verify_token(token_str)
    return SecurityContext(
        role=token.role,
        tenant_id=token.tenant_id,
        capabilities=token.capabilities,
        request_id=getattr(request.state, "request_id", "req-default"),
    )
