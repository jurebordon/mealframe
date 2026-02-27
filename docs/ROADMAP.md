# Roadmap

**Last Updated**: 2026-02-27
**Current Phase**: Phase 2 — Feature Expansion & Multi-User

## Now (Current Work)

<!-- ONE task in progress at a time -->

| Feature | ADR | Branch | Sessions | Status |
|---------|-----|--------|----------|--------|
| Authentication & multi-user | ADR-014 | `feat/auth` | 1 of ~5 done | Session 1 complete: backend auth endpoints + JWT + tests |

**Remaining auth sessions:**
- Session 2: Data migration — add `user_id` to all existing tables, backfill seed data, make NOT NULL
- Session 3: Protect all existing routes, update services to filter by `user_id`
- Session 4: Frontend — auth pages, auth context, protected routes, API client token handling
- Session 5: Email verification, password reset, Google OAuth, settings page, rate limiting

## Next (Queued)

<!-- Priority ordered - top item is next -->

**Phase 2 — Wave 3 (after auth):**

| Feature | ADR | Branch | Sessions | Depends on |
|---------|-----|--------|----------|------------|
| AI ad hoc meal capture (image MVP) | ADR-013 | `feat/ai-capture` | ~4 (pipeline+be+fe+storage) | ADR-012 (`deviated` entry point), ADR-014 (usage metering) |

**Phase 2 — Wave 4:**

- Grocery list generation (ADR-008) — Most requested feature for personal use

## Later (Backlog)

<!-- Ideas and future work, not prioritized -->
- AI meal capture Phase 2: voice dictation via Whisper (ADR-013 Phase 2)
- Push notification reminders (requires native app consideration)
- Adherence-weighted round-robin (deprioritize skipped meals)
- Watch complications for "next meal"
- Template export/import for sharing
- Public template library

## Done (Recent)

<!-- Recently completed, for context -->
- [x] Privacy policy page for waitlist landing (2026-02-25)
- [x] Track C: Waitlist landing page + self-hosted pageview analytics (2026-02-25)
- [x] Fix: MealPicker empty state (page_size 422), iOS keyboard overlap, sheet resizing (2026-02-24)
- [x] Track A: Revised completion statuses — ADR-012 (backend + frontend + stats) (2026-02-23)
- [x] Track B: Per-slot meal reassignment — ADR-011 (backend + frontend) (2026-02-23)
- [x] ADR-011 through ADR-014 written — Phase 2 feature planning (2026-02-20)
- [x] Fix: Card text selection on tap — added select-none to Card component (2026-02-20)
- [x] Soft limits frontend: template editor limits, list previews, Stats over-limit card + breakdown (2026-02-18)
- [x] Fix: test_weekly_api.py MultipleResultsFound due to seed data conflict (2026-02-18)
- [x] Soft limits backend: migration, CRUD, over-limit stats calculation (2026-02-18)
- [x] Fix: Streak inconsistency between Today View and Stats page (2026-02-18)
- [x] Ad-hoc meals frontend: MealPicker, Add Meal button, ad-hoc indicators, remove flow (2026-02-18)
- [x] Ad-hoc meals backend: is_adhoc column, POST /today/slots, DELETE /slots/{id} (2026-02-12)
- [x] Fix: Swipe cascading bug, clear status, meal ordering, sheet cutoff (2026-02-09)
- [x] Extended macro display + daily totals + avg daily stats (2026-02-08)
- [x] CSV import: auto-create missing meal types (2026-02-07)
- [x] "Yesterday Review" modal on morning open (2026-02-03)
- [x] Enable SSH-based auto-deployment from GitHub Actions (2026-02-02)
- [x] Homelab deployment to Proxmox VM with NPM reverse proxy and SSL (2026-02-02)
- [x] Fix backend API connectivity through NPM (expose API port 8003, configure proxy) (2026-02-02)
- [x] Configure split DNS in OPNsense to avoid DNS rebind warnings (2026-02-02)
- [x] Fix: Undo action for completed meals (tap to change status, "Current" badge) (2026-02-01)
- [x] Template picker modal mobile UX (fullscreen, scroll prevention, "No Plan" visible) (2026-01-30)
- [x] Week selector with navigation (arrow-based week switching, smart regeneration) (2026-01-30)
- [x] Deployment setup (Docker Compose production config, Nginx, multi-stage builds) (2026-01-30)
- [x] End-to-end testing with Playwright (daily flows, weekly generation, offline) (2026-01-27)
- [x] Build Stats view (adherence, streaks, daily chart, meal type breakdown) (2026-01-27)
- [x] Implement offline support (service worker, cache strategy, completion sync) (2026-01-26)
- [x] Build Setup screens (Meal Types, Day Templates, Week Plans) with full CRUD (2026-01-26)
- [x] Build Meals Library with full CRUD, search, and type filtering (2026-01-26)
- [x] Implement CSV meal import functionality (2026-01-26)
- [x] Build Week View with API integration and template switching (2026-01-26)
- [x] Seed initial data (Meal Types, Day Templates, Week Plan, Sample Meals) (2026-01-26)
- [x] Build Today View with API integration and completion flow (2026-01-26)
- [x] Set up frontend foundation with v0 design system (2026-01-24)
- [x] Build API endpoints for weekly planning (generate, template switching) (2026-01-24)
- [x] Build API endpoints for daily use (GET /today, POST /slots/{id}/complete) (2026-01-24)
- [x] Build Pydantic schemas for API requests/responses (2026-01-24)
- [x] Implement round-robin meal selection algorithm (2026-01-22)
- [x] Implement database schema and migrations (Alembic) (2026-01-20)
- [x] Set up backend foundation (FastAPI + PostgreSQL + Docker) (2026-01-20)
- [x] Set up project structure and development environment (2026-01-19)
- [x] Created PRD and Tech Spec (2026-01-19)
- [x] Initialized SpecFlow documentation structure (2026-01-19)

## Blockers

<!-- Anything preventing progress -->
(none)

---

## Dependency Graph

```
Wave 1:
  ✅ Track A: ADR-012 (Completion Statuses) ── merged
  ✅ Track B: ADR-011 (Meal Reassignment) ──── merged
  ✅ Track C: Waitlist Page + Analytics ──────── merged

Wave 2 (after Wave 1):
  └─→ ADR-014 (Auth) ──────────────────────────────┐
       users table → middleware → data migration    │
       → frontend auth → settings page             │
                                                    │
Wave 3 (after auth):                                │
       ADR-013 (AI Capture) ◄───────────────────────┘
       needs: ADR-012 (deviated status) ✅
       needs: ADR-014 (usage metering)
```

## Notes

- Tasks should be small enough to complete in 1-2 sessions
- Move items between sections as priorities change
- Add blockers immediately when encountered
- Reference tasks by ID in SESSION_LOG entries
- MVP scope defined in docs/frozen/PRD_v0.md
- PRDs for Phase 2 features in docs/frozen/features/

---

## Design Assets

Pre-built v0 design system in `v0_design/` folder:

| Resource | Path | Description |
|----------|------|-------------|
| Design prompts | `docs/frozen/V0_DESIGN_PROMPTS.md` | Prompts used to generate v0 designs |
| Apple HIG audit | `docs/frozen/V0_APPLE_COMPLIANCE_PROMPT.md` | Apple Human Interface Guidelines compliance |
| Components (79) | `v0_design/components/` | Radix UI primitives + MealFrame components |
| MealFrame components | `v0_design/components/mealframe/` | Domain-specific: MealCard, CompletionSheet, etc. |
| UI primitives | `v0_design/components/ui/` | Button, Card, Sheet, Dialog, etc. |
| Navigation | `v0_design/components/navigation/` | AppShell, BottomNav, Sidebar |
| Landing page | `v0_design/app/(landing)/` | Waitlist page + form component |
| Pages | `v0_design/app/(app)/` | Today, Week, Library, Stats, Settings |
| Global styles | `v0_design/app/globals.css` | Tailwind config with design tokens |

**Usage**: Copy components and styles from `v0_design/` into `frontend/` when implementing UI features. Adapt imports and connect to real API data.
