---
name: new-worktree
description: >-
  Set up a git worktree for parallel feature development. Creates a sibling
  directory with a new branch for working on independent features simultaneously.
  Only use when working on multiple independent features.
compatibility: Works with Claude Code, Codex CLI, and other Agent Skills-compatible tools
metadata:
  author: specflow
---
# New Worktree

> **Advanced option** for parallel feature development. Use only when working on multiple independent features simultaneously.

---

## Warning

Worktrees add complexity. Only use them if:
- You have 2+ independent features in progress
- Features have no dependencies on each other
- You need to switch between them frequently (reviews, blockers, priorities)

If unsure, stick with regular branches.

---

## Step 1: Confirm Feature

Ask: "What feature should this worktree be for?"

If not already clear:
- Feature name (kebab-case, e.g., `user-auth`, `api-v2`)
- Does `/new-feature` need to be run first to create the feature?
- Is there an existing branch, or create new one?

---

## Step 2: Verify Prerequisites

Check current state:
```bash
# Ensure we're in the main worktree
git worktree list

# Ensure main is up to date
git checkout main
git pull origin main
```

---

## Step 3: Create Worktree

```bash
# Create worktree with new branch
git worktree add ../meal-planner- -b feat/description/

# Or from existing branch
git worktree add ../meal-planner- feat/description/
```

Worktree location: `../meal-planner-`

---

## Step 4: Set Up Feature (if needed)

```bash
cd ../meal-planner-
```

If feature doesn't exist yet, run `/new-feature ` to create:
- `docs_specflow/feature_docs//SPEC.md`
- Tasks in `docs_specflow/ROADMAP.md` with `[feature: ]` tags

---

## Step 5: Summarize

Provide summary:

```
Worktree created: 

**Location**: ../meal-planner-
**Branch**: feat/description/

**To work on this feature**:
  cd ../meal-planner-
  /plan-session  # AI will detect feature from branch name

**To switch back to main**:
  cd ../meal-planner

**Other worktrees**:
  git worktree list

**When done**:
  git worktree remove ../meal-planner-
```

---

## How Feature Detection Works

When you run `/plan-session` in a worktree:
1. AI detects branch name (e.g., `feat/user-auth`)
2. Extracts feature name (`user-auth`)
3. Filters ROADMAP.md for tasks tagged `[feature: user-auth]`
4. Prefixes SESSION_LOG entries with `[user-auth]`

No special configuration needed - it just works.

---

## Notes

- Worktree directory is sibling to main repo (not inside it)
- Each worktree has its own working directory but shares git history
- Feature docs (`docs_specflow/`) are shared across all worktrees
- Tasks use `[feature: name]` tags in central ROADMAP.md
- Sessions use `[feature-name] YYYY-MM-DD` format in central SESSION_LOG.md
- Clean up after merge: `git worktree remove ../meal-planner-`
