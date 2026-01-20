# Roadmap

**Last Updated**: 2026-01-20
**Current Phase**: MVP - Foundation

## Now (Current Work)

<!-- ONE task in progress at a time -->
- [ ] Implement database schema and migrations (Alembic)

## Next (Queued)

<!-- Priority ordered - top item is next -->
1. Build core data models (Meal, MealType, DayTemplate, WeekPlan)
2. Implement round-robin meal selection algorithm
3. Build API endpoints for daily use (GET /today, POST /slots/{id}/complete)
4. Build API endpoints for weekly planning (generate, template switching)
5. Set up frontend foundation (Next.js + PWA)
6. Build Today View (mobile-first, primary screen)
7. Build completion tracking UI with status selection
8. Implement CSV meal import functionality
9. Build Week View (overview and template switching)
10. Build Meals Library (CRUD for meals)
11. Build Setup screens (Meal Types, Day Templates, Week Plans)
12. Implement offline support (service worker, cache strategy)
13. Build Stats view (adherence, streaks)
14. Seed initial data (Meal Types, Day Templates, Week Plan)
15. End-to-end testing (daily flows, weekly generation)
16. Deployment setup (Docker Compose production config)

## Later (Backlog)

<!-- Ideas and future work, not prioritized -->
- "Yesterday Review" modal on morning open
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
