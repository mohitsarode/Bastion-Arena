---
trigger: always_on
description: "Security invariants for every Bastion Arena change."
---

# Security Invariants

- The Arbiter is the security control plane; agents are not the boundary.
- Only synthetic/local authorized targets are in scope.
- No direct Red-to-Blue, Red-to-MUT, Blue-to-Red, or Blue-to-MUT path.
- Do not expose provider keys, signing keys, raw Blue diagnostics, evaluator prompt/rationale, or raw MUT output to Red.
- Enforce trusted role, tenant, capability, phase, size, time and budget checks server-side.
- Ledger verification must recompute canonical event hashes, verify signatures, and check previous-hash links.
- Shadow execution and latency bucketing reduce specific observables; they do not prove timing leakage is eliminated.
- Mark controls as implemented/tested/planned/residual risk. Never fabricate results.
- An evaluation or evidence failure must not become a safe verdict.
- Do not mount Docker socket or secrets into untrusted containers.
