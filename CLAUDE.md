# MealFrame

> This file provides context for AI assistants working on this project.

## Project Overview

Meal planning app that eliminates decision fatigue with authoritative, pre-planned meals with exact portions and automated round-robin rotation.

## Quick Context

- **Type**: adoption
- **Stack**: FastAPI (Python) + Next.js 14+ (React/TypeScript) + PostgreSQL 15+
- **Git Workflow**: solo (direct merge to main)

## Documentation

Read these before making changes:

| Priority | Document | Purpose |
|----------|----------|---------|
| 1 | [ROADMAP.md](docs/ROADMAP.md) | Current tasks and priorities |
| 2 | [SESSION_LOG.md](docs/SESSION_LOG.md) | Recent session history |
| 3 | [OVERVIEW.md](docs/OVERVIEW.md) | System architecture |
| 4 | [ADR.md](docs/ADR.md) | Architecture decisions |
| 5 | [VISION.md](docs/VISION.md) | Product direction |
| 6 | [LEARNED_PATTERNS.md](docs/LEARNED_PATTERNS.md) | Discovered patterns and conventions |
| 7 | [AGENTS.md](docs/AGENTS.md) | Agent orchestration guide |

> **LEARNED_PATTERNS.md**: Append codebase patterns, anti-patterns, and conventions you discover during sessions. The continuous-learning hook will periodically remind you to capture insights. Check this file at session start to avoid re-discovering known patterns.

## Session Commands

Use these commands to structure your work:

- `/plan-session` - Prepare for implementation
- `/start-session` - Begin coding
- `/end-session` - Wrap up and merge
- `/verify` - Validate docs consistency and project health

Skills are in `.claude/skills/` ([Agent Skills](https://agentskills.io) standard, also output to `.codex/skills/`).

## Technical Enforcement

### Hooks (`.claude/hooks/`)
Automated behaviors at session lifecycle points:
- **SessionStart**: Auto-loads ROADMAP, SESSION_LOG, and feature SPEC into context
- **PreToolUse**: Blocks edits to frozen docs (VISION.md, SPEC.md requirements)
- **PostToolUse**: Auto-formats code after edits, suggests /compact at high context usage, reminds to capture learned patterns, suggests specialist agents based on changed files
- **Stop**: Reminds to push unpushed commits
- **SessionEnd**: Saves session state snapshot for continuity

### Rules (`.claude/rules/`)
Always-loaded coding guidelines:
- `coding-style.md` — Language-specific style and patterns
- `git-workflow.md` — Branch, commit, and merge conventions
- `security.md` — Secret protection and secure coding
- `testing.md` — Test commands and quality standards
- `documentation.md` — SpecFlow documentation conventions

### Statusline
Real-time display: context usage %, current feature, TODO progress, git status.

## Agents

Install specialist agents in `.claude/agents/` for focused expertise during implementation.
Recommended: [VoltAgent community agents](https://github.com/VoltAgent/awesome-claude-code-subagents) — 100+ battle-tested agents for backend, frontend, security, architecture, and more.

See [AGENTS.md](docs/AGENTS.md) for orchestration patterns and installation instructions.

## Key Patterns

### Backend (FastAPI/Python)
- Route handlers in `backend/app/api/` → service functions in `backend/app/services/` → SQLAlchemy models in `backend/app/models/`
- All services accept `user_id: UUID` as first param; all queries filter by user_id
- Pydantic schemas in `backend/app/schemas/` — `Decimal` fields serialize as strings in JSON; wrap with `Number()` in frontend
- Alembic migrations in `backend/alembic/versions/` — naming: `YYYYMMDD_description.py`
- Tests override `get_current_user` via `app.dependency_overrides` — never use real JWT in tests
- pytest with asyncio_mode=auto; run with `cd backend && pytest`

### Frontend (Next.js/React)
- Route groups: `(app)` for authenticated app, `(auth)` for login/register, `(landing)` for public pages
- Auth state in Zustand (`auth-store.ts`), access token in memory only (not localStorage)
- API calls via `fetchApi()` in `lib/api.ts` — handles Bearer token injection and 401 refresh retry
- `Number()` wrapping required for all Pydantic `Decimal` fields from API (protein_g, fat_g, etc.)
- Page size for `/meals` max is 100 (backend hard limit); always use `pageSize: 100` or less
- iOS Safari: file input `.click()` must be synchronous in a user gesture handler (`forwardRef` + `useImperativeHandle` pattern)

## Invariants

These rules must always hold:

- **All API endpoints require authentication** — `get_current_user` dependency on all routes; `user_id` scopes all queries
- **Portion descriptions are mandatory** — Every meal must have exact portions (e.g., "2 eggs + 1 slice toast")
- **Round-robin is deterministic** — Same inputs always produce same meal assignments; meals ordered by `(created_at ASC, id ASC)`
- **Completion tracking is optional** — Unmarked meals are valid, not errors
- **Mobile-first Today View** — Must load from offline cache; completion actions work without network

## Git Workflow

- Work on feature branches: `feat/description`, `fix/description`, etc.
- Merge directly to main when tests pass (solo workflow)
- Delete branches after merging

## Working Agreements

1. **One task per session** - Don't mix unrelated changes
2. **Update docs** - SESSION_LOG.md after every session, ROADMAP.md when tasks change
3. **Ask when unclear** - Don't invent requirements
4. **No manual metrics** - Automated or nothing

## Getting Started

1. Run `/plan-session` to see current priorities
2. Pick ONE task from ROADMAP.md
3. Run `/start-session` to begin
4. When done, run `/end-session`

---

*This project uses [SpecFlow](https://github.com/jurebordon/specflow) for AI-assisted development.*
