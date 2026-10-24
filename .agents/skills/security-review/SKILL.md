---
name: security-review
description: Reviews changes for trust-boundary violations, data leakage, authorization flaws, container risks and audit-integrity defects.
---

# Security Review

For each change, check:
1. What trust zone receives the data?
2. Is identity/tenant/role/capability/phase validated from a trusted source?
3. Can input influence SQL, tool calls, shell, filesystem or network access?
4. Does private prompt/output/state or secret material cross a boundary?
5. Are sizes, tokens, concurrency, retries and wall time bounded?
6. Does failure become an explicit error instead of a safe verdict?
7. Are ledger hashes recomputed, signatures checked and chain links verified?
8. Are isolation claims backed by real container/network tests?
9. Are dependencies justified and locked?
10. Are secrets absent from logs, prompts, fixtures and Git?

Classify findings Critical/High/Medium/Low. Fix scoped, clear defects and add regression tests. Source review alone is not a complete security audit.
