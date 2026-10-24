"""Unit tests for tenant case count, token budgets, and concurrency limits."""

from __future__ import annotations

import asyncio

import pytest

from bastion_arena.core.budgets import BudgetManager
from bastion_arena.core.errors import BudgetExceededError


def test_budget_reservation_and_exhaustion() -> None:
    async def _run() -> None:
        mgr = BudgetManager(default_max_cases=3, default_max_concurrent=5)

        # First 3 reservations succeed
        await mgr.reserve_case_slot("tenant-1")
        await mgr.reserve_case_slot("tenant-1")
        await mgr.reserve_case_slot("tenant-1")

        # 4th reservation must exceed case budget
        with pytest.raises(BudgetExceededError) as exc:
            await mgr.reserve_case_slot("tenant-1")
        assert "Case budget exhausted" in str(exc.value)

    asyncio.run(_run())


def test_concurrency_limit_and_release() -> None:
    async def _run() -> None:
        mgr = BudgetManager(default_max_cases=10, default_max_concurrent=2)

        await mgr.reserve_case_slot("tenant-2")
        await mgr.reserve_case_slot("tenant-2")

        # 3rd concurrent request exceeds limit
        with pytest.raises(BudgetExceededError) as exc:
            await mgr.reserve_case_slot("tenant-2")
        assert "Concurrency limit reached" in str(exc.value)

        # Release one slot
        await mgr.release_case_slot("tenant-2", tokens_used=150)

        # Now reservation succeeds
        await mgr.reserve_case_slot("tenant-2")
        rem = mgr.get_remaining_budget("tenant-2")
        assert rem["active_concurrency"] == 2
        assert rem["cases_consumed"] == 3

    asyncio.run(_run())
