---
name: new-feature
description: >-
  Create a new feature with SPEC document and ROADMAP tasks. Gathers feature
  information, creates a frozen feature SPEC in feature_docs/, adds tagged tasks
  to ROADMAP, and optionally creates a feature branch.
compatibility: Works with Claude Code, Codex CLI, and other Agent Skills-compatible tools
metadata:
  author: specflow
---
# New Feature

> Create a new feature SPEC and add tasks to central ROADMAP.

---

## Step 1: Gather Feature Information

Ask the user:

1. **Feature name?** (kebab-case, e.g., `user-auth`, `api-v2`, `payment-integration`)

2. **What is this feature?**
   - Brief description
   - Why is it needed?
   - Target users or use cases

3. **What are the requirements?**
   - Key functionality
   - Inputs and outputs
   - Dependencies on existing code

4. **Success criteria?**
   - How will we know it's done?
   - What tests or validations?

5. **Ticket reference?** (optional)
   -  reference
   - External link if applicable

If user provides a spec document, PRD, or ticket, use that information.

---

## Step 2: Create Feature SPEC

Create `docs_specflow/feature_docs//SPEC.md`:

```markdown
# Feature: 

> Frozen north star for this feature.

---

## Requirements (Frozen)

### Overview
[What this feature does and why it exists]

### User Stories
- As a [user type], I want [goal] so that [benefit]

### Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

### Out of Scope
[What this feature explicitly does NOT include]

---

## Implementation Decisions

> Document decisions as you build. Major changes → also add to central ADR.md

### Technical Approach
[High-level approach - to be filled during implementation]

### Key Decisions
- **[Decision]**: [Rationale]

---

## Dependencies

### Upstream
[Features or systems this depends on]

### Downstream
[Features or systems that depend on this]

---

## Success Criteria

### Functional
- [ ] [Measurable criterion]

### Non-Functional
- [ ] Performance: [metric]
- [ ] Security: [requirement]

---

## Open Questions

- [ ] [Unresolved question 1]
- [ ] [Unresolved question 2]

---

*Created*: 2026-03-17
```

---

## Step 3: Add Tasks to Central ROADMAP

Update `docs_specflow/ROADMAP.md`:

Break feature into tasks and add to appropriate section (Now/Next/Later):

```markdown
## Now
- [ ] [First task for ] [feature: ]

## Next
1. [Second task for ] [feature: ]
2. [Third task for ] [feature: ]
```

**Important**: Every task MUST have `[feature: ]` tag.

---

## Step 4: Create Feature Branch (if needed)

Optional: Create feature branch
```bash
git checkout -b feat/description/
```

---

## Step 5: Summarize

Provide summary to user:

```
Feature created: 

**Created**:
- docs_specflow/feature_docs//SPEC.md

**Updated**:
- docs_specflow/ROADMAP.md (added tasks with [feature: ] tags)


**Next Steps**:
1. Review SPEC.md and confirm requirements
2. Run `/plan-session` to start working on first task
   - AI will automatically filter ROADMAP for [feature: ] tasks
3. Or manually update ROADMAP.md with more detailed tasks

**Working on this feature**:
- All your sessions will be tagged with [feature: ] in SESSION_LOG.md
- All tasks should have [feature: ] tag in ROADMAP.md
- Update SPEC.md as decisions are made during implementation
```

---

## Notes

- Feature name should be kebab-case
- SPEC.md is the frozen north star - requirements shouldn't change often
- Implementation decisions get added to SPEC.md as you build
- Major decisions also go in central ADR.md
- Tasks live in central ROADMAP.md with feature tags
- Sessions live in central SESSION_LOG.md with feature tags
