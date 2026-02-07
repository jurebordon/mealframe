# Roadmap

**Last Updated**: 2026-02-04
**Current Phase**: MVP Complete - Evaluating Phase 2

## Now (Current Work)

<!-- ONE task in progress at a time -->

## Next (Queued)

<!-- Priority ordered - top item is next -->
**Quick Fixes:**
- CSV import: auto-create missing meal types (currently skips with warning)

**Choose one to begin Phase 2:**
- User management and authentication (ADR-009) - Required to expose app to other users
- Grocery list generation (ADR-008) - Most requested feature for personal use

## Later (Backlog)

<!-- Ideas and future work, not prioritized -->
- Push notification reminders (requires native app consideration)
- Grocery list generation from weekly plan
- Ingredient-based meal builder with macro calculation
- Adherence-weighted round-robin (deprioritize skipped meals)
- Watch complications for "next meal"
- Template export/import for sharing
- Multi-user support with authentication
- Public template library

## Done (Recent)

<!-- Recently completed, for context -->
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
- None

---

## Notes

- Tasks should be small enough to complete in 1-2 sessions
- Move items between sections as priorities change
- Add blockers immediately when encountered
- Reference tasks by ID in SESSION_LOG entries
- MVP scope defined in docs/frozen/PRD_v0.md
- Out-of-scope features deferred to "Later" section

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
| Pages | `v0_design/app/` | Today, Week, Library, Stats, Settings |
| Global styles | `v0_design/app/globals.css` | Tailwind config with design tokens |

**Usage**: Copy components and styles from `v0_design/` into `frontend/` when implementing UI features. Adapt imports and connect to real API data.
