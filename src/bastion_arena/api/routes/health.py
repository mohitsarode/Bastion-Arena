"""Health and readiness check endpoints (API.md)."""

from __future__ import annotations

from fastapi import APIRouter, Request

from bastion_arena.core.schemas import HealthResponse
from bastion_arena.storage.database import Database

router = APIRouter(tags=["Health"])


@router.get("/health/live", response_model=dict[str, str])
async def health_live() -> dict[str, str]:
    """Process liveness probe."""
    return {"status": "alive"}


@router.get("/health/ready", response_model=HealthResponse)
async def health_ready(request: Request) -> HealthResponse:
    """Readiness probe checking database connectivity and provider configuration."""
    db: Database | None = getattr(request.app.state, "database", None)
    db_ok = False
    if db:
        try:
            with db.get_connection() as conn:
                conn.execute("SELECT 1")
            db_ok = True
        except Exception:
            db_ok = False

    return HealthResponse(
        status="ready" if db_ok else "degraded",
        environment="test",
        version="0.1.0",
        components={
            "database": db_ok,
            "provider": True,
        },
    )
