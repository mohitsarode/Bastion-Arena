# Prompt 1 — Reference audit and design reconciliation (NO CODING)

Paste into Antigravity after opening the repository root.

---

You are the Staff Engineer and AI Security Architect preparing Bastion Arena for implementation.

**This is a documentation-audit task only. Do not write application code, install packages, delete files, or rewrite original references.**

First inspect the entire workspace tree, Git status, Markdown, PDFs, configs, and any existing code. The folder contains system-design specifications from ChatGPT and Claude, plus a PDF called “Important Vibecoding Prompts”. Discover the actual filenames; do not assume them.

Read `AGENTS.md`, `PRD.md`, `ARCHITECTURE.md`, `DATABASE.md`, `API.md`, `SECURITY_MODEL.md`, `TESTING.md`, `IMPLEMENTATION_PLAN.md`, and `DECISIONS.md`. Then read every original system-design reference in full.

Tasks:
1. Fill `docs/REFERENCE_INDEX.md` using actual source paths, types, key requirements and page/section references.
2. Compare ChatGPT and Claude designs: agreements, contradictions, missing decisions, implementation defects and over-engineered elements.
3. Audit the ledger design: verifier must recompute event hashes from canonical event fields, compare against stored hash, verify signatures, and verify previous-hash continuity. Verifying a signature against only the stored hash is insufficient.
4. Distinguish logical Python module boundaries from actual process/container/network isolation.
5. Ensure core tests and the first demo work offline with deterministic fake providers. Ollama and cloud APIs are optional profiles.
6. Keep one coherent minimal MVP contract. Do not add frameworks or services without a documented reason.
7. Record each important conflict/decision in `DECISIONS.md` with context, choices, recommendation, security impact, status, and source paths.
8. Update `IMPLEMENTATION_PLAN.md` into small phases with files, prerequisites, tests, and measurable exit criteria.
9. Keep original references unchanged. Update canonical docs only to remove ambiguity; do not blindly paste reference content.
10. List all unresolved decisions requiring my approval separately from safe defaults.

Security invariants: Arbiter is the control plane; Red, Blue, Evaluator and MUT are untrusted relative to one another; no raw MUT output or private Blue/Evaluator details are returned to Red; testing is limited to synthetic/local targets; do not claim mTLS, gVisor, KV-cache isolation, no timing leakage or container isolation until implemented and verified.

Deliver an audit report with workspace inventory, source-doc agreement/conflicts, recommended decisions, docs changed, blocking questions, and the first coding task. Stop and wait for my review. **No application code in this run.**
