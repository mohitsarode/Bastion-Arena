"""Internal service endpoints for Blue, Evaluator, and Tool Gateway (API.md)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field

from bastion_arena.agents.blue.agent import BlueAgent
from bastion_arena.agents.evaluator.agent import EvaluatorAgent
from bastion_arena.api.middleware import get_security_context
from bastion_arena.core.errors import CapabilityDeniedError
from bastion_arena.core.schemas import AgentRole, EvaluationResult
from bastion_arena.security.policy import SecurityContext
from bastion_arena.tool_gateway.gateway import ToolGateway

router = APIRouter(prefix="/internal", tags=["Internal"])

# Internal roles authorized to invoke internal service endpoints
_AUTHORIZED_INTERNAL_ROLES = {
    AgentRole.BLUE,
    AgentRole.EVALUATOR,
    AgentRole.ARBITER,
    AgentRole.SYSTEM,
}


def _verify_internal_role(ctx: SecurityContext) -> None:
    """Enforce that untrusted roles (e.g. Red) cannot invoke internal endpoints."""
    if ctx.role not in _AUTHORIZED_INTERNAL_ROLES:
        raise CapabilityDeniedError(
            f"Role '{ctx.role.value}' is not authorized to invoke internal service endpoints"
        )


class PrecheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(..., max_length=12000)


class PrecheckResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blocked: bool
    reason: str | None
    matched_patterns: list[str]
    confidence: float


class PostcheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    output_text: str = Field(..., max_length=12000)


class PostcheckResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    redacted_text: str
    blocked: bool
    detected_canaries: list[str]


class EvaluatorScoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str = Field(..., max_length=128)
    prompt: str = Field(..., max_length=12000)
    response_text: str = Field(..., max_length=12000)


class ToolInvokeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str = Field(..., max_length=128)
    params: dict[str, Any] = Field(default_factory=dict)


@router.post("/blue/precheck", response_model=PrecheckResponse)
async def blue_precheck(
    body: PrecheckRequest,
    request: Request,
    ctx: SecurityContext = Depends(get_security_context),
) -> PrecheckResponse:
    """Run Blue pre-generation attack signature scans."""
    _verify_internal_role(ctx)
    blue: BlueAgent = request.app.state.blue_agent
    res = blue.check_input(body.prompt)
    return PrecheckResponse(
        blocked=res.blocked,
        reason=res.reason,
        matched_patterns=res.matched_patterns,
        confidence=res.confidence,
    )


@router.post("/blue/postcheck", response_model=PostcheckResponse)
async def blue_postcheck(
    body: PostcheckRequest,
    request: Request,
    ctx: SecurityContext = Depends(get_security_context),
) -> PostcheckResponse:
    """Run Blue post-generation canary and credential scrubbing."""
    _verify_internal_role(ctx)
    blue: BlueAgent = request.app.state.blue_agent
    res = blue.check_output(body.output_text)
    return PostcheckResponse(
        redacted_text=res.redacted_text,
        blocked=res.blocked,
        detected_canaries=res.detected_canaries,
    )


@router.post("/evaluator/score", response_model=EvaluationResult)
async def evaluator_score(
    body: EvaluatorScoreRequest,
    request: Request,
    ctx: SecurityContext = Depends(get_security_context),
) -> EvaluationResult:
    """Invoke the neutral evaluator to assess safety scores."""
    _verify_internal_role(ctx)
    evaluator: EvaluatorAgent = request.app.state.evaluator_agent
    return await evaluator.evaluate(
        case_id=body.case_id,
        prompt=body.prompt,
        response_text=body.response_text,
    )


@router.post("/tools/{tool_name}")
async def invoke_tool(
    tool_name: str,
    body: ToolInvokeRequest,
    request: Request,
    ctx: SecurityContext = Depends(get_security_context),
) -> dict[str, Any]:
    """Execute synthetic mock tools through the quota-controlled tool gateway."""
    _verify_internal_role(ctx)
    gateway: ToolGateway = request.app.state.tool_gateway
    return gateway.execute_tool(
        tool_name=tool_name,
        case_id=body.case_id,
        params=body.params,
    )
