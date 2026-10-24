"""FastAPI application entry point for Bastion Arena (API.md, ARCHITECTURE.md)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from nacl.signing import SigningKey

from bastion_arena.agents.blue.agent import BlueAgent
from bastion_arena.agents.evaluator.agent import EvaluatorAgent
from bastion_arena.api.middleware import (
    RequestCorrelationMiddleware,
    bastion_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from bastion_arena.api.routes import dashboard, evidence, health, internal, rounds
from bastion_arena.core.budgets import BudgetManager
from bastion_arena.core.config import Settings, load_config
from bastion_arena.core.errors import BastionError
from bastion_arena.ledger.chain import LedgerChain
from bastion_arena.ledger.verifier import LedgerVerifier
from bastion_arena.providers.factory import build_provider
from bastion_arena.providers.fake import FakeProvider
from bastion_arena.security.tokens import TokenManager
from bastion_arena.storage.database import Database
from bastion_arena.storage.repositories import StorageRepository
from bastion_arena.tool_gateway.gateway import ToolGateway


def create_app(
    config: Settings | None = None,
    db: Database | None = None,
    signing_key: SigningKey | None = None,
) -> FastAPI:
    """Application factory configuring routes, state, and zero-trust security boundaries."""
    app_config = config or load_config()

    app = FastAPI(
        title="Bastion Arena",
        description="Zero-Trust Adversarial AI Safety Evaluation Framework",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 1. State initialization
    database = db or Database(":memory:")
    repo = StorageRepository(database)
    sk = signing_key or SigningKey.generate()
    vk = sk.verify_key
    ledger_chain = LedgerChain(signing_key=sk)
    ledger_verifier = LedgerVerifier(verify_key=vk)

    blue_agent = BlueAgent()
    model_provider = build_provider(app_config)
    evaluator_agent = EvaluatorAgent(provider=FakeProvider())
    budget_manager = BudgetManager(
        default_max_cases=app_config.arena.max_cases_per_round,
        default_max_concurrent=app_config.arena.max_concurrent_cases_per_tenant,
    )
    token_manager = TokenManager()
    tool_gateway = ToolGateway()

    app.state.config = app_config
    app.state.database = database
    app.state.repository = repo
    app.state.signing_key = sk
    app.state.ledger_chain = ledger_chain
    app.state.ledger_verifier = ledger_verifier
    app.state.blue_agent = blue_agent
    app.state.model_provider = model_provider
    app.state.evaluator_agent = evaluator_agent
    app.state.budget_manager = budget_manager
    app.state.token_manager = token_manager
    app.state.tool_gateway = tool_gateway
    app.state.orchestrators = {}
    app.state.manifests = {}
    app.state.provider_name = "fake"

    # 2. Middleware registration
    app.add_middleware(RequestCorrelationMiddleware)

    # 3. Exception handlers
    app.add_exception_handler(BastionError, bastion_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # 4. Route registration (Public and /api/v1 prefixes)
    app.include_router(dashboard.router)  # / and /dashboard
    app.include_router(health.router)  # /health/live, /health/ready
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(rounds.router, prefix="/api/v1")
    app.include_router(evidence.router, prefix="/api/v1")
    app.include_router(internal.router, prefix="/api/v1")

    return app


# Default module instance for ASGI servers
app = create_app()
