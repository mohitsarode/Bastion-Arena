"""Round lifecycle and case submission routes (API.md)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field

from bastion_arena.api.middleware import get_security_context
from bastion_arena.core.errors import BastionError, TenantMismatchError
from bastion_arena.core.schemas import AgentRole, CaseInput, NormalizedResponse, RunPhase
from bastion_arena.core.state import RoundStateMachine
from bastion_arena.security.policy import SecurityContext
from bastion_arena.services.orchestrator import OrchestratorService
from bastion_arena.storage.repositories import StorageRepository

router = APIRouter(tags=["Rounds"])


class CreateRoundRequest(BaseModel):
    """Payload to initialize a new testing round."""

    model_config = ConfigDict(extra="forbid")

    round_id: str = Field(..., min_length=1, max_length=128)
    campaign_id: str = Field(..., min_length=1, max_length=128)
    max_cases: int = Field(default=100, ge=1, le=10000)
    ruleset_id: str = Field(default="ruleset-v1", max_length=64)


class CreateRoundResponse(BaseModel):
    """Confirmation payload returned on round initialization."""

    model_config = ConfigDict(extra="forbid")

    round_id: str
    campaign_id: str
    tenant_id: str
    phase: RunPhase
    max_cases: int


@router.post("/rounds", response_model=CreateRoundResponse, status_code=201)
async def create_round(
    body: CreateRoundRequest,
    request: Request,
    ctx: SecurityContext = Depends(get_security_context),
) -> CreateRoundResponse:
    """Initialize a new evaluation round under the caller's tenant."""
    repo: StorageRepository = request.app.state.repository

    # Ensure tenant and campaign exist
    repo.ensure_tenant(ctx.tenant_id)
    try:
        repo.create_campaign(body.campaign_id, ctx.tenant_id)
    except Exception:
        pass  # Campaign might already exist

    # Create round in repository
    repo.create_round(
        round_id=body.round_id,
        campaign_id=body.campaign_id,
        config_hash="sha256-synthetic-round-config",
        initial_state=RunPhase.COMMIT.value,
    )

    # Initialize state machine and advance to RUN phase for test execution
    sm = RoundStateMachine(initial_phase=RunPhase.COMMIT)
    sm.transition_to(RunPhase.SEAL)
    sm.transition_to(RunPhase.RUN)
    repo.update_round_state(body.round_id, RunPhase.RUN.value)

    # Build and cache orchestrator for this round
    orchestrator = OrchestratorService(
        round_id=body.round_id,
        state_machine=sm,
        blue_agent=request.app.state.blue_agent,
        model_provider=request.app.state.model_provider,
        evaluator_agent=request.app.state.evaluator_agent,
        ledger_chain=request.app.state.ledger_chain,
        repository=repo,
        budget_manager=request.app.state.budget_manager,
    )
    request.app.state.orchestrators[body.round_id] = orchestrator

    return CreateRoundResponse(
        round_id=body.round_id,
        campaign_id=body.campaign_id,
        tenant_id=ctx.tenant_id,
        phase=RunPhase.RUN,
        max_cases=body.max_cases,
    )


@router.post("/rounds/{round_id}/cases", response_model=NormalizedResponse)
async def submit_case(
    round_id: str,
    case: CaseInput,
    request: Request,
    ctx: SecurityContext = Depends(get_security_context),
) -> NormalizedResponse:
    """Submit a bounded adversarial test case through the Arbiter control plane."""
    orchestrator: OrchestratorService | None = request.app.state.orchestrators.get(round_id)
    if not orchestrator:
        # Check if round exists in database
        repo: StorageRepository = request.app.state.repository
        round_data = repo.get_round(round_id)
        if not round_data:
            raise BastionError(f"Round '{round_id}' does not exist", status_code=404)
        # Reconstruct orchestrator if needed
        sm = RoundStateMachine(initial_phase=RunPhase(round_data["state"]))
        orchestrator = OrchestratorService(
            round_id=round_id,
            state_machine=sm,
            blue_agent=request.app.state.blue_agent,
            model_provider=request.app.state.model_provider,
            evaluator_agent=request.app.state.evaluator_agent,
            ledger_chain=request.app.state.ledger_chain,
            repository=repo,
            budget_manager=request.app.state.budget_manager,
        )
        request.app.state.orchestrators[round_id] = orchestrator

    # Enforce tenant isolation
    repo: StorageRepository = request.app.state.repository
    round_data = repo.get_round(round_id)
    if round_data and round_data["tenant_id"] != ctx.tenant_id:
        raise TenantMismatchError(
            f"Authenticated tenant '{ctx.tenant_id}' cannot submit cases to round '{round_id}'"
        )

    # Execute timing-safe loop through Arbiter
    return await orchestrator.execute_case(case=case, ctx=ctx)


@router.get("/cases/{case_id}/result", response_model=NormalizedResponse)
async def get_case_result(
    case_id: str,
    request: Request,
    ctx: SecurityContext = Depends(get_security_context),
) -> NormalizedResponse:
    """Retrieve normalized test outcome scoped strictly by authenticated tenant."""
    repo: StorageRepository = request.app.state.repository
    case_data = repo.get_case(case_id)
    if not case_data:
        raise BastionError(f"Case '{case_id}' was not found", status_code=404)

    # Validate tenant ownership
    if case_data["tenant_id"] != ctx.tenant_id and ctx.role != AgentRole.ARBITER:
        raise TenantMismatchError(
            f"Case '{case_id}' does not belong to authenticated tenant '{ctx.tenant_id}'"
        )

    eval_data = repo.get_evaluation(case_id)
    if not eval_data:
        raise BastionError(f"Evaluation for case '{case_id}' is not yet available", status_code=404)

    return NormalizedResponse(
        case_id=case_id,
        status=case_data["status"],
        refusal_score=eval_data.refusal_score,
        bypass_score=eval_data.bypass_score,
        harm_score=eval_data.harm_score,
        latency_bucket_ms=500,
        evaluator_confidence=eval_data.confidence,
    )
