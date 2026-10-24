# AGENTS.md — Persistent Coding Rules

These instructions apply to all work in this repository.

## Before changing anything
1. Inspect the workspace tree, relevant files, and `git status` first.
2. Read `PRD.md`, `ARCHITECTURE.md`, `SECURITY_MODEL.md`, and the active phase in `IMPLEMENTATION_PLAN.md`.
3. Read the source specifications listed in `docs/REFERENCE_INDEX.md` when relevant.
4. Record conflicts or material assumptions in `DECISIONS.md`. Do not silently invent requirements.
5. Implement one phase or one feature per task; do not build the entire platform in one pass.

## Non-negotiable security invariants
- Bastion Arena tests a declared synthetic/local target only. No unauthorized third-party testing.
- The Arbiter is the security control plane; agents are not security boundaries.
- Red must not directly access Blue, the Model Under Test (MUT), evaluator internals, host resources, or other tenants.
- Blue must not access Red-private strategy/state or communicate directly with the MUT.
- Evaluator receives the minimum artifact for one case only.
- MUT must not access host paths, Docker socket, production data, provider credentials, or signing keys.
- Raw model output, Blue private diagnostics, evaluator prompt/rationale, and raw private ledger records must not be returned to Red. Return the normalized feedback contract only.
- A blocked Blue pre-check does not automatically imply that inference is skipped; follow the approved shadow-execution policy, subject to explicit platform safety limits.
- Infrastructure or evidence failure must never be silently converted into a `safe` verdict.
- Every security claim must be labeled implemented/tested/planned/residual risk. Never fabricate measurements.
- Ledger verification must independently recompute canonical event hashes, verify signatures, and verify previous-hash continuity. Never trust stored hashes alone.

## Implementation rules
- Python 3.11+; type hints on public interfaces.
- MVP defaults: FastAPI, Pydantic v2, `httpx`, native async Python state machine, SQLite, PyNaCl, pytest, Ruff, Docker Compose.
- Use deterministic fake providers for tests and default smoke runs. Ollama/local models and cloud providers are optional adapters, not hard dependencies.
- Keep provider integrations behind an interface. Keep routes thin and security decisions in services/policies.
- Use strict Pydantic models (`extra="forbid"` where practical), bounded strings/numbers, enums, explicit timeouts, bounded retries, and dependency injection.
- No unnecessary framework, broker, database, or deployment platform without a decision entry.
- Never hardcode secrets or commit `.env`, API keys, private keys, certificates, model weights, or sensitive data.
- Untrusted containers must not use privileged mode, host networking/PID, Docker socket mounts, or unnecessary host mounts.
- Python package boundaries do not count as container/network isolation. Test real paths before claiming isolation.
- Do not hide errors with broad exception handling or weaken tests just to get a green build.

## Verify changes
Run applicable checks and report exact results:
```bash
python -m compileall src tests
pytest -q
ruff check .
ruff format --check .
docker compose config
```
If a command was not run, say so. Do not report it as passed.

## Completion report
State: behavior changed; files changed; commands actually run and results; known limitations; security claims not yet verified; follow-up tasks.

## Change discipline
Inspect before editing. Reuse existing patterns. Avoid unrelated rewrites. Update tests and docs when a contract changes. Never overwrite or delete original design-reference documents.
