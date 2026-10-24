"""Per-tenant concurrency, case limit, and token budget governance."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from bastion_arena.core.errors import BudgetExceededError


@dataclass
class TenantBudget:
    """Tracks resource consumption and limits for a single tenant."""

    max_cases: int = 25
    cases_consumed: int = 0
    max_concurrent: int = 2
    active_cases: int = 0
    token_budget: int = 100000
    tokens_consumed: int = 0


class BudgetManager:
    """Thread-safe and async-safe budget and concurrency governor."""

    def __init__(
        self,
        default_max_cases: int = 25,
        default_max_concurrent: int = 2,
    ) -> None:
        self.default_max_cases = default_max_cases
        self.default_max_concurrent = default_max_concurrent
        self._budgets: dict[str, TenantBudget] = {}
        self._lock = asyncio.Lock()

    def _get_tenant_budget(self, tenant_id: str) -> TenantBudget:
        if tenant_id not in self._budgets:
            self._budgets[tenant_id] = TenantBudget(
                max_cases=self.default_max_cases,
                max_concurrent=self.default_max_concurrent,
            )
        return self._budgets[tenant_id]

    async def reserve_case_slot(self, tenant_id: str) -> None:
        """Reserve a case slot under the tenant's case and concurrency budget."""
        async with self._lock:
            b = self._get_tenant_budget(tenant_id)
            if b.cases_consumed >= b.max_cases:
                raise BudgetExceededError(
                    f"Case budget exhausted for tenant '{tenant_id}' "
                    f"({b.cases_consumed}/{b.max_cases})"
                )
            if b.active_cases >= b.max_concurrent:
                raise BudgetExceededError(
                    f"Concurrency limit reached for tenant '{tenant_id}' "
                    f"({b.active_cases}/{b.max_concurrent})"
                )

            b.cases_consumed += 1
            b.active_cases += 1

    async def release_case_slot(self, tenant_id: str, tokens_used: int = 0) -> None:
        """Release concurrency slot and record token consumption."""
        async with self._lock:
            b = self._get_tenant_budget(tenant_id)
            b.active_cases = max(0, b.active_cases - 1)
            b.tokens_consumed += tokens_used

    def get_remaining_budget(self, tenant_id: str) -> dict[str, int]:
        b = self._get_tenant_budget(tenant_id)
        return {
            "remaining_cases": max(0, b.max_cases - b.cases_consumed),
            "cases_consumed": b.cases_consumed,
            "max_cases": b.max_cases,
            "active_concurrency": b.active_cases,
            "max_concurrency": b.max_concurrent,
        }
