# Antigravity Prompt Sequence

Use one prompt at a time. Do not paste all phases together.

## Prompt 2 — Implement M1 after M0 is reviewed

M0 documentation audit is approved. Implement **M1 only** from `IMPLEMENTATION_PLAN.md`.

Before editing, inspect Git status and the current repository. Do not delete or rewrite original references. Follow `AGENTS.md` and the canonical project documents. Create the `src/` package foundation, `pyproject.toml`, validated configuration loading, typed base contracts, standard error types, structured logging, and a deterministic fake provider. Add a minimal health endpoint only if it is part of M1. Do not implement Red/Blue/Evaluator orchestration, Docker isolation, external API calls, dashboard, or cloud credentials yet.

Add unit tests for configuration precedence, invalid configuration, schema bounds, importability and fake-provider determinism. Run the required checks in `AGENTS.md`. Keep the project runnable with no API key and no network access. Update `IMPLEMENTATION_PLAN.md` and `docs/PROJECT_STATUS.md` with only verified results. Stop after M1 and report changed files, commands actually run, test results and outstanding decisions.

## Prompt 3 — Implement the next approved phase

Use `.agents/workflows/implement-next-phase.md` (or invoke `/implement-next-phase` if discovered). Implement only the first incomplete milestone in `IMPLEMENTATION_PLAN.md`. Do not skip phases or continue into the next milestone after the current one is complete.

## Prompt 4 — Run a focused security review

Use `.agents/workflows/verify-security.md` (or invoke `/verify-security` if discovered). Inspect the current code before asserting controls. Run only safe, local tests against synthetic fixtures and the local Compose topology. Report severity, evidence, exact commands, and residual risks. Do not claim a full security audit from code review alone.

## Prompt 5 — Debug a failing task

Follow `.agents/skills/test-and-verify/SKILL.md`. Reproduce the failure, trace the root cause, make the smallest correct fix, add a regression test, rerun the relevant tests, and report the result. Do not weaken validation or remove tests to make the build pass.
