"""Zero-trust attribute-based access control and capability policy enforcement."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from bastion_arena.core.errors import (
    AuthError,
    CapabilityDeniedError,
    InvalidPhaseError,
    TenantMismatchError,
)
from bastion_arena.core.schemas import AgentRole, RunPhase


class SecurityContext(BaseModel):
    """Authenticated and trusted security context attached to each request."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(..., max_length=128)
    role: AgentRole
    capabilities: list[str] = Field(default_factory=list)
    request_id: str = Field(default="req-default", max_length=128)


class SecurityPolicyEngine:
    """In-process zero-trust authorization engine executing ABAC rules (ADR-006)."""

    @staticmethod
    def authorize_action(
        ctx: SecurityContext,
        action: str,
        current_phase: RunPhase,
        resource_tenant_id: str | None = None,
    ) -> None:
        """Enforce role, tenant boundary, capability, and phase invariants."""
        # 1. Tenant boundary enforcement: cross-tenant access is strictly denied
        if resource_tenant_id and resource_tenant_id != ctx.tenant_id:
            raise TenantMismatchError(
                f"Tenant '{ctx.tenant_id}' cannot access resource for '{resource_tenant_id}'"
            )

        # 2. Phase and role authorization matrix
        if action == "case:submit":
            if ctx.role != AgentRole.RED:
                raise AuthError(f"Only '{AgentRole.RED.value}' may submit test cases")
            if current_phase != RunPhase.RUN:
                raise InvalidPhaseError(
                    f"Test cases require '{RunPhase.RUN.value}', currently '{current_phase.value}'"
                )

        elif action == "defense:submit":
            if ctx.role != AgentRole.BLUE:
                raise AuthError(f"Only '{AgentRole.BLUE.value}' may submit defense packs")
            if current_phase != RunPhase.COMMIT:
                raise InvalidPhaseError(
                    f"Defenses can only be submitted in '{RunPhase.COMMIT.value}' phase"
                )

        elif action == "round:close":
            if ctx.role not in (AgentRole.ARBITER, AgentRole.SYSTEM):
                raise AuthError("Only platform arbiter or system may close rounds")
            if current_phase != RunPhase.RUN:
                raise InvalidPhaseError("Only running rounds may be closed")

        elif action == "evidence:read":
            if ctx.role not in (AgentRole.AUDITOR, AgentRole.ARBITER, AgentRole.SYSTEM):
                # Red and Blue can only read public views after reveal
                if current_phase not in (RunPhase.REVEAL, RunPhase.VERIFY):
                    raise InvalidPhaseError(
                        "Detailed evidence can only be inspected after round reveal"
                    )

        # 3. Capability token check if specific capability required
        required_cap = f"{ctx.role.value}:{action}"
        if (
            ctx.capabilities
            and required_cap not in ctx.capabilities
            and action not in ctx.capabilities
            and "*" not in ctx.capabilities
        ):
            raise CapabilityDeniedError(f"Missing required capability '{required_cap}'")
