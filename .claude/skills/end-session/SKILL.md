---
name: end-session
description: >-
  Wrap up a development session. Runs final tests, updates ROADMAP (marks tasks
  complete), logs session in SESSION_LOG, commits changes, and creates PR or
  merges to main. Use when done coding.
compatibility: Works with Claude Code, Codex CLI, and other Agent Skills-compatible tools
metadata:
  author: specflow
---
# End Session

> Wrap up implementation: test, document, commit, merge/PR.

---

## Step 1: Final Tests

Verify everything works:
```bash
# Backend tests
cd backend && pytest

# Frontend lint/build check
cd frontend && npm run lint && npm run build
```

Fix any failures before proceeding.

**Optional quality reviews** (consider for significant changes):

If you have specialist agents installed in `.claude/agents/`, run applicable reviews in **parallel** using the `Task` tool:

| When to use | Look for an agent that... |
|-------------|--------------------------|
| Added substantial code | Specializes in testing/QA — ask it to review test coverage and suggest missing cases |
| Changed auth, data handling, or secrets | Specializes in security auditing — ask it to review for OWASP top 10, secrets, injection |
| Large implementation or refactor | Specializes in refactoring — ask it to review for dead code, unnecessary complexity |

These reviews are advisory — they report findings for you to act on before committing.

---

## Step 2: Update ROADMAP

Edit `docs_specflow/ROADMAP.md`:

1. **Mark task complete**: Check the box for completed task
2. **Move to Done**: If "Now" section is cluttered, move completed items to "Done" with date
3. **Add blockers**: If you discovered new issues, add them

Example:
```markdown
## Now
- [x] Add login endpoint [feature: user-auth]  ← Check this
- [ ] Add password reset [feature: user-auth]

## Done
- [x] Add login endpoint [feature: user-auth] - 2026-01-20
```

---

## Step 3: Log Session

Prepend entry to `docs_specflow/SESSION_LOG.md`:

```markdown
## [] 2026-03-17

**Task**: [Task description from ROADMAP]
**Branch**: 

### Summary
- [What was accomplished]

### Files Changed
- [List key files modified]

### Decisions
- [Design decisions made, or "None"]

### Blockers
- [Issues encountered, or "None"]

### Next
- [Suggested next task]

---
```

---

## Step 4: Update Architecture Docs (If Needed)

Only if significant changes occurred:

**docs_specflow/SPEC.md** (feature-specific):
- Update "Implementation Decisions" section
- Move resolved items from "Open Questions"

**docs_specflow/ADR.md** (project-wide):
- Add entry if major architectural decision was made

**docs_specflow/OVERVIEW.md**:
- Update if system architecture changed

---

## Step 5: Commit All Changes

```bash
git status
git add .
git commit -m "feat|fix|refactor|docs: [description]



Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Step 6: Merge or Create PR

### Solo Workflow - Merge to Main

```bash
git checkout main
git pull origin main
git merge 
git push origin main
git branch -d 
```



---

## Step 7: Session Summary

Provide brief summary to user:

```
Session complete!

**Accomplished**: [1-2 sentences]
**Files changed**: [count] files
**Tests**: Passing ✓
**Next**: [Suggested next task from ROADMAP]
```

---

## Notes

- Always update ROADMAP and SESSION_LOG
- Keep session logs concise - key decisions only
- Feature tags help track work across worktrees
- Test before committing, always
- Check `docs_specflow/CUSTOM.md` for project-specific commit conventions or PR templates
