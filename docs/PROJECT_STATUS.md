# Project Status

- Current milestone: M8 — Demo Hardening, Isolation Scorecard & Acceptance (Completed & Verified)
- Application implementation status:
  - Foundation package `src/bastion_arena` operational.
  - Blue defense scanner and canary/credential redactor implemented (`agents/blue/`).
  - Neutral Evaluator with strict JSON parsing and marked deterministic fallback implemented (`agents/evaluator/`).
  - Model providers (deterministic offline FakeProvider and OpenAI-compatible client) operational.
  - SQLite database and transactional repositories implemented (`storage/`).
  - Cryptographic append-only SHA-256 hash-chained ledger and Ed25519 signing implemented (`ledger/`).
  - Independent verification engine implementing ADR-005 (recomputing hashes from canonical unsigned fields) verified with 100% tamper detection.
  - Signed evidence manifest generator and CLI auditor tool implemented (`scripts/verify_ledger.py`).
  - Arbiter finite state machine with strict phase progression (`COMMIT` -> `SEAL` -> `RUN` -> `CLOSE` -> `REVEAL` -> `VERIFY`) implemented (`core/state.py`).
  - Per-tenant concurrency locks and case quota budget management implemented (`core/budgets.py`).
  - Attribute-based access control (ABAC) and HMAC capability tokens with JTI replay protection implemented (`security/`).
  - Discrete latency quantization and shadow execution timing governor implemented (`services/timing.py`).
  - Complete Arbiter orchestration flow with feedback isolation, shadow execution, and ledger logging verified (`services/orchestrator.py`).
  - Request correlation middleware (`X-Request-ID`), standardized `ErrorEnvelope` handling, and capability token extraction implemented (`api/middleware.py`).
  - Health liveness and readiness endpoints implemented (`api/routes/health.py`).
  - Round creation, case submission, and tenant-scoped result queries implemented (`api/routes/rounds.py`).
  - Evidence finalization, cryptographic verification, and manifest retrieval implemented (`api/routes/evidence.py`).
  - Authenticated internal service endpoints implemented for Blue, Evaluator, and Tool Gateway (`api/routes/internal.py`).
  - Synthetic sandboxed mock tools (calculator, safe lookup, echo) with strict per-case invocation quotas implemented (`tool_gateway/gateway.py`).
  - FastAPI application factory entry point wired (`src/bastion_arena/main.py`).
  - Unprivileged worker container definition created (`infra/docker/Dockerfile.worker`).
  - Hardened seccomp profile dropping ptrace, bpf, kexec, and mount syscalls created (`infra/docker/seccomp_profile.json`).
  - Multi-cell Docker Compose topology with 4 isolated internal networks (`net_red`, `net_blue`, `net_model`, `net_eval`), non-root UID 10001, dropped capabilities, no-new-privileges, read-only root filesystems, and tmpfs configured (`docker-compose.yml`).
  - Container privilege boundaries and network isolation tests verified (`tests/security/`).
  - Three-state provider circuit breaker and bounded retry policy implemented (`core/resilience.py`).
  - Dynamic runtime provider factory wired supporting `fake`, `ollama`, and `openai_compatible_cloud` (`providers/factory.py`).
  - Comprehensive documentation and setup instructions recorded in `README.md`.
  - Automated offline demo runner executing 5 benchmark cases in < 6 seconds implemented (`scripts/run_demo.py`).
  - Cryptographic tamper demonstration script showing 100% attack detection implemented (`scripts/demo_tamper.py`).
  - Automated 12-control Security Isolation Scorecard script implemented (`scripts/run_scorecard.py`).
- Default provider profile: `fake` / offline (100% offline, zero network or API keys required)
- Next milestone: All implementation phases complete. Production & evaluation ready.

| Date | Milestone | Status | Tests run | Notes |
|---|---|---|---|---|
| 2026-10-19 | M0 reference audit | Completed | N/A (Doc audit) | References discovered, copied to `docs/reference/`, indexed in `docs/REFERENCE_INDEX.md`. Critical ledger flaw documented. `DECISIONS.md` and `IMPLEMENTATION_PLAN.md` updated. |
| 2026-10-24 | M1 core foundation | Completed | 21 passed in 0.45s | `compileall` passed, 21 unit tests passed, `ruff check` passed, `ruff format --check` passed. Offline fake provider verified. |
| 2026-10-24 | M2 Blue & Evaluator | Completed | 33 passed in 0.58s | All 33 unit tests passed (Blue scanner, redactor, Evaluator JSON parsing/fallback, and OpenAI client mock). `compileall` clean, `ruff` clean. |
| 2026-10-24 | M3 Ledger & Storage | Completed | 42 passed in 0.75s | All 42 unit tests passed (9 new tests for canonical JSON, chain creation, manifest signing, SQLite repositories, and 100% tamper detection across in-place modification, deletion, reordering, bad sigs, metadata). `verify_ledger.py` CLI verified. |
| 2026-10-24 | M4 Arbiter & Control Plane | Completed | 51 passed in 1.17s | All 51 unit & integration tests passed (state machine, tenant budgets, capability tokens, replay protection, and end-to-end orchestrator flow with shadow execution and feedback isolation). `ruff` clean, `compileall` clean. |
| 2026-10-24 | M5 API & Tool Gateway | Completed | 59 passed in 3.34s | All 59 tests passed (8 new integration tests for health probes, 401 unauthenticated rejection, round creation, case execution, replay attack rejection, tenant isolation, evidence finalization/manifest, internal endpoint protection, and tool gateway quota enforcement). `ruff` clean, `compileall` clean. |
| 2026-10-24 | M6 Container Hardening | Completed | 71 passed in 3.74s | All 71 tests passed (12 new security tests verifying no Docker socket mounts, cap_drop ALL, no-new-privileges, read-only rootfs, unprivileged non-root UID 10001, CPU/memory/PID limits, dangerous syscall seccomp blocks, 4 internal isolated networks, Arbiter sole bridge, and zero cross-cell overlap). `docker compose config` validates clean. `ruff` clean, `compileall` clean. |
| 2026-10-24 | M7 Local Profiles & Circuit Breaker | Completed | 76 passed in 4.05s | All 76 tests passed (5 new resilience tests for circuit breaker tripping, recovery via HALF_OPEN, bounded retry execution, retry exhaustion, and security invariant asserting no silent pass on provider timeout). `ruff` clean, `compileall` clean. |
| 2026-10-24 | M8 Demo Hardening & Scorecard | Completed | 76 passed in 3.82s | Automated demo (`run_demo.py`), tamper demonstration (`demo_tamper.py`), and 12/12 security scorecard (`run_scorecard.py`) verified. 100% test battery passing. All milestones complete. |
