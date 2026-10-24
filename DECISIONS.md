# Architecture Decision Log

This log records architectural decisions, material conflicts between reference specifications, chosen resolutions, and their security implications.

---

## Approved Safe Defaults (Operational for MVP)

### ADR-001 — Native State Machine for Control Plane
- **Context:** Claude specifies an Arbiter gateway with OPA policies. ChatGPT Part I evaluates LangGraph/CrewAI/AutoGen before selecting a native Python state machine.
- **Options:**
  1. External multi-agent orchestration framework (LangGraph, CrewAI, AutoGen).
  2. Native async Python state machine with explicit transitions.
- **Recommendation:** Option 2. Explicit async transitions in `core/state.py` and `services/orchestrator.py`.
- **Security Impact:** Eliminates black-box framework behavior, prevents hidden prompt injection pathways, ensures 100% deterministic reviewable control flow, and simplifies testing.
- **Status:** Approved default.

### ADR-002 — Offline-First with Deterministic Fake Providers
- **Context:** Claude assumes running local 1–3B GGUF models via llama.cpp or vLLM. ChatGPT references Ollama and cloud APIs.
- **Options:**
  1. Require a live local model (Ollama / llama.cpp) or cloud API key for baseline startup and testing.
  2. Implement an offline-first deterministic fake provider as default; local model serving and cloud APIs are optional pluggable adapters.
- **Recommendation:** Option 2. All unit, integration, and security tests must execute without network connectivity or API credentials.
- **Security Impact:** Eliminates non-deterministic test flakiness, guarantees CI runs in air-gapped environments, and prevents credential leakage in CI/CD pipelines.
- **Status:** Approved default.

### ADR-003 — SQLite Relational Storage behind Repository Boundary
- **Context:** Claude specifies PostgreSQL in presentation slides and SQLite/Postgres in text. ChatGPT Part I sketches a flat JSONL file (`ledger.jsonl`), while ChatGPT Part II and `DATABASE.md` specify an SQLite schema.
- **Options:**
  1. Flat JSONL files for all state and ledger events.
  2. External PostgreSQL database container.
  3. Single-host SQLite database accessed via strict repository interfaces (`storage/`).
- **Recommendation:** Option 3. SQLite for MVP. Tables: `tenants`, `campaigns`, `rounds`, `cases`, `evaluations`, `ledger_events`, `capability_jtis`.
- **Security Impact:** Enforces ACID transactions for case submission and ledger append; prevents file-corruption race conditions; avoids external DB container dependency in MVP while keeping repositories swappable for Postgres later.
- **Status:** Approved default.

### ADR-004 — Evidence-Based Security Claims
- **Context:** Claude's pitch brief presents an ambitious 12-test scorecard and claims gVisor, zero timing leakage, and KV-cache isolation.
- **Options:**
  1. Assert security properties based on architectural intent or mock unit tests.
  2. Strictly categorize every security property as: `implemented-and-tested`, `implemented-not-tested`, `planned`, or `residual risk`.
- **Recommendation:** Option 2. Never claim container isolation, timing side-channel elimination, or hypervisor security without empirical, recorded test execution.
- **Security Impact:** Preserves audit credibility and eliminates false senses of security.
- **Status:** Invariant rule.

### ADR-005 — Independent Hash Recomputation in Ledger Verification
- **Context:** REF-01 (ChatGPT Part I Section 18) had a critical defect: `ledger.verify()` only checked `verify_key.verify(event.event_hash, signature)` and `previous_hash` equality without recomputing `event_hash` from canonical unsigned fields. Claude's snippet (Page 5) used untyped dict hashing. REF-02 (ChatGPT Part II Sections 41–43) resolved this.
- **Options:**
  1. Verify stored signatures directly against stored `event_hash` (REF-01 flaw).
  2. Independently reconstruct canonical unsigned event fields, recompute SHA-256 hash, compare with stored `event_hash`, verify Ed25519 signature, and verify `previous_hash` chain continuity (REF-02 standard).
- **Recommendation:** Option 2. The verifier MUST independently recompute:
  $$\text{expected\_hash} = \text{SHA-256}(\text{canonical\_json}(\text{unsigned\_fields}))$$
  $$\text{assert } \text{expected\_hash} == \text{event.event\_hash}$$
  $$\text{verify\_signature}(\text{event.event\_hash}, \text{event.signature\_b64})$$
  $$\text{assert } \text{event.previous\_hash} == \text{expected\_previous\_hash}$$
- **Security Impact:** Closes the vulnerability where an attacker tampers with event fields (payload hash, metadata, actor, phase) while leaving the original valid `event_hash` and signature untouched.
- **Status:** Invariant rule.

### ADR-006 — In-Process Python Policy Enforcement vs. External OPA Daemon
- **Context:** Claude specifies Open Policy Agent (OPA) with Rego rules (`policy/authz.rego`) for every request. ChatGPT Part II specifies Python middleware enforcing role/tenant/budget/phase attributes.
- **Options:**
  1. Deploy an external OPA daemon container and execute HTTP/gRPC policy queries for every state transition.
  2. Implement an in-process, typed Python policy engine (`security/policy.py`) executing identical ABAC rules.
- **Recommendation:** Option 2 for MVP. Defer external OPA daemon to post-MVP production hardening.
- **Security Impact:** Reduces latency and deployment complexity; keeps authorization logic within the Python type checker; maintains identical zero-trust ABAC semantics.
- **Status:** Approved default.

### ADR-007 — Local PyNaCl Key Management vs. HashiCorp Vault / OpenBao KMS
- **Context:** Claude specifies HashiCorp Vault / OpenBao dev server with transit engine for per-epoch envelope encryption and Shamir-split unsealing. ChatGPT Part I/II recommends local PyNaCl Ed25519 keys loaded via environment or injected tmpfs files.
- **Options:**
  1. Mandate OpenBao/Vault container and API initialization scripts for MVP.
  2. Use PyNaCl `SigningKey` generated in memory for tests or loaded from an environment variable / secure file path (`BASTION_SIGNING_KEY`).
- **Recommendation:** Option 2. Defer Vault/OpenBao KMS daemon for the single-host MVP.
- **Security Impact:** Prevents key management infrastructure failure from blocking local tests and hackathon demos, while keeping the cryptographic signing primitive (Ed25519) identical.
- **Status:** Approved default.

### ADR-008 — Application-Level Structured Logging & Canaries vs. Kernel eBPF Diode
- **Context:** Claude specifies eBPF (Tetragon or Falco) kernel tracing emitting to a sealed SIEM through a one-way hardware diode. ChatGPT Part II specifies structured JSON logging with strict field whitelisting and canary detection.
- **Options:**
  1. Require eBPF kernel probes (Linux-only, root required, fails on standard Windows/macOS Docker environments).
  2. Implement application-level structured logging with strict field whitelisting, synthetic canary scanning, and redaction.
- **Recommendation:** Option 2 for MVP. Structured JSON logs with automated canary alert triggers.
- **Security Impact:** Ensures the observability system itself does not become a data leak channel; runnable cross-platform.
- **Status:** Approved default.

### ADR-009 — Synthetic Benchmark Corpora and Mock Tool Gateway vs. Arbitrary Code Packs
- **Context:** Claude describes Red and Blue uploading arbitrary code "packs" executed in isolated sandboxes. ChatGPT Part I/II & PRD constrain inputs to synthetic prompt benchmarks and tools to an allow-listed mock gateway.
- **Options:**
  1. Accept arbitrary untrusted binary/script packages for Red attacks and Blue defenses.
  2. Restrict Red attacks to structured benchmark datasets (JailbreakBench, HarmBench slices) and Blue defenses to bounded rule/classifier pipelines, routing target calls through an allow-listed synthetic tool gateway.
- **Recommendation:** Option 2. In MVP, Red and Blue operate on declarative prompts, rules, and synthetic tool requests.
- **Security Impact:** Eliminates arbitrary remote code execution risks on the host during initial milestones; enables strict input validation.
- **Status:** Approved default.

### ADR-010 — Container Hardening Baseline: Docker Compose with runc + Seccomp
- **Context:** Claude mandates gVisor (`runsc`) for all cell sandboxing. gVisor requires a native Linux host kernel and fails under Docker Desktop on Windows/macOS.
- **Options:**
  1. Mandate gVisor (`runsc`), preventing local testing on Windows/macOS development machines.
  2. Use standard Docker Compose with `security_opt: ["no-new-privileges:true"]`, `cap_drop: ["ALL"]`, `read_only: true`, `pids_limit`, `mem_limit`, and custom seccomp profiles as the portable baseline. Auto-detect `runsc` if available on Linux, and gracefully report degraded sandbox status if absent.
- **Recommendation:** Option 2. Maintain developer portability while enforcing strict container boundaries.
- **Security Impact:** Transparently documents the boundary level rather than failing or silently claiming hypervisor isolation.
- **Status:** Approved default.

---

## Decisions Requiring User Approval

### DEC-01 — Inter-Cell Workload Authentication (mTLS vs. Docker Internal Network + HMAC Capability Tokens)
- **Context:**
  Claude mandates mutual TLS (mTLS) with short-lived certificates issued by `step-ca` or SPIFFE/SPIRE for all internal service communication. ChatGPT Part II outlines an mTLS PKI hierarchy but notes that local testing requires substantial certificate generation and distribution infrastructure.
- **Options:**
  - **Option A (Recommended):** Use Docker internal networks (isolated bridge networks with no inter-cell routing) combined with HMAC-SHA256 signed capability tokens in HTTP headers (`Authorization: Bearer <token>`) validated by the Arbiter. Keep mTLS as an optional profile for hardened deployments (M6).
  - **Option B (Strict Claude Design):** Mandate `step-ca` sidecar container and mTLS certificates for all inter-container HTTP/gRPC traffic from Milestone 6 onward.
- **Architect's Assessment:** Option A provides full cryptographic authentication and authorization between cells without introducing certificate expiration, bootstrapping, and CA complexity into early development and local developer environments.
- **Status:** PENDING USER APPROVAL.

### DEC-02 — Shadow Execution Policy and Platform Safety Limits
- **Context:**
  Both Claude and ChatGPT agree on *shadow execution*: when Blue blocks an attack prompt, the Arbiter still executes the prompt against the Model Under Test (MUT) in the background so that response latency does not reveal whether Blue blocked the prompt (preventing a timing oracle). However, ChatGPT Part II and `AGENTS.md` note that blindly executing every blocked input poses resource exhaustion risks and potential safety hazards.
- **Options:**
  - **Option A (Recommended):** Implement shadow execution by default, but subject it to strict platform safety filters: if a prompt exceeds hard character bounds, triggers severe internal canary tripwires, or exhausts tenant compute budget, shadow execution is aborted and replaced with synthetic latency padding (`sleep_until(target_bucket)`).
  - **Option B (Unconditional Shadow Execution):** Always invoke the MUT on every blocked input regardless of content or budget, prioritizing absolute timing indistinguishability above compute cost and resource safety.
- **Architect's Assessment:** Option A prevents denial-of-service and extreme payload risks while maintaining timing defense via artificial latency padding when execution is truncated.
- **Status:** PENDING USER APPROVAL.

### DEC-03 — Cryptographic Evidence Structure: Linear Hash Chaining vs. Epoch Merkle Trees
- **Context:**
  ChatGPT Part I & II and Claude agree that every event must be SHA-256 hash-chained and Ed25519-signed. Claude additionally specifies computing a full cryptographic Merkle tree per epoch to enable $O(\log n)$ inclusion proofs for individual cases ("prove case 481 was in epoch 17") anchored to external RFC 3161 timestamping authorities or Sigstore Rekor.
- **Options:**
  - **Option A (Recommended for MVP):** Implement the linear append-only SHA-256 hash chain with Ed25519 signed manifest per round/epoch (Milestone 3). Defer full Merkle tree inclusion proofs and external TSA/Rekor anchoring to post-MVP.
  - **Option B (Full Merkle Tree in MVP):** Implement both linear hash chaining and a binary Merkle tree engine with inclusion proof generation in Milestone 3.
- **Architect's Assessment:** Linear hash chaining and Ed25519 signatures completely satisfy the tamper-evidence and auditability requirements for MVP. Merkle inclusion proofs are an optimization for very large epochs ($n > 10,000$).
- **Status:** PENDING USER APPROVAL.
