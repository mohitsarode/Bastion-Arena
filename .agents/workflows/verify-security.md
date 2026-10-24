---
title: Verify Security Controls
description: Runs a scoped security review against documented trust boundaries and evidence-integrity controls.
---

1. Read `SECURITY_MODEL.md`, `ARCHITECTURE.md`, `API.md` and `TESTING.md`.
2. Inspect implementation before asserting a control exists.
3. Run existing security tests; add missing scoped regression tests.
4. Test both permitted and forbidden paths.
5. Recompute ledger hashes from canonical fields; verify signatures and chain continuity.
6. Inspect Compose for privileged mode, host networking/PID, Docker socket, secret mounts and absent resource limits.
7. Use only local containers and synthetic canary data; no destructive external tests.
8. Report severity and distinguish implemented/tested/planned/residual risk.
