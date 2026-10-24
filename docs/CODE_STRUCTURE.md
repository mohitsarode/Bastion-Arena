# Recommended Code Structure

Use `src/` layout. Do not create every empty file up front; add modules as milestones require them. If the current workspace already has a good structure, inspect and adapt it rather than replacing it destructively.

```text
bastion-arena/
├── AGENTS.md
├── PRD.md
├── ARCHITECTURE.md
├── DATABASE.md
├── API.md
├── SECURITY_MODEL.md
├── TESTING.md
├── IMPLEMENTATION_PLAN.md
├── DECISIONS.md
├── config.yaml
├── .env.example
├── .gitignore
├── pyproject.toml
├── src/bastion_arena/
│   ├── __init__.py
│   ├── main.py
│   ├── api/                 # health, rounds, cases, evidence
│   ├── core/                # config, schemas, state machine, budgets, errors
│   ├── agents/
│   │   ├── red/             # agent, prompt, mutations
│   │   ├── blue/            # agent, scanners, redaction
│   │   └── evaluator/       # agent, prompt, rubric
│   ├── providers/           # protocol, fake, OpenAI-compatible client
│   ├── services/            # case/round/orchestrator services
│   ├── ledger/              # canonicalization, chain, signing, verifier
│   ├── storage/             # SQLite schema and repositories
│   ├── security/            # identity, authorization, replay defense
│   └── tool_gateway/        # policy and synthetic fake tools
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── fixtures/
├── scripts/                 # smoke test, ledger verifier
├── infra/                   # Dockerfiles, Compose, seccomp
├── docs/reference/          # immutable input specifications
├── docs/REFERENCE_INDEX.md
└── .agents/
    ├── rules/
    ├── skills/<skill-name>/SKILL.md
    └── workflows/
```
