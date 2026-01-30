# Session Log

> Append-only journal of development sessions. Newest entries first.
> Each session gets one entry - prepend new entries at the top.

---

## Session: 2026-01-30 (12)

**Role**: frontend
**Task**: Fix template picker modal UX on mobile (scroll bleed-through, "No Plan" option hidden)
**Branch**: fix/template-picker-mobile-ux

### Summary
- Made template picker fullscreen on mobile (< 768px viewport)
- Added body scroll lock when modal is open to prevent scroll bleed-through
- Ensured "No Plan" option is always visible without scrolling
- Added close button with aria-label for accessibility
- Desktop behavior unchanged (centered modal with max-h-85vh)
- Content area uses flex-1 on mobile, fixed max-height on desktop
- Confirmation screen also uses fullscreen layout on mobile

### Files Changed
**Frontend (modified):**
- [frontend/src/components/mealframe/template-picker.tsx](frontend/src/components/mealframe/template-picker.tsx) - Fullscreen mobile modal, body scroll lock, improved layout

### Implementation Details
- Used `useIsMobile()` hook to detect viewport < 768px
- Added `useEffect` to lock/unlock body scroll based on modal open state
- Modal height changes from `h-full` (mobile) to `max-h-[85vh]` (desktop)
- Modal animation changes from slide-up on mobile to fade-in on desktop
- Content area is `flex-1` on mobile to fill available space and ensure "No Plan" is visible

### Decisions
- Kept custom modal implementation instead of switching to Drawer component (vaul)
- Body scroll lock implemented directly rather than relying on library
- Fullscreen on mobile provides maximum content visibility and prevents scroll issues
- Desktop retains centered modal for better desktop UX

### Testing Performed
- Frontend build passes with no TypeScript errors
- Manual testing required: verify fullscreen on mobile, scroll lock, "No Plan" visibility
- E2E tests not run (backend database connection issues unrelated to this change)

### Status: COMPLETE

---

## Session: 2026-01-30 (11)

**Role**: fullstack
**Task**: Week selector with navigation (arrow-based week switching, smart regeneration)
**Branch**: feat/week-selector

### Summary
- Added week selector component with left/right arrow navigation
- Implemented smart regeneration that preserves completed slots
- Updated GET /weekly-plans/current to accept week_start_date query parameter
- Modified POST /weekly-plans/generate to return 200 for regeneration (201 for new weeks)
- Navigation allows 4 weeks back, unlimited forward
- "Regenerate" button appears for weeks with uncompleted slots
- "Generate Week" appears for weeks without plans

### Files Changed
**Backend (modified):**
- backend/app/api/weekly.py (added week_start_date param, smart regeneration, dynamic status codes)
- backend/app/services/weekly.py (added get_week_instance, regenerate_weekly_plan functions)
- backend/app/services/__init__.py (exported new functions)
- backend/tests/test_weekly_api.py (updated conflict test, added regeneration tests)

**Frontend (new):**
- frontend/src/components/mealframe/week-selector.tsx (arrow navigation component)

**Frontend (modified):**
- frontend/src/app/week/page.tsx (integrated week selector, selected week state)
- frontend/src/hooks/use-week.ts (added useWeek hook with date param)
- frontend/src/lib/api.ts (added getWeek function with date param)

### API Changes
| Endpoint | Change |
|----------|--------|
| GET /weekly-plans/current | Added optional `week_start_date` query param |
| POST /weekly-plans/generate | Returns 201 for new weeks, 200 for regeneration |

### Smart Regeneration Logic
- When generate is called for an existing week, only uncompleted slots are refreshed
- Completed slots (any completion_status) retain their meal assignments
- New meals are assigned via round-robin to uncompleted slots only
- Useful for refreshing meal variety without losing tracking progress

### Decisions
- Used arrow buttons instead of carousel for more explicit navigation
- 4 weeks back limit to keep the scope manageable while allowing history review
- Unlimited future weeks to support planning ahead
- Regeneration preserves all completed slots (not just today's)

### Testing Performed
- 143 backend tests pass (including 4 new weekly API tests)
- Frontend build passes (8 static pages)
- Manual testing: generate, regenerate, navigation, week-by-date fetching

### Status: COMPLETE

---

## Session: 2026-01-30 (10)

**Role**: devops + frontend
**Task**: Deployment setup (Docker Compose production config)
**Branch**: main (direct)

### Summary
- Created multi-stage Dockerfiles for both backend and frontend with dev/prod targets
- Backend prod: gunicorn + uvicorn workers, non-root user, auto-migrations via entrypoint.sh
- Frontend prod: Next.js standalone output for minimal image size
- Added docker-compose.prod.yml with Nginx reverse proxy (routes /api/ to backend, / to frontend)
- Created .env.production.example with required DB_PASSWORD and optional config
- Fixed dev docker-compose.yml to use explicit build targets and env var interpolation
- Tested full production stack locally (all services healthy, API and frontend accessible)
- Debugged mobile access: fixed CORS_ORIGINS and NEXT_PUBLIC_API_URL for LAN access
- Generated current week plan manually (generate endpoint defaults to next week)
- Identified UX improvements for week view: week selector carousel, regenerate functionality

### Files Changed
**New:**
- backend/entrypoint.sh (migrations + gunicorn startup)
- docker-compose.prod.yml (production overrides with Nginx)
- nginx.conf (reverse proxy configuration)
- .env.production.example (production env template)

**Modified:**
- backend/Dockerfile (multi-stage: base → deps → dev/prod)
- backend/requirements.txt (added gunicorn==23.0.0)
- frontend/Dockerfile (multi-stage: base → deps → dev/builder/prod)
- frontend/next.config.js (added output: 'standalone')
- docker-compose.yml (added build targets, env var interpolation for CORS/API_URL)
- docs/ROADMAP.md (updated current task, added UX fixes to Next)
- .gitignore (added v0_design/)

### Decisions
- Used Docker Compose override pattern (base + prod file) rather than separate configs
- Nginx handles routing instead of exposing both services on different ports
- Auto-run migrations in entrypoint for zero-touch deploys
- Environment variables drive all config (GCP-ready)
- Week selector feature deferred to separate session (added to ROADMAP)

### Status: COMPLETE

---

## Session: 2026-01-27 (9)

**Role**: frontend
**Task**: End-to-end testing with Playwright
**Branch**: test/e2e-playwright

### Summary
- Set up Playwright with Chromium in the frontend project
- Created API-driven test helpers that work with existing seed data (reset completions, fetch today/week data, create fixtures)
- Wrote 8 daily flow tests: date header, "Next" indicator, progress ring, completion sheet opening, "Followed" status, sequential completion, "Day Complete" celebration, undo via toast
- Wrote 8 weekly flow tests: day cards with progress, week plan name, "Today" highlight, day expansion, "Generate Next Week" button, template picker modal, template switching, "No Plan" override
- Wrote 3 offline tests: offline banner appears, recovers on reconnect, all routes accessible
- Total: 19 E2E tests, all passing against Docker services

### Decisions
- Used API-driven fixtures instead of shared seed data for test isolation
- Tests reset today's completions via DELETE /slots/{id}/complete before each daily test
- Used `force: true` for modal clicks where backdrop intercepts pointer events
- Offline tests dispatch browser events rather than reload (no service worker in dev mode)
- Filtered E2E fixture templates from template picker assertions to avoid test data pollution

### Files Changed
**Frontend (new):**
- frontend/playwright.config.ts (Playwright configuration)
- frontend/e2e/helpers.ts (API-driven fixture setup and reset utilities)
- frontend/e2e/daily-flow.spec.ts (8 daily meal completion flow tests)
- frontend/e2e/weekly-flow.spec.ts (8 weekly plan and template switching tests)
- frontend/e2e/offline.spec.ts (3 offline behavior and route tests)

**Modified:**
- frontend/package.json (added @playwright/test, test:e2e scripts)
- .gitignore (added Playwright artifacts)
- docs/ROADMAP.md (moved E2E testing to Done)
- docs/SESSION_LOG.md (this entry)

### Status: COMPLETE

---

## Session: 2026-01-27 (8)

**Role**: backend + frontend
**Task**: Build Stats view (adherence, streaks)
**Branch**: feat/stats-view

### Summary
- Created stats service with adherence rate calculation, streak tracking, per-meal-type breakdown, and daily data points
- Added `GET /api/v1/stats?days=N` endpoint with full response including daily adherence for charting
- Extended `StatsResponse` schema with new `DailyAdherence` model for per-day chart data
- Built complete Stats page with 4 overview cards, daily adherence bar chart with 7-day rolling average, per-meal-type progress bars with "Focus area" badges, completion status pie chart, and time period selector (7/30/90 days)
- Created TanStack Query hook and API function for stats
- Wrote 13 integration tests covering response structure, status breakdown, adherence calculation, streaks, overrides, meal type ordering, daily data, and parameter validation

### Files Changed
**Backend (new):**
- backend/app/services/stats.py (created — stats calculation service)
- backend/app/api/stats.py (created — GET /stats endpoint)
- backend/tests/test_stats.py (created — 13 integration tests)

**Backend (modified):**
- backend/app/schemas/stats.py (added DailyAdherence schema)
- backend/app/schemas/__init__.py (exported DailyAdherence)
- backend/app/services/__init__.py (exported get_stats)
- backend/app/api/__init__.py (exported stats_router)
- backend/app/main.py (registered stats_router)

**Frontend (new):**
- frontend/src/hooks/use-stats.ts (created — TanStack Query hook)

**Frontend (modified):**
- frontend/src/lib/types.ts (added StatsResponse, StatusBreakdown, MealTypeAdherence, DailyAdherence types)
- frontend/src/lib/api.ts (added getStats function)
- frontend/src/app/stats/page.tsx (rewrote — full stats page with charts)

### Decisions
- Streak calculation is strict: all slots must have a completion status for a day to count toward a streak
- Adherence formula: `(followed + adjusted) / (total - social - unmarked)` per Tech Spec 4.3
- Used recharts (already in dependencies) for ComposedChart and PieChart — loaded only on /stats route
- Daily adherence array included in API response to avoid N+1 queries for chart data

### Blockers
- None

### Next
- End-to-end testing (daily flows, weekly generation)

---

## Session: 2026-01-26 (7)

**Role**: frontend
**Task**: Implement offline support (service worker, cache strategy)
**Branch**: feat/offline-support

### Summary
- Generated PWA icons (192x192, 512x512, maskable variants, apple-touch) from existing SVG
- Created `useOnlineStatus` hook using `useSyncExternalStore` for tear-free online/offline tracking
- Built `OfflineBanner` component that shows "You're offline — showing cached data" when network is lost
- Configured TanStack Query's `onlineManager` to pause/resume queries with connectivity changes
- Set `networkMode: 'always'` on completion mutations so optimistic updates work offline
- Built localStorage-backed offline queue that persists completion/uncomplete actions across app restarts
- Added `useOfflineSync` hook that flushes queued actions when connectivity is restored
- Updated `.gitignore` to exclude generated service worker files (sw.js, workbox-*.js, tsbuildinfo)
- Updated layout metadata with proper icon references (PNG fallbacks + apple-touch-icon)
- Fixed: Added missing `python-multipart` dependency (backend crashed on startup)
- Fixed: Navigation links pointed to wrong routes (`/library` → `/meals`, `/settings` → `/setup`)
- Fixed: `NEXT_PUBLIC_API_URL` in docker-compose.yml was missing `/api/v1` suffix

### Files Changed
**Frontend (new):**
- frontend/src/hooks/use-online-status.ts (created — useSyncExternalStore-based online detection)
- frontend/src/components/mealframe/offline-banner.tsx (created — offline indicator banner)
- frontend/src/lib/offline-queue.ts (created — localStorage-backed completion sync queue)
- frontend/public/icons/icon-192.png (generated from SVG)
- frontend/public/icons/icon-512.png (generated from SVG)
- frontend/public/icons/icon-maskable-192.png (generated from SVG)
- frontend/public/icons/icon-maskable-512.png (generated from SVG)
- frontend/public/icons/apple-touch-icon.png (generated from SVG)

**Frontend (modified):**
- frontend/src/app/layout.tsx (updated — OfflineBanner, icon metadata)
- frontend/src/app/page.tsx (updated — useOfflineSync hook)
- frontend/src/components/providers.tsx (updated — initOnlineManager on mount)
- frontend/src/hooks/use-today.ts (updated — networkMode, offline queue enqueue, useOfflineSync)
- frontend/src/lib/queryClient.ts (updated — onlineManager initialization)
- frontend/src/components/navigation/bottom-nav.tsx (fixed — /library → /meals, /settings → /setup)
- frontend/src/components/navigation/sidebar.tsx (fixed — /library → /meals, /settings → /setup)

**Backend (modified):**
- backend/requirements.txt (added python-multipart dependency)

**Root:**
- .gitignore (updated — exclude sw.js, workbox-*.js, tsbuildinfo)
- docker-compose.yml (fixed — NEXT_PUBLIC_API_URL now includes /api/v1)

### Offline Support Architecture
| Layer | Strategy | Details |
|-------|----------|---------|
| App Shell | Precache (Workbox) | HTML, CSS, JS, icons precached on install |
| /today API | NetworkFirst (10s timeout) | Falls back to cached response when offline |
| Other APIs | StaleWhileRevalidate | Cached 24h, revalidated when possible |
| Static Assets | CacheFirst | 30-day cache for JS, CSS, fonts, images |
| Completion Actions | Optimistic + Queue | Immediate UI update, localStorage queue for sync |
| Online Detection | useSyncExternalStore | Tear-free reads of navigator.onLine + events |

### Decisions
- Used `useSyncExternalStore` for online status (React 18+ recommended pattern, avoids tearing)
- Completion-only offline queue (setup screens are desktop workflows, not needed offline)
- Last-action-wins deduplication in queue (if user completes then uncompletes same slot offline, only last action is sent)
- `networkMode: 'always'` instead of `'offlineFirst'` — fires mutation immediately, enqueues on network error
- OfflineBanner placed above AppShell in layout (visible on all pages, not affected by scroll)

### Testing Performed
- npm run build: Passes, 8 static pages generated
- Service worker precache includes all icon files
- No TypeScript errors
- All Docker containers running and serving data
- Backend tests: Pre-existing failure (tests connect to localhost:5436 which isn't reachable from inside Docker container — tests must be run from host)

### Blockers
- None

### Next
- Build Stats view (adherence, streaks)

---

## Session: 2026-01-26 (6)

**Role**: fullstack
**Task**: Build Setup screens (Meal Types, Day Templates, Week Plans)
**Branch**: feat/setup-screens

### Summary
- Built full CRUD backends for all three setup entities (Meal Types, Day Templates, Week Plans)
- Created service layers with proper async SQLAlchemy patterns (expunge+reload for relationship updates)
- Expanded Day Templates API from GET-only to full CRUD
- Created new Meal Types and Week Plans API routers with registration in main.py
- Wrote 37 integration tests covering all CRUD operations for all three entities
- Built three-tab Setup page at `/setup` with live data from API
- Created/adapted editor components for all three entities with proper form reset, isSaving state, and delete confirmation
- Built new Week Plan editor component from scratch (weekday-to-template mapping)
- Added missing TypeScript types, API functions, and TanStack Query hooks with mutations

### Files Changed
**Backend (new):**
- backend/app/services/meal_types.py (created — CRUD service)
- backend/app/services/day_templates.py (created — CRUD service with slot replacement)
- backend/app/services/week_plans.py (created — CRUD service with day replacement + set-default)
- backend/app/api/meal_types.py (created — 5 CRUD endpoints)
- backend/app/api/week_plans.py (created — 6 endpoints including set-default)
- backend/tests/test_meal_type_crud.py (created — 12 tests)
- backend/tests/test_day_template_crud.py (created — 12 tests)
- backend/tests/test_week_plan_crud.py (created — 13 tests)

**Backend (modified):**
- backend/app/api/day_templates.py (expanded — full CRUD via service layer)
- backend/app/api/__init__.py (updated — register new routers)
- backend/app/main.py (updated — include new routers)
- backend/app/services/__init__.py (updated — export new services)

**Frontend (new):**
- frontend/src/hooks/use-week-plans.ts (created — 6 TanStack Query hooks)
- frontend/src/components/mealframe/week-plan-editor.tsx (created — weekday mapping editor)

**Frontend (modified):**
- frontend/src/lib/types.ts (updated — WeekPlanListItem, WeekPlanCreate, WeekPlanUpdate, WeekPlanDayCreate, weekday_name)
- frontend/src/lib/api.ts (updated — createWeekPlan, updateWeekPlan, deleteWeekPlan, setDefaultWeekPlan)
- frontend/src/hooks/use-meal-types.ts (expanded — CRUD mutations)
- frontend/src/hooks/use-day-templates.ts (expanded — CRUD mutations, detail query)
- frontend/src/components/mealframe/meal-type-editor.tsx (rewritten — real API types)
- frontend/src/components/mealframe/day-template-editor.tsx (rewritten — real API types)
- frontend/src/app/setup/page.tsx (rewritten — 3-tab setup with full CRUD)

### Endpoints Implemented
| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/v1/meal-types | GET | List meal types with counts |
| /api/v1/meal-types/{id} | GET | Get single meal type |
| /api/v1/meal-types | POST | Create meal type |
| /api/v1/meal-types/{id} | PUT | Update meal type |
| /api/v1/meal-types/{id} | DELETE | Delete meal type |
| /api/v1/day-templates/{id} | GET | Get single template with slots |
| /api/v1/day-templates | POST | Create template with slots |
| /api/v1/day-templates/{id} | PUT | Update template (replace slots) |
| /api/v1/day-templates/{id} | DELETE | Delete template |
| /api/v1/week-plans | GET | List week plans with day counts |
| /api/v1/week-plans/{id} | GET | Get plan with day mappings |
| /api/v1/week-plans | POST | Create week plan |
| /api/v1/week-plans/{id} | PUT | Update week plan |
| /api/v1/week-plans/{id} | DELETE | Delete week plan |
| /api/v1/week-plans/{id}/set-default | POST | Set as default plan |

### Decisions
- Used expunge+reload pattern for async SQLAlchemy relationship updates (expire causes MissingGreenlet with lazy loading)
- Editor components don't close dialog on save — parent controls close via mutation onSuccess callback
- Day Template and Week Plan editors fetch full detail via separate GET when editing (list endpoints return compact data)
- Week Plan editor uses sentinel value "__none__" for unassigned weekdays (Radix Select doesn't support empty string)
- Delete buttons disabled when entity is in use (meal types with assigned meals)

### Testing Performed
- 37 backend integration tests: all pass
- npm run build: Passes, 8 static pages (setup at 37.3 kB)
- No TypeScript errors
- Pre-existing tests unaffected

### Blockers
- None

### Next
- Implement offline support (service worker, cache strategy)

---

## Session: 2026-01-26 (5)

**Role**: fullstack
**Task**: Build Meals Library (CRUD for meals)
**Branch**: feat/meals-library-crud

### Summary
- Added 5 CRUD backend endpoints: GET /meals (paginated, search, type filter), GET /meals/{id}, POST /meals, PUT /meals/{id}, DELETE /meals/{id}
- Service layer: list_meals, get_meal_by_id, create_meal, update_meal, delete_meal in meals.py
- Wrote 16 integration tests covering all CRUD operations, pagination, search, type filtering, validation errors, and 404s
- Updated frontend API client getMeals() to support search and meal_type_id params
- Created useMeals, useCreateMeal, useUpdateMeal, useDeleteMeal TanStack Query hooks
- Created useMealTypes hook for dynamic meal type loading
- Rewrote MealEditor component to use real API types with dynamic meal types (fetched from GET /meal-types)
- Built full Meals Library page with search bar, meal type filter dropdown, meal list cards, create/edit/delete via modal, and CSV import integration

### Files Changed
- backend/app/services/meals.py (updated — added CRUD service functions)
- backend/app/services/__init__.py (updated — export new functions)
- backend/app/api/meals.py (updated — added GET/POST/PUT/DELETE route handlers)
- backend/tests/test_meal_crud.py (created — 16 integration tests)
- frontend/src/lib/api.ts (updated — getMeals now accepts search/mealTypeId)
- frontend/src/hooks/use-meals.ts (created — TanStack Query hooks for meal CRUD)
- frontend/src/hooks/use-meal-types.ts (created — TanStack Query hook for meal types)
- frontend/src/components/mealframe/meal-editor.tsx (updated — real API types, dynamic meal types)
- frontend/src/app/meals/page.tsx (rewritten — full library UI with search, filter, CRUD)
- docs/ROADMAP.md (updated — task marked done, next task promoted)

### Decisions
- Offset-based pagination (matches existing PaginatedResponse schema)
- Search by meal name only (ilike, case-insensitive)
- Meal type filter uses real IDs from GET /meal-types endpoint
- Macros made optional in editor (no longer required, matching backend schema)

---

## Session: 2026-01-26 (4)

**Role**: fullstack
**Task**: Implement CSV meal import functionality
**Branch**: feat/csv-meal-import

### Summary
- Built the full CSV meal import pipeline: backend service, API endpoint, frontend integration
- Updated `MealImportResult` Pydantic schema to match frozen spec (MEAL_IMPORT_GUIDE.md) response format
- Created meal import service with CSV parsing, validation, and bulk creation with meal-type associations
- Created `POST /api/v1/meals/import` endpoint (multipart/form-data)
- Wrote 14 integration tests covering happy path, warnings, errors, and edge cases
- Rewrote frontend CSVImporter component to call real API instead of client-side parsing
- Added `importMeals()` to frontend API client and import types to types.ts
- Wired import into the /meals page with an "Import CSV" button

### Files Changed
- backend/app/schemas/meal.py (updated - MealImportResult aligned to frozen spec format with summary/warnings/errors)
- backend/app/schemas/__init__.py (updated - export new schema types)
- backend/app/services/meals.py (created - CSV parsing, validation, meal creation with type associations)
- backend/app/services/__init__.py (updated - export import_meals_from_csv)
- backend/app/api/meals.py (created - POST /meals/import endpoint)
- backend/app/api/__init__.py (updated - register meals_router)
- backend/app/main.py (updated - register meals_router)
- backend/tests/test_meal_import.py (created - 14 integration tests)
- frontend/src/lib/types.ts (updated - MealImportResult, MealImportSummary, etc.)
- frontend/src/lib/api.ts (updated - importMeals() with multipart/form-data)
- frontend/src/components/mealframe/csv-importer.tsx (rewritten - calls real API, shows results)
- frontend/src/app/meals/page.tsx (updated - Import CSV button, CSVImporter modal)
- docs/ROADMAP.md (updated - task complete, promoted Meals Library CRUD to Now)
- docs/SESSION_LOG.md (this entry)

### Key Features
- CSV format per MEAL_IMPORT_GUIDE.md: name, portion_description (required), plus optional macros, meal_types, notes
- Meal types resolved by exact name match (case-sensitive, comma-separated)
- Unknown meal types generate warnings but don't block meal creation
- Missing required fields skip the row and report errors
- Handles UTF-8 BOM from Excel exports
- Trailing blank rows are filtered out
- Frontend shows upload → importing spinner → results with summary/warnings/errors

### Decisions
- Schema aligned to frozen spec exactly: `{ success, summary: { total_rows, created, skipped, warnings }, warnings: [{ row, message }], errors: [{ row, message }] }`
- Removed client-side CSV parsing from frontend — backend handles all validation and parsing
- Content-Type header not set for multipart uploads (browser sets boundary automatically)
- Used `utf-8-sig` decoding to handle BOM from Excel
- Added explicit `db.flush()` after meal-type association inserts for transaction consistency

### Testing Performed
- 14 backend integration tests: all pass
- Tests cover: valid CSV with all columns, required fields only, multiple meal types, duplicate names, unknown meal types (warning), invalid numerics (warning), missing name (error), missing portion (error), missing column header, empty file, header only, trailing blank rows, mixed valid/invalid rows, UTF-8 BOM
- npm run build: Passes, 8 static pages generated (including /meals at 3.91 kB)
- All component types align correctly (no TypeScript errors)
- Pre-existing weekly test failures unrelated to this session (seeded data conflicts)

### Blockers
- None

### Next
- Build Meals Library (CRUD for meals)

---

## Session: 2026-01-26 (3)

**Role**: fullstack
**Task**: Build Week View (overview and template switching)
**Branch**: feat/week-view

### Summary
- Built the Week View page at `/week` with full API integration
- Added `GET /api/v1/day-templates` backend endpoint for the TemplatePicker modal
- Created TanStack Query hooks for weekly plan data and day template listing
- Connected v0 design components (DayCardExpandable, TemplatePicker) to real API types
- All UI states implemented: loading, empty (no plan with generate CTA), error, populated week

### Files Changed
- backend/app/api/day_templates.py (created - GET /day-templates list endpoint)
- backend/app/api/__init__.py (updated - register day_templates_router)
- backend/app/main.py (updated - register day_templates_router)
- frontend/src/hooks/use-week.ts (created - useCurrentWeek, useGenerateWeek, useSwitchTemplate, useSetOverride, useClearOverride)
- frontend/src/hooks/use-day-templates.ts (created - useDayTemplates hook)
- frontend/src/app/week/page.tsx (rewritten - full Week View with API integration)
- frontend/src/components/mealframe/template-picker.tsx (updated - allow empty reason for No Plan)
- docs/ROADMAP.md (updated - task complete, promoted CSV import to Now)
- docs/SESSION_LOG.md (this entry)

### Key Features
- Week header with date range and "Generate Next Week" button
- 7 expandable day cards showing template name, meals, progress bar, completion badges
- Today highlighted with badge and ring, past days muted
- Override days show "No Plan" with optional reason
- Template switching via TemplatePicker modal with confirmation when meals are completed
- Empty state with prominent "Generate Week" CTA when no plan exists
- Error state with message display
- Mutations invalidate both `currentWeek` and `today` query caches

### Decisions
- Added backend `GET /day-templates` endpoint (frontend API client already defined it but backend didn't serve it)
- Mapped API types to v0 component props in the page (not in components) to keep v0 components reusable
- Removed the week navigation arrows from v0 design (only current week is relevant for MVP)
- Fixed TemplatePicker to allow empty reason for "No Plan" (API allows it, UI was blocking it)

### Testing Performed
- npm run build: Passes, 8 static pages generated (including /week at 6.42 kB)
- All component types align correctly (no TypeScript errors)

### Blockers
- None

### Next
- Implement CSV meal import functionality

---

## Session: 2026-01-26 (2)

**Role**: backend
**Task**: Seed initial data (Meal Types, Day Templates, Week Plan, Sample Meals)
**Branch**: feat/seed-data

### Summary
- Created idempotent seed script (`backend/app/seed.py`) that populates all initial data from SEED_DATA.md
- Seeded 12 meal types, 31 sample meals with meal-type associations, 5 day templates with slots, 1 default week plan with 7 day mappings, and app config
- Generated a weekly plan for the current week and verified GET /today returns populated meals
- Script is re-runnable: checks for existing data before inserting

### Files Changed
- backend/app/seed.py (created - idempotent seed script)
- docs/ROADMAP.md (updated - task complete, promoted Week View to Now)
- docs/SESSION_LOG.md (this entry)

### Data Seeded
| Entity | Count | Details |
|--------|-------|---------|
| App Config | 1 | timezone=Europe/Ljubljana, week_start_day=0 |
| Meal Types | 12 | Breakfast through Hiking Fuel |
| Meals | 31 | 3 Breakfast, 2 Pre-Workout Breakfast, 2 Mid-Morning Protein, 3 Lunch, 3 Afternoon Filler, 2 Pre-Workout Snack, 3 Post-Workout Snack, 4 Dinner, 3 Light Dinner, 3 Weekend Breakfast, 3 Hiking Fuel |
| Day Templates | 5 | Normal Workday (5 slots), Morning Workout (5), Evening Workout (5), Weekend (3), Hiking Weekend (4) |
| Week Plan | 1 | Default Week with 7 day mappings |

### Decisions
- Seed script runs standalone via `python -m app.seed` (not an API endpoint or Alembic migration)
- Idempotency via check-before-insert: queries existing records by name before creating
- Requires DATABASE_URL env var pointing to localhost:5436 when running outside Docker
- Generated weekly plan separately via API after seeding (not part of seed script)

### Testing Performed
- Seed script: Ran successfully, all 12 meal types + 31 meals + 5 templates + 1 plan created
- Idempotency: Re-ran seed, all entities skipped (no duplicates)
- API: POST /weekly-plans/generate created week for 2026-01-26
- API: GET /today returns Normal Workday with 5 populated meal slots (Scrambled Eggs, Protein Coffee, Chicken Rice Bowl, Cottage Cheese Bowl, Grilled Salmon)

### Blockers
- None

### Next
- Build Week View (overview and template switching)

---

## Session: 2026-01-26

**Role**: frontend
**Task**: Build Today View (mobile-first, primary screen)
**Branch**: feat/today-view

### Summary
- Built the Today View as the primary screen at `/`, connected to `GET /api/v1/today`
- Created TanStack Query hooks with optimistic updates for completion flow
- Integrated v0 design components: MealCardGesture, CompletionSheetAnimated, CompletionAnimation, ProgressRing, StreakBadge, Toast
- Added AppShell (bottom nav + sidebar) to root layout for app-wide navigation
- All UI states implemented: loading, error, empty (no plan / override), meals with hero "next" card, day complete celebration
- Full completion flow: tap for status picker, long-press/swipe for quick "followed", animation, undo via toast

### Files Changed
- frontend/src/app/page.tsx (rewritten - Today View with API integration)
- frontend/src/app/layout.tsx (updated - AppShell wrapper added)
- frontend/src/hooks/use-today.ts (created - useToday, useCompleteSlot, useUncompleteSlot hooks)
- frontend/src/components/navigation/bottom-nav.tsx (updated - route `/today` → `/`)
- frontend/src/components/navigation/sidebar.tsx (updated - route `/today` → `/`)
- docs/ROADMAP.md (updated - task complete, reprioritized Next)
- docs/SESSION_LOG.md (this entry)

### Key Features
- Optimistic updates on completion (instant UI, rollback on error)
- Automatic `is_next` recomputation after completion
- Streak badge only shown when streak > 0
- Empty state differentiates between "no plan generated" and "override day"
- Navigation now functional across all pages via AppShell in layout

### Decisions
- Today View lives at `/` (root route), not `/today` — updated all nav links accordingly
- AppShell in layout.tsx (not page-level) so all pages get navigation automatically
- Completion tracking UI built directly into Today View (not a separate task — the v0 components already provide the full interaction)
- Moved "Seed initial data" to Now since the Today View needs data to be useful

### Testing Performed
- npm run build: Passes, 8 static pages generated
- Dev server: Starts, compiles `/` successfully, HTTP 200
- Backend health check: API healthy, `/today` returns empty plan (expected — no seed data)
- Backend tests: Pre-existing pytest-asyncio version mismatch (ScopeMismatch error) — not caused by this session

### Blockers
- None

### Next
- Seed initial data (Meal Types, Day Templates, Week Plan) so Today View has real content
- Build Week View (overview and template switching)

---

## Session: 2026-01-24 (4)

**Role**: frontend
**Task**: Set up frontend foundation with v0 design system
**Branch**: feat/frontend-foundation

### Summary
- Migrated pre-built v0 design system (79 components) into frontend project
- Set up Tailwind CSS with custom warm neutral design tokens
- Configured TanStack Query for server state management
- Created typed API client matching backend Pydantic schemas
- Configured PWA with service worker caching strategies
- All routes working, build passes, dev server runs

### Files Changed
- frontend/package.json (updated - all dependencies from v0_design)
- frontend/tailwind.config.ts (created - custom design tokens)
- frontend/postcss.config.js (created)
- frontend/next.config.js (updated - PWA configuration)
- frontend/public/manifest.json (updated - proper metadata)
- frontend/public/icons/icon.svg (created - placeholder icon)
- frontend/src/app/globals.css (created - Tailwind with safe areas)
- frontend/src/app/layout.tsx (updated - providers, theme, metadata)
- frontend/src/app/page.tsx (updated - demo of v0 components)
- frontend/src/app/*/page.tsx (created - placeholder routes)
- frontend/src/components/ui/* (56 files - Radix UI primitives)
- frontend/src/components/mealframe/* (19 files - MealFrame components)
- frontend/src/components/navigation/* (3 files - AppShell, BottomNav, Sidebar)
- frontend/src/components/providers.tsx (created - Query + Theme providers)
- frontend/src/components/theme-provider.tsx (copied from v0_design)
- frontend/src/lib/api.ts (created - typed API client)
- frontend/src/lib/types.ts (created - TypeScript types matching backend)
- frontend/src/lib/queryClient.ts (created - TanStack Query setup)
- frontend/src/lib/utils.ts (copied - cn utility)
- frontend/src/hooks/use-mobile.ts (copied from v0_design)
- frontend/src/hooks/use-toast.ts (copied from v0_design)
- docs/ROADMAP.md (updated - task complete, design assets documented)
- docs/SESSION_LOG.md (this entry)

### Design Assets Integrated
| Component Type | Count | Source |
|---------------|-------|--------|
| UI Primitives | 56 | v0_design/components/ui/ |
| MealFrame Components | 19 | v0_design/components/mealframe/ |
| Navigation | 3 | v0_design/components/navigation/ |
| Hooks | 2 | v0_design/hooks/ |

### Key Features
- Dark mode by default with warm neutral palette
- Safe area utilities for iOS notch/home indicator (Apple HIG compliant)
- PWA disabled in development, enabled in production
- API client with typed endpoints for all backend routes
- TanStack Query with 5-minute stale time for meal data

### Type Fix Applied
- Fixed CompletionSheetAnimated onSelect type to use `Exclude<CompletionStatus, 'pending'>`
- The v0 components included 'pending' in CompletionStatus but the callback correctly excludes it

### Testing Performed
- npm install: 807 packages installed
- npm run build: Passes, generates 8 static pages
- npm run dev: Dev server starts, components render correctly
- Home page shows ProgressRing (3/5) and StreakBadge (4 days) correctly

### Decisions
- Used Tailwind v3 (stable) instead of v4 (from v0_design) for compatibility
- Adapted globals.css from OKLCH to HSL color format for Tailwind v3
- Used Inter font as fallback since Geist requires Google Fonts setup
- Components copied directly, will adapt as we connect to real API

### Blockers
- None

### Next
- Build Today View (mobile-first, primary screen)
- Connect to backend API with real data

---

## Session: 2026-01-24 (3)

**Role**: backend
**Task**: Build API endpoints for weekly planning (generate, template switching)
**Branch**: feat/weekly-api

### Summary
- Implemented all 5 weekly planning API endpoints per Tech Spec section 4.4
- Created service layer for week generation and template switching
- Week generation uses existing round-robin algorithm for meal assignment
- Added 20 new integration tests covering all endpoints and edge cases
- All 60 tests pass (40 existing + 20 new)

### Files Changed
- backend/app/services/weekly.py (created - week generation, template switching, overrides)
- backend/app/services/__init__.py (updated - export weekly service functions)
- backend/app/api/weekly.py (created - 5 weekly planning API routes)
- backend/app/api/__init__.py (updated - export weekly_router)
- backend/app/main.py (updated - register weekly router)
- backend/tests/test_weekly_api.py (created - 20 integration tests)
- docs/ROADMAP.md (updated)
- docs/SESSION_LOG.md (this entry)

### Endpoints Implemented
| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/v1/weekly-plans/current | GET | Current week's plan with all days/slots |
| /api/v1/weekly-plans/generate | POST | Generate new week via round-robin |
| /api/v1/weekly-plans/current/days/{date}/template | PUT | Switch day's template |
| /api/v1/weekly-plans/current/days/{date}/override | PUT | Mark day as "no plan" |
| /api/v1/weekly-plans/current/days/{date}/override | DELETE | Remove override, restore plan |

### Key Features
- Week generation defaults to next Monday if no date provided
- Template switching deletes existing slots and regenerates with new meals
- Override functionality marks day as "no plan" and deletes slots
- Clearing override restores plan using the day's original template
- Validates week_start_date is a Monday
- Validates target dates are within current week

### Testing Performed
- 20 new integration tests covering all endpoints
- Tests for edge cases: no plan, conflict (409), invalid template, date not in week
- Round-robin rotation verified across multiple weeks
- All 60 tests pass

### Decisions
- Service layer pattern: business logic in services/weekly.py, routes thin
- get_week_start_date reused from today service
- Date validation happens at API layer before calling service functions

### Blockers
- None

### Next
- Set up frontend foundation (Next.js + PWA)
- Build Today View (mobile-first, primary screen)

---

## Session: 2026-01-24 (2)

**Role**: backend
**Task**: Build API endpoints for daily use (GET /today, POST /slots/{id}/complete)
**Branch**: feat/daily-api

### Summary
- Implemented primary daily use API endpoints per Tech Spec section 4.3
- Created service layer for today view business logic
- Added comprehensive integration tests (15 new tests)
- All 40 tests pass

### Files Changed
- backend/app/api/today.py (created - daily use API routes)
- backend/app/api/__init__.py (updated - export today_router)
- backend/app/main.py (updated - register router)
- backend/app/services/today.py (created - today view business logic)
- backend/tests/test_today_api.py (created - 15 integration tests)
- docs/ROADMAP.md (updated)
- docs/SESSION_LOG.md (this entry)

### Endpoints Implemented
| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/v1/today | GET | Today's meal plan with is_next indicator |
| /api/v1/yesterday | GET | Yesterday's plan for catch-up |
| /api/v1/slots/{id}/complete | POST | Mark slot with completion status |
| /api/v1/slots/{id}/complete | DELETE | Undo completion (reset to null) |

### Key Features
- `is_next` computed as first slot with null completion_status
- Streak calculation counts consecutive completed days backwards
- Stats include completed count, total slots, and streak days
- Graceful handling of missing plans (empty response)
- All 5 completion statuses supported: followed, adjusted, skipped, replaced, social

### Testing Performed
- 15 new integration tests covering all endpoints
- Tests for edge cases: no plan, slot not found, invalid status
- Streak calculation tests (consecutive days, break on incomplete)
- All 40 tests pass (25 existing + 15 new)

### Decisions
- Service layer pattern: business logic in services/today.py, routes thin
- Streak calculation stops on first incomplete day or override day
- Uses existing Pydantic schemas from previous session

### Blockers
- None

### Next
- Build API endpoints for weekly planning (generate, template switching)
- Set up frontend foundation

---

## Session: 2026-01-24

**Role**: backend
**Task**: Build Pydantic schemas for API requests/responses
**Branch**: feat/pydantic-schemas

### Summary
- Created comprehensive Pydantic schemas matching Tech Spec section 4 API contracts
- Implemented 10 schema files covering all entities and API operations
- Schemas support ORM serialization, JSON encoding, and validation
- All existing tests still pass

### Files Changed
- backend/app/schemas/base.py (created - base config, ORM mode, JSON encoders)
- backend/app/schemas/common.py (created - CompletionStatus enum, pagination, errors)
- backend/app/schemas/meal_type.py (created - MealType CRUD schemas)
- backend/app/schemas/meal.py (created - Meal CRUD + CSV import schemas)
- backend/app/schemas/day_template.py (created - DayTemplate with slots)
- backend/app/schemas/week_plan.py (created - WeekPlan with day mappings)
- backend/app/schemas/weekly_plan.py (created - instance/day/slot schemas)
- backend/app/schemas/today.py (created - TodayResponse with is_next, stats)
- backend/app/schemas/stats.py (created - adherence statistics schemas)
- backend/app/schemas/__init__.py (updated - export all schemas)
- docs/ROADMAP.md (updated)
- docs/SESSION_LOG.md (this entry)

### Schema Organization
| File | Purpose |
|------|---------|
| base.py | BaseSchema with from_attributes, JSON encoders |
| common.py | CompletionStatus enum, Weekday enum, pagination, errors |
| meal_type.py | Create/Update/Response + Compact variant |
| meal.py | Full CRUD + MealImportRow for CSV import |
| day_template.py | Template + slots with position ordering |
| week_plan.py | Week structure with weekday→template mapping |
| weekly_plan.py | Generated instances, slots, completion tracking |
| today.py | TodayResponse with is_next indicator and stats |
| stats.py | Adherence rates, streaks, meal type breakdown |

### Decisions
- Used `from_attributes=True` (Pydantic v2) instead of deprecated `orm_mode`
- Decimal type for macro values (protein_g, etc.) to match database precision
- Compact variants for nested responses to avoid circular dependencies
- `is_next` computed at API layer, not stored in database

### Testing Performed
- Verified all schemas import without errors
- All 25 existing round-robin tests pass
- No circular import issues

### Blockers
- None

### Next
- Build API endpoints for daily use (GET /today, POST /slots/{id}/complete)
- Build API endpoints for weekly planning

---

## Session: 2026-01-22

**Role**: backend
**Task**: Implement round-robin meal selection algorithm
**Branch**: feat/round-robin

### Summary
- Implemented deterministic round-robin algorithm per Tech Spec section 3.1 and ADR-002
- Created services/round_robin.py with core selection logic
- Added peek function for previewing without advancing state
- Added reset function for testing and state management
- Set up pytest infrastructure with PostgreSQL integration tests
- Wrote 25 comprehensive unit tests covering all algorithm properties
- Also changed backend port from 8000 to 8003 (avoid local conflicts)

### Files Changed
- backend/app/services/round_robin.py (created - core algorithm)
- backend/app/services/__init__.py (exports)
- backend/requirements.txt (added pytest, pytest-asyncio, aiosqlite, httpx)
- backend/pytest.ini (created - test configuration)
- backend/tests/__init__.py (created)
- backend/tests/conftest.py (created - fixtures and helpers)
- backend/tests/test_round_robin.py (created - 25 tests)
- docker-compose.yml (port 8000 → 8003)
- .env.example (port note)
- docs/ROADMAP.md (updated)
- docs/SESSION_LOG.md (this entry)

### Algorithm Details
The round-robin algorithm:
1. Orders meals by (created_at ASC, id ASC) for determinism
2. Tracks last-used meal ID in round_robin_state table
3. Returns next meal as (last_index + 1) % total_meals
4. Handles edge cases: no meals (None), single meal (always return), deleted meal (reset to first)

### Testing Performed
- All 25 tests pass against PostgreSQL (Docker container)
- Tests cover: ordering, rotation, wraparound, state tracking, edge cases
- Tests verify determinism (same inputs → same outputs)
- Tests verify fairness (all meals get equal turns)

### Decisions
- Used PostgreSQL for tests (SQLite doesn't support ARRAY type)
- Tests use transaction rollback for isolation (fast, clean)
- Added peek_next_meal_for_type for preview without side effects
- Added reset_round_robin_state for testing purposes

### Blockers
- None

### Next
- Build Pydantic schemas for API requests/responses
- Build API endpoints for daily use

---

## Session: 2026-01-20 (2)

**Role**: backend
**Task**: Implement database schema and migrations (Alembic)
**Branch**: feat/database-schema

### Summary
- Created all 12 SQLAlchemy models exactly matching Tech Spec v0 schema
- Implemented proper relationships, indexes, and constraints per specification
- Generated initial Alembic migration with auto-detection
- Applied migration and verified all tables created correctly in PostgreSQL
- Tested both upgrade and downgrade migrations successfully
- Confirmed API health after schema application

### Files Changed
- backend/app/models/meal_type.py (created)
- backend/app/models/meal.py (created)
- backend/app/models/meal_to_meal_type.py (created - junction table)
- backend/app/models/day_template.py (created - DayTemplate + DayTemplateSlot)
- backend/app/models/week_plan.py (created - WeekPlan + WeekPlanDay)
- backend/app/models/weekly_plan.py (created - WeeklyPlanInstance + days + slots)
- backend/app/models/round_robin.py (created - RoundRobinState)
- backend/app/models/app_config.py (created - AppConfig singleton)
- backend/app/models/__init__.py (export all models)
- backend/alembic/env.py (import models for auto-detection)
- backend/alembic/versions/1454edda6380_initial_schema.py (generated migration)
- docs/ROADMAP.md (updated task status)
- docs/SESSION_LOG.md (this entry)

### Decisions
- All models use UUIDs as primary keys (per Tech Spec)
- Timezone-aware timestamps (TIMESTAMPTZ) for all datetime fields
- Proper cascade behaviors: CASCADE for owned children, SET NULL for references, RESTRICT for templates
- Indexes on: meal.name, meal.created_at (for round-robin), meal_type.name, all date fields
- CHECK constraints: weekday (0-6), completion_status enum, app_config singleton (id=1)
- UNIQUE constraints: position uniqueness, date uniqueness where required
- Did NOT add user_id columns yet (deferred per session plan decision)

### Testing Performed
- Generated migration with `alembic revision --autogenerate`
- Applied migration with `alembic upgrade head`
- Verified all 12 tables + alembic_version table created
- Checked table structures match Tech Spec exactly (via psql \d commands)
- Confirmed indexes, foreign keys, and constraints present
- Tested rollback with `alembic downgrade base`
- Re-applied migration successfully
- Verified API health endpoint still responsive

### Schema Verification
All tables created with correct structure:
- meal_type: name index (unique), tags array, timestamps
- meal: name + created_at indexes, portion_description NOT NULL, macros optional
- meal_to_meal_type: composite PK, CASCADE deletes
- day_template + day_template_slot: position uniqueness, RESTRICT on meal_type FK
- week_plan + week_plan_day: weekday CHECK (0-6), is_default flag
- weekly_plan_instance: unique week_start_date, SET NULL on week_plan
- weekly_plan_instance_day: date uniqueness, is_override flag, template switching support
- weekly_plan_slot: completion_status CHECK (5 values + NULL), composite unique on (instance, date, position)
- round_robin_state: PK on meal_type_id, tracks last_meal_id
- app_config: singleton CHECK (id=1), timezone, week_start_day

### Blockers
- None

### Next
- Implement round-robin meal selection algorithm (services/round_robin.py)
- Build Pydantic schemas for API requests/responses
- Build API endpoints for daily use and weekly planning

---

## Session: 2026-01-20 (1)

**Role**: backend
**Task**: Set up backend foundation (FastAPI + PostgreSQL + Docker)
**Branch**: feat/backend-foundation

### Summary
- Implemented complete backend foundation with FastAPI, PostgreSQL, and Docker
- Created production-ready configuration management with Pydantic Settings
- Set up async SQLAlchemy with connection pooling and lifecycle management
- Configured Alembic for database migrations with async support
- Added CORS middleware and health check endpoints
- Pinned all dependency versions for reproducibility
- Fixed CORS configuration parsing to handle comma-separated strings
- Resolved Docker port conflicts and verified full stack startup

### Files Changed
- backend/app/config.py (implemented with environment variable support)
- backend/app/database.py (async SQLAlchemy with session management)
- backend/app/main.py (CORS, lifecycle hooks, health endpoints)
- backend/requirements.txt (pinned versions)
- backend/alembic.ini (created)
- backend/alembic/env.py (async migration support)
- backend/alembic/script.py.mako (migration template)
- backend/alembic/README (migration guide)
- .env.example (configuration template)
- docker-compose.yml (removed obsolete version, changed DB port to 5436)
- frontend/Dockerfile (handle missing package-lock.json)
- docs/ROADMAP.md (updated task status)
- docs/SESSION_LOG.md (this entry)

### Decisions
- Used field validator for CORS_ORIGINS to parse comma-separated strings
- Changed database port to 5436 to avoid conflicts with other local services
- Configured connection pool (size=5, max_overflow=10) for production readiness
- Added both root (/) and /health endpoints for monitoring
- Enabled auto-reload in development for faster iteration

### Testing Performed
- Verified Docker Compose builds all images successfully
- Confirmed PostgreSQL container starts and accepts connections
- Validated FastAPI application starts and connects to database
- Tested health endpoints return correct responses
- Verified API documentation accessible at /docs

### Blockers
- None

### Next
- Implement database schema and migrations (Alembic)
- Build core data models (Meal, MealType, DayTemplate, WeekPlan)

---

## Session: 2026-01-19

**Role**: architecture
**Task**: Initialize SpecFlow documentation structure
**Branch**: N/A (initial setup)

### Summary
- Initialized SpecFlow framework for MealFrame project
- Created comprehensive documentation structure (full depth)
- Extracted 18 priority tasks from PRD into ROADMAP
- Configured for solo git workflow with type/description branch convention
- Set up agent guides for backend (FastAPI) and frontend (Next.js)

### Files Changed
- .specflow-config.md (created)
- CLAUDE.md (created)
- docs/ROADMAP.md (created)
- docs/SESSION_LOG.md (created)
- docs/WORKFLOW.md (created)
- docs/VISION.md (created)
- docs/OVERVIEW.md (created)
- docs/ADR.md (created)
- .claude/commands/plan-session.md (created)
- .claude/commands/start-session.md (created)
- .claude/commands/end-session.md (created)
- .claude/commands/pivot-session.md (created)
- .ai/agents/backend.md (created)
- .ai/agents/frontend.md (created)

### Decisions
- Using central documentation organization (not per-feature) - simpler for solo workflow
- Full documentation depth to support both backend and frontend development
- No ticketing system integration for MVP (can add later if needed)

### Blockers
- None

### Next
- Initialize git repository and create .gitignore
- Set up backend foundation (FastAPI + PostgreSQL + Docker)

---

<!-- Prepend new session entries above this line -->
