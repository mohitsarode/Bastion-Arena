"""Interactive Web Dashboard for Bastion Arena (Auditor Console & Visual Demo)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard"])

_TEMPLATE_PATH = Path(__file__).resolve().parents[4] / "dashboard.html"


@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard() -> HTMLResponse:
    """Serve interactive single-page auditor dashboard."""
    template_file = _TEMPLATE_PATH if _TEMPLATE_PATH.exists() else Path.cwd() / "dashboard.html"
    if template_file.exists():
        content = template_file.read_text(encoding="utf-8")
    else:
        content = "<h1>BASTION ARENA</h1><p>dashboard.html not found.</p>"
    return HTMLResponse(content=content)
