# Implementation Plan — Bastion Arena

This plan organizes implementation into small, testable phases.
**Rule:** Complete one milestone, verify all exit criteria, and obtain approval before starting the next milestone. Do not implement application code until M0 is reviewed.

---

## Milestone 0: Reference Audit & Architecture Reconciliation (Active)
- **Goal:** Audit workspace, inspect ChatGPT & Claude design specifications and prompt guide, resolve architectural conflicts, complete reference index, and establish verified baseline contracts.
- **Tasks:**
  1. Complete inventory of workspace, external references, and configuration files.
  2. Populate `docs/REFERENCE_INDEX.md` with file locations, sections, and gap analyses.
  3. Compare ChatGPT and Claude designs: document agreements, contradictions, and defects.
  4. Perform ledger design audit: document independent hash recomputation requirement.
  5. Clarify logical module vs. process/container/network isolation boundaries.
  6. Record decisions in `DECISIONS.md`, separating approved safe defaults from items requiring user approval.
  7. Refine `IMPLEMENTATION_PLAN.md` with explicit file paths, prerequisites, tests, and measurable exit criteria.
- **Affected Files:**
  - `docs/REFERENCE_INDEX.md`
  - `DECISIONS.md`
  - `IMPLEMENTATION_PLAN.md`
  - `docs/PROJECT_STATUS.md`
- **Prerequisites:** None.
- **Tests Required:** N/A (Documentation audit only).
- **Measurable Exit Criteria:**
  - All original reference files located, copied to `docs/reference/`, and indexed with section references.
  - No application code written or modified.
  - Audit report delivered with clear separation of safe defaults and decisions requiring approval.

---

## Milestone 1: Core Foundation & Configuration (Completed & Verified)
- **Goal:** Establish standard Python package layout, validated configuration loader, Pydantic base models, structured error envelope, structured logging, and a deterministic offline fake provider.
- **Tasks:**
  1. [x] Scaffold `src/bastion_arena/` layout with `__init__.py` and core submodules.
  2. [x] Implement `core/config.py` loading `config.yaml` with environment variable overrides and bounds checking.
  3. [x] Implement `core/errors.py` with typed domain exceptions (`AuthError`, `BudgetExceededError`, `InvalidPhaseError`, etc.) and JSON error envelope model matching `API.md`.
  4. [x] Implement `core/schemas.py` defining core enums (`AgentRole`, `RunPhase`, `VerdictStatus`, `TaxonomyCategory`) and shared Pydantic v2 data models with `extra="forbid"`.
  5. [x] Implement `providers/base.py` (abstract provider interface) and `providers/fake.py` (deterministic offline fake provider returning predictable tokens and scores).
  6. [x] Configure logging in `core/logging.py` (JSON output, secret redaction filter).
  7. [x] Add minimal health check model and validation.
- **Affected Files:**
  - `src/bastion_arena/__init__.py`
  - `src/bastion_arena/core/__init__.py`
  - `src/bastion_arena/core/config.py`
  - `src/bastion_arena/core/errors.py`
  - `src/bastion_arena/core/schemas.py`
  - `src/bastion_arena/core/logging.py`
  - `src/bastion_arena/providers/__init__.py`
  - `src/bastion_arena/providers/base.py`
  - `src/bastion_arena/providers/fake.py`
  - `tests/unit/test_config.py`
  - `tests/unit/test_schemas.py`
  - `tests/unit/test_fake_provider.py`
- **Prerequisites:** M0 approval (Completed).
- **Tests Required:**
  - `test_config.py`: config loading, environment overrides, invalid bounds rejection.
  - `test_schemas.py`: validation of valid/invalid inputs, enum parsing, forbidden extra fields.
  - `test_fake_provider.py`: deterministic response matching given prompt hash.
- **Measurable Exit Criteria:**
  - [x] `python -m compileall src tests` exits 0.
  - [x] `pytest tests/unit/ -q` passes 100% (21/21 passed).
  - [x] `ruff check src tests` and `ruff format --check src tests` exit 0.
  - [x] Zero network calls during tests.

---

## Milestone 2: Blue Defense, Neutral Evaluator & Provider Abstraction (Completed & Verified)
- **Goal:** Implement the Blue defense scanning and redaction pipeline, the neutral Evaluator scoring engine with strict output parsing, and the client model adapter interface.
- **Tasks:**
  1. [x] Implement `agents/blue/scanner.py` with regex/keyword pattern matching, lexical toxicity checks, and input inspection (`check_input`).
  2. [x] Implement `agents/blue/redactor.py` for model output inspection and sensitive data redaction (`check_output`).
  3. [x] Implement `agents/blue/agent.py` orchestrating fast-path checks and rule evaluation.
  4. [x] Implement `agents/evaluator/rubric.py` defining refusal, bypass, and harm scoring criteria (0–2 integer scales, confidence 0.0–1.0).
  5. [x] Implement `agents/evaluator/agent.py` with strict JSON verdict parsing, semantic boundary checks, and marked deterministic fallback on malformed model output.
  6. [x] Implement `providers/openai_client.py` using `httpx.AsyncClient` supporting optional local (Ollama / llama.cpp) and cloud OpenAI-compatible endpoints behind `BaseProvider`.
- **Affected Files:**
  - `src/bastion_arena/agents/blue/__init__.py`
  - `src/bastion_arena/agents/blue/scanner.py`
  - `src/bastion_arena/agents/blue/redactor.py`
  - `src/bastion_arena/agents/blue/agent.py`
  - `src/bastion_arena/agents/evaluator/__init__.py`
  - `src/bastion_arena/agents/evaluator/rubric.py`
  - `src/bastion_arena/agents/evaluator/agent.py`
  - `src/bastion_arena/providers/openai_client.py`
  - `tests/unit/test_blue_agent.py`
  - `tests/unit/test_evaluator_agent.py`
  - `tests/unit/test_openai_client.py`
- **Prerequisites:** M1 (Completed).
- **Tests Required:**
  - `test_blue_agent.py`: detection of known attack keywords, clean pass for benign prompts, output redaction.
  - `test_evaluator_agent.py`: JSON parsing of compliant verdicts, graceful fallback on corrupted/injected evaluator output, scoring bounds enforcement (0–2).
  - `test_openai_client.py`: mock transport test and timeout exception verification.
- **Measurable Exit Criteria:**
  - [x] `python -m compileall src tests` exits 0.
  - [x] `pytest tests/unit/ -q` passes 100% (33/33 passed).
  - [x] `ruff check src tests` and `ruff format --check src tests` exit 0.
  - [x] Evaluator failure does not crash orchestrator and defaults to fail-closed / marked fallback.

---

## Milestone 3: Cryptographic Audit Ledger & Verifier Engine (Completed & Verified)
- **Goal:** Implement the append-only, SHA-256 hash-chained, Ed25519-signed audit ledger, SQLite persistence, and an independent verification engine that recomputes canonical event hashes.
- **Tasks:**
  1. [x] Implement `storage/database.py` with SQLite connection management and migration execution for tables in `DATABASE.md`.
  2. [x] Implement `storage/repositories.py` for transactional round, case, and evaluation records.
  3. [x] Implement `ledger/canonical.py` producing deterministic, sorted, compact JSON bytes for unsigned event data.
  4. [x] Implement `ledger/chain.py` managing sequence numbering, SHA-256 previous-hash chaining, and PyNaCl Ed25519 signing.
  5. [x] Implement `ledger/verifier.py` performing independent hash recomputation from raw event fields, signature verification, and chain link continuity checking.
  6. [x] Implement `ledger/manifest.py` generating signed round evidence manifests.
  7. [x] Create standalone CLI verification utility `scripts/verify_ledger.py`.
- **Affected Files:**
  - `src/bastion_arena/storage/__init__.py`
  - `src/bastion_arena/storage/database.py`
  - `src/bastion_arena/storage/repositories.py`
  - `src/bastion_arena/ledger/__init__.py`
  - `src/bastion_arena/ledger/canonical.py`
  - `src/bastion_arena/ledger/chain.py`
  - `src/bastion_arena/ledger/verifier.py`
  - `src/bastion_arena/ledger/manifest.py`
  - `scripts/verify_ledger.py`
  - `tests/unit/test_ledger.py`
  - `tests/unit/test_ledger_tamper.py`
- **Prerequisites:** M1 (Completed).
- **Tests Required:**
  - `test_ledger.py`: append valid events, verify unbroken chain, generate valid manifest, SQLite persistence.
  - `test_ledger_tamper.py`: tamper tests demonstrating verification failure when:
    - An event field (e.g., payload hash, actor, metadata) is modified in place.
    - An event is deleted from the sequence.
    - Two events are swapped in order.
    - An event hash is forged without a valid private key signature.
- **Measurable Exit Criteria:**
  - [x] `python -m compileall src tests scripts` exits 0.
  - [x] `pytest tests/unit/ -q` passes 100% (42/42 passed).
  - [x] `ruff check src tests scripts` and `ruff format --check src tests scripts` exit 0.
  - [x] Tamper detection succeeds in 100% of mutation cases.

---

## Milestone 4: Arbiter Security Control Plane & State Machine (Completed)
- **Goal:** Implement the core Arbiter orchestration engine: state machine transitions, role/tenant/budget authorization, shadow execution, latency bucketing, and normalized feedback generation.
- **Tasks:**
  1. Implement `core/state.py` defining valid round states (`CREATED`, `SEALED`, `RUNNING`, `CLOSING`, `CLOSED`, `REVEALED`) and transitions.
  2. Implement `security/policy.py` checking caller identity, role, tenant scope, capability tokens, and active phase.
  3. Implement `core/budgets.py` tracking per-tenant concurrency, case count limits, and token budgets.
  4. Implement `services/orchestrator.py` executing the timing-safe test case request loop:
     - Authz check & budget reservation.
     - Synthetic canary token injection.
     - Blue input pre-check.
     - Shadow execution: execute MUT in background regardless of Blue block status (subject to safety limits per DEC-02).
     - Blue output post-check & redaction.
     - Evaluator scoring.
     - Normalized feedback construction (mask raw output and private diagnostics).
     - Quantized latency delay (`sleep_until(target_bucket)`).
     - Ledger append.
- **Affected Files:**
  - `src/bastion_arena/core/state.py`
  - `src/bastion_arena/core/budgets.py`
  - `src/bastion_arena/security/__init__.py`
  - `src/bastion_arena/security/policy.py`
  - `src/bastion_arena/security/tokens.py`
  - `src/bastion_arena/services/__init__.py`
  - `src/bastion_arena/services/orchestrator.py`
  - `src/bastion_arena/services/timing.py`
  - `tests/unit/test_state_machine.py`
  - `tests/unit/test_budgets.py`
  - `tests/integration/test_orchestrator_flow.py`
- **Prerequisites:** M1, M2, M3.
- **Tests Required:**
  - [x] `test_state_machine.py`: valid transitions pass, out-of-order transitions rejected.
  - [x] `test_budgets.py`: rate limits and max-case budgets enforced.
  - [x] `test_orchestrator_flow.py`: end-to-end fake mode case execution, Blue-blocked path shadow execution, feedback payload contains zero raw model tokens.
- **Measurable Exit Criteria:**
  - [x] `pytest tests/unit/test_state_machine.py tests/unit/test_budgets.py tests/integration/test_orchestrator_flow.py -q` passes 100% (51 passed across full test suite).
  - [x] Verified: Red response object matches `API.md` normalized schema with no leaked private keys, prompts, or rationale.
  - [x] `ruff check src tests scripts` and `ruff format --check src tests scripts` exit 0.

---

## Milestone 5: External & Internal API Endpoints (Completed)
- **Goal:** Implement FastAPI application endpoints matching `API.md`, authentication middleware, request correlation IDs, replay attack prevention, and health/readiness checks.
- **Tasks:**
  1. Implement `api/middleware.py` for request ID generation, client identity extraction, and error envelope handling.
  2. Implement `api/routes/health.py` (`GET /health/live`, `GET /health/ready`).
  3. Implement `api/routes/rounds.py` (`POST /rounds`, `POST /rounds/{round_id}/cases`, `GET /cases/{case_id}/result`).
  4. Implement `api/routes/evidence.py` (`POST /evidence/{round_id}/finalize`, `GET /evidence/{round_id}/manifest`).
  5. Implement `api/routes/internal.py` (internal endpoints for blue, evaluator, and synthetic tool gateway).
  6. Implement `tool_gateway/gateway.py` with synthetic mock tools (e.g., mock calculator, mock safe lookup) with strict per-case invocation quotas.
  7. Wire FastAPI application entry point in `src/bastion_arena/main.py`.
- **Affected Files:**
  - `src/bastion_arena/main.py`
  - `src/bastion_arena/api/__init__.py`
  - `src/bastion_arena/api/middleware.py`
  - `src/bastion_arena/api/routes/__init__.py`
  - `src/bastion_arena/api/routes/health.py`
  - `src/bastion_arena/api/routes/rounds.py`
  - `src/bastion_arena/api/routes/evidence.py`
  - `src/bastion_arena/api/routes/internal.py`
  - `src/bastion_arena/tool_gateway/__init__.py`
  - `src/bastion_arena/tool_gateway/gateway.py`
  - `tests/integration/test_api_endpoints.py`
- **Prerequisites:** M4.
- **Tests Required:**
  - [x] `test_api_endpoints.py`: test client queries against all routes; unauthorized access rejection; replay rejection with duplicate case ID; evidence retrieval.
- **Measurable Exit Criteria:**
  - [x] `pytest tests/integration/test_api_endpoints.py -q` passes 100% (59 passed across full test suite).
  - [x] All responses conform to typed JSON contracts with proper HTTP status codes.
  - [x] `ruff check src tests scripts` and `ruff format --check src tests scripts` exit 0.

---

## Milestone 6: Container Hardening & Network Boundary Verification (Completed)
- **Goal:** Create hardened Docker Compose topology separating trust cells (Arbiter, Red, Blue, Model, Evaluator) on dedicated internal networks, with active network reachability tests.
- **Tasks:**
  1. Write `infra/docker/Dockerfile.worker` (unprivileged user, non-root, minimal attack surface).
  2. Write `docker-compose.yml` with 4 isolated internal networks (`net_red`, `net_blue`, `net_model`, `net_eval`).
  3. Apply container security options (`cap_drop: [ALL]`, `no-new-privileges: true`, `read_only: true`, tmpfs mounts, memory/pid limits).
  4. Implement connectivity test script `tests/security/test_network_isolation.py` attempting permitted (Red -> Arbiter) and forbidden (Red -> Blue, Red -> Model, Red -> Internet) network paths.
  5. Add Docker socket mount audit test to verify no cell accesses the host Docker daemon.
- **Affected Files:**
  - `infra/docker/Dockerfile.worker`
  - `infra/docker/seccomp_profile.json`
  - `docker-compose.yml`
  - `tests/security/test_network_isolation.py`
  - `tests/security/test_container_privilege.py`
- **Prerequisites:** M5.
- **Tests Required:**
  - [x] `test_network_isolation.py`: verify dropped packets on forbidden cross-cell connections.
  - [x] `test_container_privilege.py`: verify non-root user, dropped capabilities, no Docker socket.
- **Measurable Exit Criteria:**
  - [x] `docker compose config` validates without errors.
  - [x] Integration tests demonstrate forbidden cell-to-cell TCP connections are blocked.
  - [x] `pytest tests/security/ -q` passes 100% (12 security tests passing, 71 passed across full test suite).
  - [x] `ruff check src tests scripts` and `ruff format --check src tests scripts` exit 0.
  - [x] Explicit reporting: report actual isolation boundary achieved on host.

---

## Milestone 7: Optional Local Model Runtime Profile (Completed)
- **Goal:** Add support for running local open-weights models (via Ollama or llama.cpp OpenAI-compatible server) while maintaining deterministic fake mode as the default for all tests.
- **Tasks:**
  1. Implement runtime profile selector in `core/config.py` (`fake` | `ollama` | `openai_compatible_cloud`).
  2. Implement model metadata recording and SHA-256 weight hash commitment in round configuration.
  3. Implement provider timeout, retry, and circuit breaker policies (`core/resilience.py`).
  4. Document local model setup instructions in `README.md`.
- **Affected Files:**
  - `src/bastion_arena/core/resilience.py`
  - `src/bastion_arena/providers/factory.py`
  - `src/bastion_arena/providers/__init__.py`
  - `src/bastion_arena/main.py`
  - `tests/integration/test_provider_resilience.py`
  - `README.md`
- **Prerequisites:** M5.
- **Tests Required:**
  - [x] `test_provider_resilience.py`: simulate provider timeout, verify circuit breaker trips, verify explicit `MODEL_TIMEOUT` error returned rather than silent safe verdict.
- **Measurable Exit Criteria:**
  - [x] Full test suite passes without Ollama installed or running (`providers.mode = fake`).
  - [x] Switching to `ollama` profile connects seamlessly when a local server is present.
  - [x] `pytest tests/integration/test_provider_resilience.py -q` passes 100% (76 passed across full test suite).
  - [x] `ruff check src tests scripts` and `ruff format --check src tests scripts` exit 0.

---

## Milestone 8: Demo Hardening, Isolation Scorecard & Acceptance (Completed)
- **Goal:** Package an automated, one-command demonstration showing normal evaluation flow, an automated tamper detection demo, and a published security scorecard.
- **Tasks:**
  1. Implement automated test runner `scripts/run_demo.py` (executes 5 benchmark test cases offline, prints results, exports signed evidence).
  2. Implement tamper demo `scripts/demo_tamper.py` (alters one byte in stored ledger, demonstrates verifier detecting corrupted sequence and pinpointing record).
  3. Implement automated Isolation Scorecard script `scripts/run_scorecard.py`.
  4. Update `docs/PROJECT_STATUS.md` with verified test results and final scorecard.
  5. Final audit against `AGENTS.md` and all security invariants.
- **Affected Files:**
  - `scripts/run_demo.py`
  - `scripts/demo_tamper.py`
  - `scripts/run_scorecard.py`
  - `docs/PROJECT_STATUS.md`
  - `README.md`
- **Prerequisites:** M1 through M7.
- **Tests Required:**
  - [x] Full test battery: `pytest -q` (76 passed).
  - [x] Smoke test execution via `python scripts/run_demo.py` (5 benchmark cases executed, manifest exported and verified).
  - [x] Tamper demonstration via `python scripts/demo_tamper.py` (100% tamper detection across 4 mutation scenarios).
  - [x] Isolation Scorecard via `python scripts/run_scorecard.py` (12/12 security controls verified).
- **Measurable Exit Criteria:**
  - [x] Complete demo runs in < 60 seconds offline with zero paid API keys or downloads (actual: ~5 seconds).
  - [x] Tamper demo reliably detects corrupted records with 100% precision.
  - [x] Every security claim is backed by automated test output.
  - [x] `ruff check src tests scripts` and `ruff format --check src tests scripts` exit 0.

---

**Current Status:** All Milestones (M0 through M8) completed and verified. System is fully operational, hardened, and verified against Track 04 problem requirements.
