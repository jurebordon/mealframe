# Development Workflow

> How to work on this repository - for humans and AI assistants.

## Documentation Layers

| Layer | Documents | Change Frequency |
|-------|-----------|------------------|
| **Strategic** | VISION.md, ADR.md | Rarely (pivots, major decisions) |
| **Tactical** | OVERVIEW.md, ROADMAP.md, WORKFLOW.md | Per milestone/feature |
| **Operational** | SESSION_LOG.md, .claude/skills/* | Every session |
| **Frozen** | feature_docs/*/SPEC.md | Never (feature north star) |

## Session Lifecycle

### Before Starting Work

- [ ] Read `ROADMAP.md` - pick ONE task from Now/Next
- [ ] Read last 3 entries in `SESSION_LOG.md`
- [ ] Check `ADR.md` for relevant decisions
- [ ] Run `/plan-session` or read the plan prompt

### During Work

- [ ] Create feature branch: `feat/description`
- [ ] Stay within scope of chosen task
- [ ] Commit frequently with clear messages
- [ ] Note any decisions made for later documentation

### After Work

- [ ] Run tests: `cd backend && pytest` and `cd frontend && npm run lint`
- [ ] Update `ROADMAP.md` (mark done, adjust Next)
- [ ] Append entry to `SESSION_LOG.md`
- [ ] If architecture changed: update `OVERVIEW.md` and/or `ADR.md`
- [ ] Merge feature branch to main locally

## Git Workflow

### Solo Developer Flow

```
main ←── feature/branch
         └── merge when tests pass
```

- Branch from main: `git checkout -b type/description`
- Work and commit on branch
- When done: merge directly to main locally
- Branch naming: `feat/`, `fix/`, `refactor/`, `docs/`



## Documentation Update Rules

### Always Update (every session)

- `SESSION_LOG.md` - Prepend new entry with session summary

### Update When Changed

| Document | Update When |
|----------|-------------|
| `ROADMAP.md` | Tasks complete, priorities change |
| `OVERVIEW.md` | System architecture changes |
| `ADR.md` | Significant technical decision made (append only) |
| `VISION.md` | Product direction pivots |
| `WORKFLOW.md` | Process changes |

### Never Update

- `feature_docs/*/SPEC.md` - Feature north star (frozen after creation)

## Metrics Policy

**No manual metrics.** Do not track:
- Test counts
- Coverage percentages
- Lines of code
- Velocity numbers

If metrics are needed, they must be:
- Generated automatically by CI/scripts
- Stored in auto-generated artifacts (not hand-edited docs)

## Session Commands

| Command | When to Use |
|---------|-------------|
| `/plan-session` | Before starting work |
| `/start-session` | Beginning implementation |
| `/end-session` | Wrapping up, merging |
| `/pivot-session` | Reassessing direction |

Skills are in `.claude/skills/` ([Agent Skills](https://agentskills.io) standard, also output to `.codex/skills/`).

## Quick Reference

```bash
# Start work
git checkout main && git pull
git checkout -b feat/my-feature
# ... code ...

# End work
cd backend && pytest && cd ../frontend && npm run lint
git add . && git commit -m "feat: description"
git checkout main && git merge feat/my-feature && git branch -d feat/my-feature
```

## Getting Help

- Architecture questions → Check `ADR.md`, then ask
- Current priorities → Check `ROADMAP.md`
- Recent context → Check `SESSION_LOG.md`
- System understanding → Check `OVERVIEW.md`
