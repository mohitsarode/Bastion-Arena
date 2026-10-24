"""Evidence finalization and audit manifest retrieval routes (API.md)."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict

from bastion_arena.api.middleware import get_security_context
from bastion_arena.core.errors import (
    BastionError,
    CapabilityDeniedError,
    LedgerVerifyError,
    TenantMismatchError,
)
from bastion_arena.core.schemas import AgentRole, RunPhase
from bastion_arena.ledger.manifest import EvidenceManifest, create_manifest
from bastion_arena.ledger.verifier import LedgerVerifier
from bastion_arena.security.policy import SecurityContext
from bastion_arena.storage.repositories import StorageRepository

router = APIRouter(tags=["Evidence"])


class FinalizeRoundResponse(BaseModel):
    """Evidence finalization receipt and signature confirmation."""

    model_config = ConfigDict(extra="forbid")

    round_id: str
    tenant_id: str
    phase: RunPhase
    total_events: int
    final_event_hash: str
    manifest_signature_b64: str


@router.post("/evidence/{round_id}/finalize", response_model=FinalizeRoundResponse)
async def finalize_evidence(
    round_id: str,
    request: Request,
    ctx: SecurityContext = Depends(get_security_context),
) -> FinalizeRoundResponse:
    """Close the round, verify cryptographic ledger integrity, and sign evidence manifest."""
    repo: StorageRepository = request.app.state.repository
    round_data = repo.get_round(round_id)
    if not round_data:
        raise BastionError(f"Round '{round_id}' does not exist", status_code=404)

    # Validate tenant ownership
    if round_data["tenant_id"] != ctx.tenant_id and ctx.role not in (
        AgentRole.ARBITER,
        AgentRole.AUDITOR,
    ):
        raise TenantMismatchError(f"Tenant '{ctx.tenant_id}' cannot finalize round '{round_id}'")

    # Advance state machine if orchestrator exists
    orchestrator = request.app.state.orchestrators.get(round_id)
    if orchestrator:
        if orchestrator.state_machine.current_phase == RunPhase.RUN:
            orchestrator.state_machine.transition_to(RunPhase.CLOSE)
            orchestrator.state_machine.transition_to(RunPhase.REVEAL)
            orchestrator.state_machine.transition_to(RunPhase.VERIFY)

    # 1. Fetch all ledger events
    events = repo.get_ledger_events()

    # 2. Cryptographic verification (ADR-005)
    verifier: LedgerVerifier = request.app.state.ledger_verifier
    res = verifier.verify_chain(events)
    if not res.valid:
        raise LedgerVerifyError(f"Audit ledger verification failed: {res.error_message}")

    # 3. Create signed manifest
    signing_key = request.app.state.signing_key
    manifest = create_manifest(
        round_id=round_id,
        tenant_id=round_data["tenant_id"],
        events=events,
        signing_key=signing_key,
    )

    # Update round status in database
    repo.update_round_state(
        round_id=round_id,
        state=RunPhase.VERIFY.value,
        closed_at=time.time(),
    )

    # Cache manifest
    request.app.state.manifests[round_id] = manifest

    return FinalizeRoundResponse(
        round_id=round_id,
        tenant_id=round_data["tenant_id"],
        phase=RunPhase.VERIFY,
        total_events=manifest.total_events,
        final_event_hash=manifest.final_event_hash,
        manifest_signature_b64=manifest.manifest_signature_b64,
    )


@router.get("/evidence/{round_id}/manifest", response_model=EvidenceManifest)
async def get_evidence_manifest(
    round_id: str,
    request: Request,
    ctx: SecurityContext = Depends(get_security_context),
) -> EvidenceManifest:
    """Retrieve the authorized public-safe signed manifest for an audited round."""
    manifest: EvidenceManifest | None = request.app.state.manifests.get(round_id)
    if not manifest:
        # Check if finalized in DB
        repo: StorageRepository = request.app.state.repository
        round_data = repo.get_round(round_id)
        if not round_data:
            raise BastionError(f"Round '{round_id}' does not exist", status_code=404)
        if round_data["tenant_id"] != ctx.tenant_id and ctx.role not in (
            AgentRole.ARBITER,
            AgentRole.AUDITOR,
        ):
            raise TenantMismatchError(
                f"Tenant '{ctx.tenant_id}' cannot view evidence for '{round_data['tenant_id']}'"
            )
        # Generate on-demand if round is closed/verified
        events = repo.get_ledger_events()
        manifest = create_manifest(
            round_id=round_id,
            tenant_id=round_data["tenant_id"],
            events=events,
            signing_key=request.app.state.signing_key,
        )
        request.app.state.manifests[round_id] = manifest

    # Check tenant access
    if manifest.tenant_id != ctx.tenant_id and ctx.role not in (
        AgentRole.ARBITER,
        AgentRole.AUDITOR,
    ):
        raise TenantMismatchError(
            f"Tenant '{ctx.tenant_id}' cannot view evidence for '{manifest.tenant_id}'"
        )

    return manifest


@router.get("/evidence/{round_id}/audit-trail")
async def get_audit_trail(
    round_id: str,
    request: Request,
    ctx: SecurityContext = Depends(get_security_context),
) -> dict:
    """Privileged forensic endpoint allowing auditors to view full ground-truth multi-agent logs."""
    if ctx.role not in (AgentRole.AUDITOR, AgentRole.ARBITER, AgentRole.SYSTEM):
        raise CapabilityDeniedError(
            f"Role '{ctx.role.value}' is not permitted to inspect internal audit trail"
        )

    repo: StorageRepository = request.app.state.repository
    round_data = repo.get_round(round_id)
    if not round_data:
        raise BastionError(f"Round '{round_id}' does not exist", status_code=404)

    events = repo.get_ledger_events()
    verifier: LedgerVerifier = request.app.state.ledger_verifier
    v_res = verifier.verify_chain(events)

    return {
        "round_id": round_id,
        "tenant_id": round_data["tenant_id"],
        "phase": round_data["state"],
        "total_events": len(events),
        "events": [ev.model_dump() for ev in events],
        "verification": {
            "valid": v_res.valid,
            "events_verified": v_res.events_verified,
            "error_message": v_res.error_message,
        },
    }
