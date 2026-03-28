# Documentation

> Follow these conventions for all documentation updates.

## File Locations

- All documentation lives in `docs//`. Do not create documentation files outside this directory.
- Feature-specific docs go in `docs//feature_docs/<feature-name>/`.

## ROADMAP.md

- Update `docs//ROADMAP.md` immediately when a task changes status.
- Tag every task with `[feature: name]`. Untagged tasks will not be filtered correctly.
- Check the box `[x]` when a task is complete. Move it to the "Done" section with a date.
- Add new tasks or blockers discovered during implementation.

## SESSION_LOG.md

- Prepend a new entry to `docs//SESSION_LOG.md` at the end of every session.
- Use the heading format: `## [feature-name] YYYY-MM-DD`.
- Include: task, summary, files changed, decisions, blockers, next steps.
- Keep entries concise. Focus on decisions made, not keystrokes.

## Frozen Documents

These documents have restricted editing rules:

- **VISION.md**: Do not modify without explicit user approval.
- **SPEC.md** (requirements sections): Requirements are frozen once approved. Add notes or updates in the "Implementation Decisions" section only.
- **ADR.md**: Append-only. Never edit or delete existing entries. Add new entries at the top when architectural decisions are made.

## When to Update

| Event | Update |
|-------|--------|
| Task completed | `docs//ROADMAP.md` |
| Session ends | `docs//SESSION_LOG.md` |
| Architecture changes | `docs//OVERVIEW.md` |
| Design decision made | `docs//ADR.md` |
| New feature planned | `docs//feature_docs/<name>/SPEC.md` |

## General Rules

- Write for the next session. Assume the reader has no context from this session.
- Use feature tags consistently. Mismatched tags break filtering.
- Do not duplicate information across documents. Reference other docs instead.
- Keep documentation factual. No aspirational language or vague plans.
