# Reference Index

This document maps all original design specifications and prompt references for Bastion Arena.
The source files are preserved under `docs/reference/` and must remain immutable.

| ID | Repository path | Original external path | Format | Key requirements / sections | Conflicts, defects, or gaps |
|---|---|---|---|---|---|
| **REF-01** | `docs/reference/Bastion_Arena_System_Design_Spec.md` | `C:\Users\shots\OneDrive\Desktop\hackHills\Bastion_Arena_System_Design_Spec.md` (also in `Bastion_Arena_System_Design_Spec_Pack.zip`) | Markdown (3,007 lines, 43 sections) | System design spec: Sections 0–12 architecture & execution model; Sections 13–19 initial code sketches (`core/schemas.py`, `core/providers.py`, `agents/red/agent.py`, `agents/blue/agent.py`, `agents/evaluator/agent.py`, `core/ledger.py`, `arbiter/orchestrator.py`); Section 20 `config.yaml`; Section 21 Docker Compose baseline; Sections 22–31 mTLS, tokens, audit, failure semantics; Sections 32–43 roadmap & scorecard. | **Critical Defect in Section 18:** `ledger.verify()` validates signatures against stored `event_hash` without recomputing the SHA-256 hash from unsigned canonical fields. In-place tampering of event fields goes undetected. Over-engineered code sketches mixed with specification. |
| **REF-02** | `docs/reference/Bastion_Arena_System_Design_Spec_Part_II.md` | `C:\Users\shots\OneDrive\Desktop\hackHills\Bastion_Arena_System_Design_Spec_Part_II.md` | Markdown (4,185 lines, 103 sections) | Hardened specification: Sections 1–3 principles, service decomposition & API contracts; Sections 4–8 budgets, auth, capability tokens, mTLS; Sections 9–12 model adapters, evaluator JSON parsing, Blue pipeline, Arbiter middleware; Sections 13–15 SQLite relational schema & ledger persistence; Sections 16–19 evidence manifest, bundle, replay & determinism; Sections 20–24 fake tool gateway, container hardening, seccomp, network isolation; **Sections 40–43 Correct Ledger Verification Contract**; Sections 44–47 evidence export & Docker Compose topology; Sections 48–56 runtime profiles, failure handling, secrets; Sections 57–76 isolation testing (canaries, timing, KV-cache, noisy neighbor, network, socket); Sections 77–103 CI/CD, error model, feedback budget, definition of done. | Resolves the REF-01 ledger verification flaw by mandating independent hash recomputation from unsigned canonical fields. Introduces extensive production-grade features (Cilium L7, OpenFGA, Vault, TLA+ formal verification) that exceed MVP scope and must be staged. |
| **REF-03** | `docs/reference/Bastion_Arena_System_Design.pdf` | `C:\Users\shots\OneDrive\Desktop\hackHills\Bastion_Arena_System_Design.pdf` | PDF (13 pages, 10 sections + Appendix A) | Claude system design & hackathon brief: Page 1 winning thesis & 4 hidden contradictions (blind execution, controlled oracle, governed fairness, security plane diode); Page 2 4-plane architecture (Control, Data, Evidence, Security); Page 3 epoch protocol (commit → seal → run → close → reveal → verify); Pages 4–6 deep dive on 7 technical verticals (gVisor sandboxing, 4 internal Docker networks, Biscuit/OPA access, hash-chained ledger, cgroup v2 resource governance, LLM threat surface & KV-cache probe, eBPF diode); Pages 6–7 threat model, residual risk & tech stack; Pages 8–9 implementation playbook, timing-safe Arbiter hot path, 12-attack Isolation Scorecard (T1–T12); Pages 10–13 pitch script, economics, roadmap. | Assumes a native Linux kernel with gVisor (`runsc`), cgroup v2 CPU pinning, eBPF Tetragon/Falco, and OpenBao KMS which cannot execute directly on Windows development environments without nested virtualization. Page 5 ledger verifier snippet hashes untyped dicts and omits structured field validation. |
| **REF-04** | `docs/reference/Important Vibecoding Prompts.pdf` | `C:\Users\shots\Downloads\Important Vibecoding Prompts.pdf` | PDF (14 pages, 20 prompts) | Vibecoding prompt methodology guide: 1. PRD Creation (p. 1); 2. DESIGN.md (p. 1–2); 3. ARCHITECTURE.md (p. 2–3); 4. DATABASE.md (p. 3); 5. API.md (p. 3–4); 6. AGENTS.md / Coding Rules (p. 4–5); 7. Implementation Planning (p. 5); 8. Project Setup (p. 5–6); 9. Feature Development (p. 6–7); 10. Database & Backend Connection (p. 7); 11. Authentication & Authorization (p. 7–8); 12. MCP Connection (p. 8–9); 13. External API Integration (p. 9); 14. Testing & QA (p. 9–10); 15. Debugging / Root Cause (p. 10–11); 16. Security Audit & Hardening (p. 11); 17. Code Review & Refactoring (p. 12); 18. Deployment & Production Setup (p. 12–13); 19. Production Monitoring & Maintenance (p. 13–14); 20. Final Production Audit (p. 14). | Process discipline and prompt engineering standards for agent workflows; provides engineering rules (e.g. no unnecessary dependencies, fail closed, test before claiming victory), not application platform requirements. |

## Detailed Traceability and Section Mapping

### 1. Control Plane & Orchestration
- **REF-01:** Section 8 (Arbiter Gateway), Section 11 (Why Native Async State Machines Are Default), Section 19 (`arbiter/orchestrator.py`).
- **REF-02:** Section 2 (Process and Service Decomposition), Section 27 (Orchestrator API Layer), Section 28 (State Machine Implementation).
- **REF-03:** Section 2 (System Architecture), Section 6.3 (Arbiter Hot Path timing-safe loop).
- **Canonical Contract:** `ARCHITECTURE.md` (Native async state machine, FastAPI endpoints), `AGENTS.md` (Arbiter as sole control plane).

### 2. Ledger, Hashing & Cryptographic Verification
- **REF-01:** Section 18 (`core/ledger.py` with defective verification), Section 25 (Audit & Evidence Model).
- **REF-02:** Section 15 (Ledger Persistence), Section 16 (Evidence Manifest), Section 40 (`tests/unit/test_ledger.py`), Section 41 (Ledger Tamper Test), **Section 42 (Correct Ledger Verification Contract)**, **Section 43 (Correct `ledger.verify()` Example)**.
- **REF-03:** Section 3.4 (Audit trails and forensic provenance), Page 5 (`class Ledger` and `verify` snippet).
- **Canonical Contract:** `DATABASE.md` (Table `ledger_events`), `SECURITY_MODEL.md` (Tamper-to-control map), `DECISIONS.md` (ADR-005).

### 3. Isolation & Boundary Defenses
- **REF-01:** Section 2.1 (Trust zones), Section 3.2 (Network topology), Section 21 (`docker-compose.yml`), Section 24 (Tool Isolation).
- **REF-02:** Section 20 (Tool Gateway), Section 21 (Container Hardening), Section 24 (Network Isolation), Section 47 (Docker Compose Topology), Sections 72–75 (Isolation Test Scripts).
- **REF-03:** Section 1 (Winning thesis), Section 3.1 (Container & sandbox isolation), Section 3.2 (Network segmentation), Section 7 (Isolation Scorecard T1–T12).
- **Canonical Contract:** `SECURITY_MODEL.md` (Required boundaries & threat map), `ARCHITECTURE.md` (Trust caveat: logical modules vs. container networks).

### 4. LLM & Evaluation Pipeline
- **REF-01:** Section 5 (Dual-model execution), Section 6 (Agent grounding & prompts), Section 9 (Evaluator design), Section 14 (`core/providers.py`).
- **REF-02:** Section 9 (Model Adapter Layer), Section 10 (Structured Evaluator Output), Section 11 (Blue Decision Pipeline), Section 29 (Shadow Execution Contract), Section 30 (Latency Normalization).
- **REF-03:** Section 2.1 (Request path & shadow execution), Section 3.6 (LLM-specific threat surface: KV-cache probe, stateless lanes, pinned weights).
- **Canonical Contract:** `PRD.md` (MVP requirements 2–6), `API.md` (Normalized response & internal endpoints).

### 5. Data Model & Storage
- **REF-01:** Section 13 (`core/schemas.py`), Section 18 (`data/ledger.jsonl`).
- **REF-02:** Section 13 (Persistent State Model: SQLite rationale & schema), Section 14 (Database Rules).
- **REF-03:** Section 3.4 (SQLite/Postgres ledger), Page 4 Core Stack (PostgreSQL relational state store).
- **Canonical Contract:** `DATABASE.md` (SQLite relational schema: `tenants`, `campaigns`, `rounds`, `cases`, `evaluations`, `ledger_events`, `capability_jtis`).
