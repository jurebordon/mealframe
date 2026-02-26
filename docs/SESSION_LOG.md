# Session Log

> Append-only journal of development sessions. Newest entries first.
> Each session gets one entry - prepend new entries at the top.

---

## Session: 2026-02-26

**Role**: devops / frontend
**Task**: Production deployment of landing page + privacy policy
**Branch**: main (direct commits)

### Summary
- Added `NEXT_PUBLIC_GOOGLE_SCRIPT_URL` and `NEXT_PUBLIC_SITE_URL` as Docker build args in Dockerfile and docker-compose.prod.yml so env vars are baked into the production client bundle
- Deployed landing page, privacy policy, and waitlist form to production at `mealframe.io`
- Configured Nginx Proxy Manager: both `mealframe.io` and `www.mealframe.io` proxy to stack nginx on port 80, SSL via Let's Encrypt covering both domains
- Added `location = / { return 302 /waitlist; }` in NPM advanced config to redirect root to waitlist
- Removed old NPM advanced API proxy config (port 8003 direct) — stack nginx now handles `/api/` routing internally
- Set up DNS: A record for `@` and CNAME for `www` pointing to server
- Verified Google Sheets integration working end-to-end in production

### Files Changed
- [frontend/Dockerfile](frontend/Dockerfile) — Added `NEXT_PUBLIC_GOOGLE_SCRIPT_URL` and `NEXT_PUBLIC_SITE_URL` build args
- [docker-compose.prod.yml](docker-compose.prod.yml) — Added corresponding build args with defaults

### Decisions
- NPM points to stack nginx (port 80) instead of web container directly (port 3000) — cleaner architecture, stack nginx handles API routing
- Canonical domain is `mealframe.io` (both bare and www served, no redirect between them)
- Root `/` redirects to `/waitlist` via NPM config until auth is implemented

### Blockers
- None

### Next
- Set up email forwarding for `hello@mealframe.io` (Namecheap or Cloudflare)
- Phase 2 Wave 2: Authentication & multi-user (ADR-014)

---

## Session: 2026-02-25 (b)

**Role**: frontend
**Task**: Privacy policy page for waitlist landing
**Branch**: feat/privacy-policy

### Summary
- Created standard privacy policy page at `/privacy` covering: email collection (waitlist), self-hosted pageview analytics, localStorage usage, cookies (none), third parties (Google Sheets), data retention, user rights, contact info
- Added "Privacy" link to waitlist page footer with amber hover state
- Page uses same dark design tokens as waitlist page, inherits Geist font from `(landing)` layout

### Files Changed
- [frontend/src/app/(landing)/privacy/page.tsx](frontend/src/app/(landing)/privacy/page.tsx) — New: privacy policy page
- [frontend/src/app/(landing)/waitlist/page.tsx](frontend/src/app/(landing)/waitlist/page.tsx) — Added Privacy link to footer

### Decisions
- Used `hello@mealframe.io` as the contact email for data requests
- Set 12-month retention for pageview data
- Page is a static client component (no API calls needed)

### Blockers
- None

### Next
- Phase 2 Wave 2: Authentication & multi-user (ADR-014)

---

## Session: 2026-02-25

**Role**: full-stack
**Task**: Track C — Waitlist landing page + self-hosted pageview analytics
**Branch**: feat/landing-page

### Summary
- Restructured frontend into Next.js route groups: `(app)` for existing pages (with AppShell/Providers) and `(landing)` for the standalone waitlist page (no app chrome)
- Built waitlist landing page at `/waitlist` with all 6 sections from the PRD: hero, problem, solution, early results, about, final CTA
- Page uses Geist font (via `geist` npm package), inline dark design tokens (bg `#0d0c0b`, amber accent `#c47a30`), scroll-fade animations (Intersection Observer), and sticky header
- Implemented reusable `WaitlistForm` component with 4 states (idle/loading/success/error), localStorage persistence (`mf_waitlist_submitted`), and Google Apps Script integration via `NEXT_PUBLIC_GOOGLE_SCRIPT_URL` env var
- Built lightweight self-hosted pageview analytics: `POST /api/v1/analytics/pageview` endpoint, `landing_pageview` Postgres table with privacy-friendly IP hashing (SHA-256 with daily salt)
- Frontend analytics client (`lib/analytics.ts`) fires pageview on mount via `fetch` with `keepalive: true` — fire-and-forget, never breaks the page
- Merged `v0_design_new/` into `v0_design/` (single design folder with route group structure)
- Geist font from `next/font/google` doesn't exist in Next.js 14 — used the `geist` npm package instead, applied via `GeistSans.className` on the landing layout to avoid CSS variable collision with Inter's `--font-geist-sans`

### Files Changed
**Frontend — route group restructure:**
- [frontend/src/app/layout.tsx](frontend/src/app/layout.tsx) — Stripped to minimal root layout (no Providers/AppShell)
- [frontend/src/app/(app)/layout.tsx](frontend/src/app/(app)/layout.tsx) — New: Providers + OfflineBanner + AppShell wrapper
- [frontend/src/app/(app)/page.tsx](frontend/src/app/(app)/page.tsx) — Moved from `app/page.tsx`
- `(app)/week/`, `(app)/meals/`, `(app)/setup/`, `(app)/stats/` — Moved from `app/`

**Frontend — landing page:**
- [frontend/src/app/(landing)/layout.tsx](frontend/src/app/(landing)/layout.tsx) — SEO metadata, OG/Twitter tags, Geist font
- [frontend/src/app/(landing)/waitlist/page.tsx](frontend/src/app/(landing)/waitlist/page.tsx) — Full landing page
- [frontend/src/components/landing/waitlist-form.tsx](frontend/src/components/landing/waitlist-form.tsx) — Email form component
- [frontend/src/lib/analytics.ts](frontend/src/lib/analytics.ts) — Pageview tracker
- [frontend/public/og-image.jpg](frontend/public/og-image.jpg) — OG image for social sharing
- [frontend/.env.local](frontend/.env.local) — New env vars (gitignored)
- [frontend/package.json](frontend/package.json) — Added `geist` font package

**Backend — analytics:**
- [backend/app/models/landing_pageview.py](backend/app/models/landing_pageview.py) — New model
- [backend/app/schemas/analytics.py](backend/app/schemas/analytics.py) — Request/response schemas
- [backend/app/services/analytics.py](backend/app/services/analytics.py) — Service with IP hashing
- [backend/app/api/analytics.py](backend/app/api/analytics.py) — POST endpoint (202 Accepted)
- [backend/app/api/__init__.py](backend/app/api/__init__.py) — Registered analytics_router
- [backend/app/main.py](backend/app/main.py) — Included analytics_router
- [backend/app/models/__init__.py](backend/app/models/__init__.py) — Registered LandingPageview
- [backend/app/services/__init__.py](backend/app/services/__init__.py) — Exported record_pageview
- [backend/alembic/versions/20260225_add_landing_pageview.py](backend/alembic/versions/20260225_add_landing_pageview.py) — Migration

**Design assets:**
- `v0_design/` — Merged from `v0_design_new/` (now includes route groups + landing page)

### Decisions
- Used `geist` npm package instead of `next/font/google` (Geist not available in Next.js 14, only 15+)
- Applied Geist via `GeistSans.className` on landing layout div to avoid CSS variable collision with Inter's `--font-geist-sans`
- Analytics uses `fetch` with `keepalive: true` instead of `navigator.sendBeacon` — sendBeacon with `application/json` triggers CORS preflight which it can't handle
- IP hashing uses SHA-256 with daily salt for privacy — no raw IPs stored
- Landing page uses inline styles with own design tokens, independent of Tailwind theme variables
- Domain routing (www vs app) deferred to deployment phase — currently path-based only

### Blockers
- None

### Next
- DNS + Nginx Proxy Manager config for `www.mealframe.io` → `/waitlist`, `app.mealframe.io` → `/`
- Google Apps Script setup for waitlist form submission
- Wave 2: Authentication (ADR-014)

---

## Session: 2026-02-24

**Role**: frontend
**Task**: Fix MealPicker bugs — empty state, iOS keyboard, sheet resizing
**Branch**: fix/meal-picker-bugs

### Summary
- Fixed MealPicker showing "No meals available" in both add-adhoc and reassign modes
- Root cause: `pageSize: 200` exceeded backend's `page_size` max of 100, causing a silent 422 validation error. TanStack Query entered error state, `data` was `undefined`, rendered as empty list
- Fixed iOS keyboard pushing the bottom sheet off-screen by replacing `autoFocus` with delayed focus (400ms post-animation) and using `dvh` units
- Fixed sheet resizing as search results reduced — changed from `max-h` to fixed `h-[85dvh]`
- Added `enabled: open` to `useMeals` so query only fires when picker is visible
- Added `isFetching` check alongside `isLoading` to show spinner during query key transitions

### Files Changed
- [frontend/src/components/mealframe/meal-picker.tsx](frontend/src/components/mealframe/meal-picker.tsx) — pageSize fix, delayed focus, dvh units, flexbox layout, fixed height
- [frontend/src/hooks/use-meals.ts](frontend/src/hooks/use-meals.ts) — Added `enabled` parameter

### Decisions
- Used `h-[85dvh]` (fixed) instead of `max-h` so the sheet doesn't shrink when filtering reduces results
- Deferred search input focus by 400ms to let the sheet animation complete before triggering keyboard
- Kept `pageSize: 100` (backend max) — sufficient since library has ~31 meals

### Blockers
- None

### Next
- Track C: Landing page (Next.js route)
- Wave 2: Authentication (ADR-014)
- iOS testing of keyboard behavior on real device (verified on desktop only this session)

---

## Session: 2026-02-23

**Role**: full-stack
**Task**: Phase 2 Wave 1 — ADR-011 (Meal Reassignment) + ADR-012 (Completion Statuses)
**Branches**: feat/meal-reassignment, feat/completion-statuses (via worktrees, merged to main)

### Summary
- Implemented both Track A (ADR-012) and Track B (ADR-011) in parallel using git worktrees
- **Track B (ADR-011) — Per-Slot Meal Reassignment:**
  - Backend: Added `is_manual_override` column + migration, `PUT /slots/{id}/reassign` endpoint with meal type validation, past-date guard, round-robin preservation. 445-line test suite (9 tests)
  - Frontend: Wired "Change meal" button in CompletionSheet, added MealPicker in reassign mode with meal type filtering, "Changed" indicator badges for manually overridden slots
- **Track A (ADR-012) — Revised Completion Statuses:**
  - Backend: Migration renames adjusted→equivalent, replaced→deviated. Added `actual_meal_id` FK column and `actual_meal` relationship. Updated CHECK constraint, schemas, stats service (new adherence formula: `followed / (total - equivalent - social - unmarked)`), today service, and all tests
  - Frontend: Updated all status references across 11 component files. Deviated now uses destructive color scheme. StatusBadge, CompletionSheet, CompletionAnimation, YesterdayReview, Stats page all updated
- Fixed migration ordering (must drop CHECK before renaming data values)
- Fixed `Meal.weekly_plan_slots` ambiguous FK (two paths to meal table via `meal_id` and `actual_meal_id`)
- Fixed `RoundRobinState` test using invalid `id` kwarg (model uses `meal_type_id` as PK)
- All 165 backend tests pass, frontend builds clean

### Files Changed
**Track B (ADR-011):**
- [backend/alembic/versions/20260223_add_is_manual_override_to_weekly_plan_slot.py](backend/alembic/versions/20260223_add_is_manual_override_to_weekly_plan_slot.py) — New migration
- [backend/app/models/weekly_plan.py](backend/app/models/weekly_plan.py) — Added `is_manual_override` column
- [backend/app/schemas/weekly_plan.py](backend/app/schemas/weekly_plan.py) — Added `ReassignSlotRequest`, `is_manual_override` field
- [backend/app/services/today.py](backend/app/services/today.py) — Added `reassign_slot()` service
- [backend/app/api/today.py](backend/app/api/today.py) — Added `PUT /slots/{id}/reassign` endpoint
- [backend/tests/test_reassign_api.py](backend/tests/test_reassign_api.py) — New 9-test suite
- [frontend/src/lib/types.ts](frontend/src/lib/types.ts) — Added `is_manual_override`, `ReassignSlotRequest`
- [frontend/src/lib/api.ts](frontend/src/lib/api.ts) — Added `reassignSlot()`
- [frontend/src/hooks/use-today.ts](frontend/src/hooks/use-today.ts) — Added `useReassignSlot()`
- [frontend/src/components/mealframe/completion-sheet-animated.tsx](frontend/src/components/mealframe/completion-sheet-animated.tsx) — Added "Change meal" button
- [frontend/src/components/mealframe/meal-picker.tsx](frontend/src/components/mealframe/meal-picker.tsx) — Added `mode` and `mealTypeId` props
- [frontend/src/app/page.tsx](frontend/src/app/page.tsx) — Reassign flow + "Changed" indicators

**Track A (ADR-012):**
- [backend/alembic/versions/20260223_revise_completion_statuses.py](backend/alembic/versions/20260223_revise_completion_statuses.py) — New migration (status rename + actual_meal_id)
- [backend/app/models/meal.py](backend/app/models/meal.py) — Added `foreign_keys` to `weekly_plan_slots` relationship
- [backend/app/schemas/common.py](backend/app/schemas/common.py) — Updated CompletionStatus enum
- [backend/app/schemas/stats.py](backend/app/schemas/stats.py) — Updated StatusBreakdown fields
- [backend/app/services/stats.py](backend/app/services/stats.py) — Updated adherence formula
- [backend/tests/test_today_api.py](backend/tests/test_today_api.py), [backend/tests/test_stats.py](backend/tests/test_stats.py) — Updated status names
- [frontend/src/components/mealframe/status-badge.tsx](frontend/src/components/mealframe/status-badge.tsx) — New status labels/colors
- [frontend/src/components/mealframe/completion-animation.tsx](frontend/src/components/mealframe/completion-animation.tsx) — Updated status types
- [frontend/src/components/mealframe/yesterday-review-modal.tsx](frontend/src/components/mealframe/yesterday-review-modal.tsx) — Updated labels
- [frontend/src/app/stats/page.tsx](frontend/src/app/stats/page.tsx) — Updated status colors/labels
- Plus 5 more frontend components with status string updates

### Decisions
- Used git worktrees for parallel development (worktree-a, worktree-b)
- Merged Track B first (simpler), then rebased Track A on top (fixed migration chain)
- Skipped Week View reassignment integration for now — primary entry point is Today View completion sheet per ADR-011
- Migration must drop CHECK constraint before UPDATEing data (learned during deployment)
- `equivalent` status is neutral: excluded from both numerator and denominator in adherence

### Blockers
- None

### Next
- Track C: Landing page (waiting for design)
- Wave 2: Authentication (ADR-014)

---

## Session: 2026-02-20

**Role**: architecture
**Task**: Phase 2 feature planning — ADR-011 through ADR-014 + ROADMAP restructure
**Branch**: main (docs only)

### Summary
- Wrote 4 new ADRs for Phase 2 features after discussing requirements and reviewing uploaded PRDs
- ADR-011: Per-Slot Meal Reassignment — relaxes ADR-003, adds `PUT /slots/{id}/reassign`, `is_manual_override` column, reuses MealPicker in Week/Today views
- ADR-012: Revised Completion Statuses — replaces `adjusted`/`replaced` with `equivalent` (neutral) and `deviated` (negative, triggers AI capture). Adds `actual_meal_id` FK, quick-add flow for unknown meals
- ADR-013: AI-Powered Ad Hoc Meal Capture — image MVP (Phase 1), voice via Whisper (Phase 2). Two entry points: standalone + deviated completion flow. Background async processing via task queue. GPT-4o recommended
- ADR-014: Authentication & Multi-User — self-managed auth with Argon2id password hashing, JWT access tokens (15 min), refresh token rotation (7 days), Google OAuth via `authlib`, Resend for transactional email. Full data model, API endpoints, migration strategy documented
- Marked ADR-009 as superseded by ADR-014
- Restructured ROADMAP.md with Wave-based parallel execution plan and dependency graph
- Reviewed 3 uploaded PRDs (Auth, Ad Hoc Meal, Landing Page) and mapped them to ADRs
- Decided landing page will be a Next.js route in this repo (www.mealframe.io for landing, app.mealframe.io for app)
- Fixed card text selection UX (select-none on Card component) — committed separately
- Resolved auth provider blocker: self-managed (Option C) with email/password + Google OAuth

### Files Changed
- [docs/ADR.md](docs/ADR.md) - Added ADR-011 through ADR-014, marked ADR-009 as superseded
- [docs/ROADMAP.md](docs/ROADMAP.md) - Complete restructure: Wave 1 (parallel: completion statuses + meal reassignment + landing page), Wave 2 (auth), Wave 3 (AI capture), Wave 4 (grocery list). Dependency graph, blocker cleared
- [docs/frozen/features/Mealframe_Auth_MultiUser_PRD.md](docs/frozen/features/Mealframe_Auth_MultiUser_PRD.md) - New PRD (user-uploaded)
- [docs/frozen/features/Mealframe_AdHoc_Meal_PRD.md](docs/frozen/features/Mealframe_AdHoc_Meal_PRD.md) - New PRD (user-uploaded)
- [docs/frozen/features/Mealframe_LandingPage_PRD.md](docs/frozen/features/Mealframe_LandingPage_PRD.md) - New PRD (user-uploaded)
- [frontend/src/components/ui/card.tsx](frontend/src/components/ui/card.tsx) - Added select-none (committed earlier)

### Decisions
- Wave 1 uses separate git worktrees for ADR-011 and ADR-012 (zero file overlap)
- Completion statuses: `followed`, `skipped`, `equivalent`, `deviated`, `social` (replaces `adjusted` + `replaced`)
- Social meals count as non-adherent (own category in stats)
- Auth: self-managed over Clerk/Auth0/Supabase — aligns with self-hosted philosophy, small user base, cost-sensitive
- New users get empty accounts (no onboarding wizard or template clone)
- Landing page as Next.js route in existing app (not separate repo)
- ADR-008 (Grocery List) left open for Wave 4 — AI infra from ADR-013 may inform approach

### Blockers
- None

### Next
- Begin Wave 1 implementation: pick Track A (ADR-012), Track B (ADR-011), or Track C (landing page)

---

## Session: 2026-02-18 (4)

**Role**: frontend
**Task**: Day Template Calorie/Macro Soft Limits — Session 4 (Frontend) + test fix
**Branch**: feat/soft-limits-frontend

### Summary
- Added `max_calories_kcal` and `max_protein_g` to all DayTemplate TypeScript types and `OverLimitBreakdown` + 3 new fields to `StatsResponse`
- Added "Daily Limits (optional)" section to Day Template editor with max calories (kcal) and max protein (g) inputs, populated from template on edit, included in save payload
- Template list items now show "Max: 2,200 kcal / 180g protein" preview line when limits are set
- Stats page shows conditionally-rendered "Over Limit Days" card (warning amber) as 5th card in overview grid when any templates have limits
- Stats page shows "Over Limit Breakdown" section with per-template exceeded counts and percentages
- Fixed pre-existing `test_weekly_api.py` `MultipleResultsFound` failure: root cause was seed data creating a default week plan that conflicted with test fixtures. Fixed by clearing existing defaults within the test savepoint before creating test data.
- All 156 backend tests pass, Next.js build clean

### Files Changed
- [frontend/src/lib/types.ts](frontend/src/lib/types.ts) - Added soft limit fields to DayTemplate types, new `OverLimitBreakdown` type, updated `StatsResponse`
- [frontend/src/components/mealframe/day-template-editor.tsx](frontend/src/components/mealframe/day-template-editor.tsx) - Added maxCalories/maxProtein state, resetForm population, save payload, soft limits UI section
- [frontend/src/app/setup/page.tsx](frontend/src/app/setup/page.tsx) - Limit preview line in template list items
- [frontend/src/app/stats/page.tsx](frontend/src/app/stats/page.tsx) - Over Limit Days card, Over Limit Breakdown section, AlertTriangle import
- [backend/tests/test_weekly_api.py](backend/tests/test_weekly_api.py) - Fixed seed data isolation: clear existing default week plans in fixtures

### Decisions
- Over Limit Days card uses dynamic grid (`lg:grid-cols-5` when visible, `lg:grid-cols-4` when hidden) to avoid empty space
- Over Limit Breakdown placed between Average Daily Macros and Adherence Chart for visual flow
- Test fix uses `UPDATE ... SET is_default=False` inside savepoint — rolls back automatically, no permanent side effects

### Blockers
- None

### Next
- Phase 2 planning: User management/auth (ADR-009) or Grocery list generation (ADR-008)

---

## Session: 2026-02-18 (3)

**Role**: backend
**Task**: Day Template Calorie/Macro Soft Limits — Session 3 (Backend)
**Branch**: feat/soft-limits-backend

### Summary
- Added `max_calories_kcal` (nullable Integer) and `max_protein_g` (nullable Numeric(6,1)) columns to `day_template` table via Alembic migration
- Updated all Pydantic schemas (`DayTemplateBase`, `DayTemplateCreate`, `DayTemplateUpdate`, `DayTemplateResponse`, `DayTemplateListItem`) with optional limit fields
- Updated CRUD service: create persists new fields, update uses `model_fields_set` to support clearing limits via `null` while preserving on omission
- Added `OverLimitBreakdown` schema and three new fields to `StatsResponse`: `over_limit_days`, `days_with_limits`, `over_limit_breakdown`
- Implemented `_calculate_over_limit_stats()` in stats service: joins instance days with templates that have limits, sums actual meal macros per day, compares against limits, aggregates per-template breakdown
- Added 7 new day template CRUD tests (create with/without limits, update set/clear/preserve limits, list includes limits)
- Added 6 new stats tests (response fields, no limits, calories exceeded, within limits, protein exceeded, override exclusion)
- All 118 backend tests pass, Next.js build clean

### Files Changed
- [backend/alembic/versions/20260218_add_soft_limits_to_day_template.py](backend/alembic/versions/20260218_add_soft_limits_to_day_template.py) - New: migration for soft limit columns
- [backend/app/models/day_template.py](backend/app/models/day_template.py) - Added `max_calories_kcal` and `max_protein_g` columns
- [backend/app/schemas/day_template.py](backend/app/schemas/day_template.py) - Added limit fields to Base, Update, and ListItem schemas
- [backend/app/schemas/stats.py](backend/app/schemas/stats.py) - New `OverLimitBreakdown` schema, 3 new fields on `StatsResponse`
- [backend/app/schemas/__init__.py](backend/app/schemas/__init__.py) - Export `OverLimitBreakdown`
- [backend/app/api/day_templates.py](backend/app/api/day_templates.py) - Pass limit fields through list and detail responses
- [backend/app/services/day_templates.py](backend/app/services/day_templates.py) - Persist limits on create/update
- [backend/app/services/stats.py](backend/app/services/stats.py) - New `_calculate_over_limit_stats()`, wired into `get_stats()`
- [backend/tests/test_day_template_crud.py](backend/tests/test_day_template_crud.py) - 7 new soft limit CRUD tests
- [backend/tests/test_stats.py](backend/tests/test_stats.py) - 6 new over-limit stats tests

### Decisions
- Update uses `model_fields_set` to distinguish "field omitted" (no change) from "field sent as null" (clear limit) — allows clearing limits without always having to resend them
- Override days are excluded from over-limit calculations — if you marked a day as "no plan", the template limits don't apply
- `exceeded_metric` field tracks which limit(s) were exceeded per template: "calories", "protein", or "both"

### Blockers
- None

### Next
- Session 4: Frontend for soft limits (template editor UI, list previews, Stats page over-limit cards)

---

## Session: 2026-02-18 (2)

**Role**: frontend
**Task**: Ad-hoc meal addition — Session 2 (Frontend)
**Branch**: main (direct commit)

### Summary
- Created MealPicker bottom sheet component adapted from v0 design, using real meal library data via `useMeals` hook with search filtering
- Added "Add meal" ghost button below meal list in Today View
- Added `is_adhoc` field to `WeeklyPlanSlotBase` TypeScript type
- Created `addAdhocSlot` and `deleteAdhocSlot` API functions (`POST /today/slots`, `DELETE /slots/{id}`)
- Created `useAddAdhocSlot` and `useDeleteAdhocSlot` mutation hooks with optimistic updates
- Ad-hoc slots display with colored left border indicator and "Added" label
- Updated `CompletionSheetAnimated` with `isAdHoc` + `onRemove` props, showing "Remove meal" button (destructive style) for ad-hoc slots
- Full add/remove flow wired with toast notifications
- TypeScript clean, Next.js build passes

### Files Changed
- [frontend/src/lib/types.ts](frontend/src/lib/types.ts) - Added `is_adhoc` to `WeeklyPlanSlotBase`, new `AddAdhocSlotRequest` interface
- [frontend/src/lib/api.ts](frontend/src/lib/api.ts) - Added `addAdhocSlot()` and `deleteAdhocSlot()` API functions
- [frontend/src/hooks/use-today.ts](frontend/src/hooks/use-today.ts) - Added `useAddAdhocSlot` and `useDeleteAdhocSlot` mutation hooks
- [frontend/src/components/mealframe/meal-picker.tsx](frontend/src/components/mealframe/meal-picker.tsx) - New: MealPicker bottom sheet with search, loading state, meal library browsing
- [frontend/src/components/mealframe/completion-sheet-animated.tsx](frontend/src/components/mealframe/completion-sheet-animated.tsx) - Added `isAdHoc` + `onRemove` props, "Remove meal" button
- [frontend/src/app/page.tsx](frontend/src/app/page.tsx) - Added MealPicker, Add Meal button, ad-hoc indicators, remove flow wiring

### Decisions
- MealPicker fetches all meals (pageSize=200) from existing `useMeals` hook — simple, works for current library size
- Ad-hoc indicator uses `bg-primary/40` left border to be visible but not distracting
- "Remove meal" button in completion sheet uses destructive styling (red dashed border) to distinguish from status options
- `useDeleteAdhocSlot` has optimistic updates (removes slot immediately from UI), `useAddAdhocSlot` invalidates and refetches (needs server data for new slot)

### Blockers
- None

### Next
- Session 3: Backend for soft limits (migration, schema updates, over-limit stats calculation)

---

## Session: 2026-02-18

**Role**: backend
**Task**: Fix streak inconsistency between Today View and Stats page
**Branch**: fix/streak-inconsistency

### Summary
- Fixed streak inconsistency where Stats page showed "0 days" while Today View showed "6 days" for the same user
- Root cause: two separate streak calculation functions with different logic
  - `stats.py:_calculate_streaks()` counted backwards from today (inclusive) — if today had unmarked slots, streak = 0
  - `today.py:calculate_streak()` counted backwards from yesterday — correctly showed completed past days
- Unified behavior: both now count backwards from yesterday (today is still in progress)
- Removed `is_override` streak break in Today View — override days now count toward streak if all slots are marked

### Files Changed
- [backend/app/services/stats.py](backend/app/services/stats.py) - Changed current streak to start from `today - 1` instead of `today`
- [backend/app/services/today.py](backend/app/services/today.py) - Removed `is_override` break from streak calculation
- [backend/tests/test_stats.py](backend/tests/test_stats.py) - Updated streak tests to match new behavior (excludes today, breaks on unmarked past day)
- [docs/ROADMAP.md](docs/ROADMAP.md) - Added to Done
- [docs/SESSION_LOG.md](docs/SESSION_LOG.md) - This entry

### Decisions
- Current streak excludes today — today is still in progress, only fully completed past days count
- Override days do NOT break streak — plan changes are fine as long as you follow through

### Blockers
- None

### Next
- Ad-hoc meals frontend (Session 2)

---

## Session: 2026-02-12 (2)

**Role**: backend
**Task**: Ad-hoc meal addition — Session 1 (Backend)
**Branch**: feat/adhoc-meals-backend

### Summary
- Added `is_adhoc` boolean column to `weekly_plan_slot` table with Alembic migration
- Added `is_adhoc` field to all slot Pydantic schemas (`WeeklyPlanSlotBase`, inherited by `WeeklyPlanSlotResponse` and `WeeklyPlanSlotWithNext`)
- Implemented `POST /api/v1/today/slots` endpoint to create ad-hoc meal slots for today
- Implemented `DELETE /api/v1/slots/{slot_id}` endpoint that only allows deleting ad-hoc slots (403 for template slots)
- Wired `is_adhoc` through `build_today_response` and week view's `build_slot_response`
- All 105 existing tests pass (excluding pre-existing today/weekly test isolation issues)

### Files Changed
- [backend/app/models/weekly_plan.py](backend/app/models/weekly_plan.py) - Added `is_adhoc` column to `WeeklyPlanSlot`
- [backend/alembic/versions/20260212_add_is_adhoc_to_weekly_plan_slot.py](backend/alembic/versions/20260212_add_is_adhoc_to_weekly_plan_slot.py) - New: migration for `is_adhoc` column
- [backend/app/schemas/weekly_plan.py](backend/app/schemas/weekly_plan.py) - Added `is_adhoc` to `WeeklyPlanSlotBase`, new `AddAdhocSlotRequest` schema
- [backend/app/services/today.py](backend/app/services/today.py) - Added `create_adhoc_slot()` and `delete_adhoc_slot()`, wired `is_adhoc` in response builder
- [backend/app/api/today.py](backend/app/api/today.py) - New `POST /today/slots` and `DELETE /slots/{slot_id}` endpoints
- [backend/app/api/weekly.py](backend/app/api/weekly.py) - Pass `is_adhoc` in week view slot responses

### Decisions
- Meals have many-to-many with meal types; ad-hoc slots use the meal's first associated type (or null if none)
- Position for new ad-hoc slot = max(existing positions for that day) + 1
- DELETE returns 204 for success, 403 for template slots, 404 for not found
- `server_default="false"` on migration ensures existing rows get the default without backfill

### Blockers
- None

### Next
- Session 2: Frontend for ad-hoc meals (MealPicker component, Add Meal button, ad-hoc indicators, remove flow)

---

## Session: 2026-02-12

**Role**: docs / design
**Task**: Import new v0 designs + write implementation plans for ad-hoc meals and soft limits
**Branch**: main (docs only)

### Summary
- Replaced v0_design directory with updated v0_design_new containing new feature designs
- Compared old vs new: new directory is a superset — no files removed, 3 new files + 5 modified files
- Wrote detailed 4-session implementation plan in ROADMAP.md covering both features end-to-end

### New v0 Design Assets
- `v0_design/app/adhoc-demo/page.tsx` — demo of ad-hoc meal flow
- `v0_design/app/soft-limits-demo/page.tsx` — demo of soft limits UI
- `v0_design/components/mealframe/meal-picker.tsx` — new meal picker bottom sheet
- Modified: `completion-sheet-animated.tsx` (isAdHoc + onRemove props), `day-template-editor.tsx` (soft limit fields), `app/today/page.tsx`, `app/stats/page.tsx`, `app/settings/page.tsx`

### Implementation Plan (4 sessions)
1. **Session 1**: Backend for ad-hoc meals — migration (`is_adhoc` column), new endpoints (`POST /today/slots`, `DELETE /slots/{id}`)
2. **Session 2**: Frontend for ad-hoc meals — MealPicker component, Add Meal button, ad-hoc indicators, remove flow
3. **Session 3**: Backend for soft limits — migration (`max_calories_kcal`, `max_protein_g`), schema updates, over-limit stats calculation
4. **Session 4**: Frontend for soft limits — template editor fields, template list preview, Stats "Over Limit" card and breakdown

### Files Changed
- [docs/ROADMAP.md](docs/ROADMAP.md) - Detailed implementation plan with 4 sessions
- [docs/SESSION_LOG.md](docs/SESSION_LOG.md) - This entry
- Replaced `v0_design/` directory with updated designs from `v0_design_new/`

### Decisions
- Deleted old v0_design entirely (new directory is a superset)
- Split implementation into 4 focused sessions (2 per feature, backend then frontend)
- Ad-hoc meals use `is_adhoc` boolean on `weekly_plan_slot` — simplest approach, slots are first-class
- Soft limits use nullable columns on `day_template` — both optional, tracked at stats level only

### Blockers
- None

### Next
- Start Session 1: Backend for ad-hoc meals

---

## Session: 2026-02-10

**Role**: docs / design
**Task**: Add ad-hoc meals and day template soft limits to roadmap + v0 design prompts
**Branch**: main (docs only)

### Summary
- Added two new features to ROADMAP.md "Next" section (above Phase 2 items):
  1. Ad-hoc meal addition — add meals to today that aren't in the template (e.g., snacks from the meal library)
  2. Day template calorie/macro soft limits — optional max_calories_kcal and max_protein_g per template, tracked in Stats
- Created v0 design prompts for both features (docs/v0_prompts_adhoc_meals_and_limits.md)
  - Prompt A: Ad-hoc meal addition (Today View button, meal picker sheet, ad-hoc card styling)
  - Prompt B: Soft limits (template editor fields, template list preview, Stats "Over Limit" card)
- Prompts designed for the existing v0 thread, referencing established components and patterns

### Files Changed
- [docs/ROADMAP.md](docs/ROADMAP.md) - Added two features to Next section
- [docs/v0_prompts_adhoc_meals_and_limits.md](docs/v0_prompts_adhoc_meals_and_limits.md) - New: v0 design prompts for both features

### Decisions
- Soft limits are NOT shown in Today View or Week View — only tracked in Stats (no daily nagging)
- Ad-hoc meals get full completion tracking, same as template meals
- Ad-hoc meals are visually distinguished with an "Added" badge but otherwise treated as first-class
- "Over Limit" tracking counts days where actual totals exceed either calories OR protein limit
- Both features prioritized above Phase 2 (auth/grocery list) as personal use improvements

### Blockers
- None

### Next
- Post v0 prompts and iterate on designs
- Implement ad-hoc meal addition (smaller scope, more immediately useful)
- Implement soft limits (requires migration + stats backend changes)

---

## Session: 2026-02-09

**Role**: frontend
**Task**: Fix completion UX — swipe cascading bug, clear status, meal ordering
**Branch**: fix/completion-undo-and-swipe-sensitivity (+ direct main commits)

### Summary
- Investigated reported bug where all meals got marked as "followed" after swiping one
- Root cause: swipe completion triggered on one card, React re-rendered a new card under the same finger, which immediately received the ongoing touch events and cascaded through all meals
- Fixed with module-level 400ms cooldown guard + clearing touchStartRef on completion
- Added "Clear status" button to completion sheet for resetting meals back to unmarked
- Increased swipe-to-complete threshold from 100px to 140px
- Fixed remaining meals ordering: uncompleted slots now sort before completed (by template position)
- Fixed "Clear status" button being cut off on mobile (increased sheet max-height + safe area padding)

### Files Changed
- [frontend/src/components/mealframe/meal-card-gesture.tsx](frontend/src/components/mealframe/meal-card-gesture.tsx) - Module-level completion cooldown (400ms), clear touchStartRef in cancelGesture, increased swipe threshold 100→140px
- [frontend/src/components/mealframe/completion-sheet-animated.tsx](frontend/src/components/mealframe/completion-sheet-animated.tsx) - Added `onClear` prop and "Clear status" button, increased max-height 60→70vh, safe area padding h-8→h-16
- [frontend/src/app/page.tsx](frontend/src/app/page.tsx) - Added `handleClearStatus` callback, sort remaining slots (uncompleted first by position, then completed by position)

### Decisions
- Module-level `lastCompletionTime` variable used as cross-instance guard to prevent cascading — simpler than React context for a single timestamp
- "Clear status" button uses dashed border style to visually separate from the 5 status options
- Remaining meals sorted uncompleted-first so clearing a status moves the card back to its natural position
- Yesterday Review modal not affected (doesn't pass `onClear`)

### Blockers
- None

### Next
- Consider Phase 2 features: user auth or grocery list generation

---

## Session: 2026-02-08

**Role**: backend + frontend
**Task**: Extended macro display + daily totals + average daily stats
**Branch**: feat/extended-macros-display

### Summary
- Added sugar_g, saturated_fat_g, fiber_g to all macro displays across the app
- Added daily macro totals row to Week view day cards and Today view header
- Added average daily calories and protein cards to Stats page
- Fixed Pydantic Decimal string serialization causing JS string concatenation in reduce operations

### Files Changed
- [backend/app/services/today.py](backend/app/services/today.py) - Pass extended macros to MealCompact
- [backend/app/api/weekly.py](backend/app/api/weekly.py) - Pass extended macros to MealCompact
- [backend/app/schemas/meal.py](backend/app/schemas/meal.py) - Add extended fields to MealListItem
- [backend/app/api/meals.py](backend/app/api/meals.py) - Pass extended fields when constructing MealListItem
- [backend/app/schemas/stats.py](backend/app/schemas/stats.py) - Add avg_daily_calories/protein to StatsResponse
- [backend/app/services/stats.py](backend/app/services/stats.py) - New _calculate_avg_daily_macros function
- [frontend/src/lib/types.ts](frontend/src/lib/types.ts) - Add extended macro fields to all type interfaces
- [frontend/src/components/mealframe/meal-card.tsx](frontend/src/components/mealframe/meal-card.tsx) - Show all 7 macros
- [frontend/src/components/mealframe/meal-card-gesture.tsx](frontend/src/components/mealframe/meal-card-gesture.tsx) - Show all 7 macros
- [frontend/src/components/mealframe/day-card-expandable.tsx](frontend/src/components/mealframe/day-card-expandable.tsx) - Extended Meal interface, daily totals, expanded meal macros
- [frontend/src/app/page.tsx](frontend/src/app/page.tsx) - Daily macro totals in header, Number() conversion for props
- [frontend/src/app/week/page.tsx](frontend/src/app/week/page.tsx) - Number() conversion in mapSlotsToMeals
- [frontend/src/app/meals/page.tsx](frontend/src/app/meals/page.tsx) - Show all 7 macros in list items
- [frontend/src/app/stats/page.tsx](frontend/src/app/stats/page.tsx) - Avg daily calories + protein cards

### Decisions
- Pydantic Decimal fields serialize as strings in JSON; must use Number() in frontend
- Daily totals show all 7 macros (compact row with abbreviations: P, C, F, sugar, sat.F, fiber)
- Stats page shows only avg calories and protein (not all macros)
- Math.round() applied to totals for clean integer display

### Blockers
- Pre-existing test failures in test_today_api.py and test_weekly_api.py (MultipleResultsFound database state issue) — not related to this work

### Next
- Fix pre-existing test database state isolation issue
- Consider Phase 2 features: user auth or grocery list generation

---

## Session: 2026-02-07 (Quick Fix)

**Role**: backend + docs
**Task**: CSV import auto-create missing meal types
**Branch**: main (direct commits)

### Summary
- Implemented auto-creation of missing meal types during CSV import
- Changed behavior from "skip with warning" to "create and assign with info message"
- Updated MealImportSummary schema to include `created_meal_types` list
- Import now tracks which meal types were created and shows them in the response
- Updated MEAL_IMPORT_GUIDE.md to reflect new behavior and remove friction

### Files Changed
- [backend/app/services/meals.py](backend/app/services/meals.py) - Auto-create meal types (lines 207-226)
- [backend/app/schemas/meal.py](backend/app/schemas/meal.py) - Added created_meal_types field to MealImportSummary
- [docs/frozen/MEAL_IMPORT_GUIDE.md](docs/frozen/MEAL_IMPORT_GUIDE.md) - Updated behavior description and examples

### Implementation Details
- When CSV references unknown meal type, create it with just `name` field
- Add to lookup dict immediately to avoid duplicates within same import
- Track created types and log info message: "Created new meal type: '{name}'"
- Case-sensitive: "Breakfast" and "breakfast" are different types
- All part of same transaction (rolled back if import fails)

### Decisions
- Meal types created with minimal data (name only, no description/tags)
- Info message logged as "warning" (existing pattern, non-fatal informational)
- Created types shown in summary.created_meal_types array
- No special UI handling needed - users see the info in warnings list

### Next
- User can re-import meals without pre-creating meal types
- Consider future enhancement: bulk edit meal type properties after import

---

## Session: 2026-02-07 (Planning)

**Role**: planning + code audit
**Task**: Verify CSV import meal type handling
**Branch**: main

### Summary
- User successfully imported 11 meals from converted spreadsheet data to homelab instance
- Audited CSV import code to verify meal type auto-creation behavior
- Found that `import_meals_from_csv` does NOT auto-create missing meal types
- Current behavior: logs warning and skips meal type assignment (line 210-212 in meals.py)
- Moved "CSV import: auto-create missing meal types" from Later to Next (Quick Fixes) in ROADMAP
- Cleaned up temporary files (CSV data and conversion script)

### Files Changed
- [docs/ROADMAP.md](docs/ROADMAP.md) - Moved meal type auto-creation to Quick Fixes section
- Deleted: `data/import/*.csv` (meals, ingredients, meals_ingredients, mealframe_import)
- Deleted: `scripts/convert_spreadsheet_meals.py`

### Findings
- CSV import at [backend/app/services/meals.py:207-212](backend/app/services/meals.py#L207-L212) skips unknown meal types with warning
- Behavior documented in MEAL_IMPORT_GUIDE.md as "Unknown meal types are logged as warnings, meal is still created"
- This matches spec but creates friction: users must pre-create all meal types before import

### Next
- Consider implementing auto-creation of missing meal types during CSV import
- Alternative: Update UI to show which meal types are missing before import

---

## Session: 2026-02-07 (Continued)

**Role**: backend + frontend + bugfix
**Task**: Extended nutrients UI + day template fix + auto-default week plan
**Branch**: main (direct commits)

### Summary
- Fixed critical day template save bug (0-based vs 1-based position indexing)
- Added sugar_g, saturated_fat_g, fiber_g input fields to meal editor UI
- Fixed local development environment (.env with correct DB port 5436)
- Implemented auto-default logic: first created week plan automatically becomes default
- Diagnosed week view issue: expected behavior when setup incomplete

### Files Changed
- `frontend/src/components/mealframe/day-template-editor.tsx` - Fixed 0-based indexing bug
- `frontend/src/components/mealframe/meal-editor.tsx` - Added 3 new nutrient input fields
- `frontend/src/app/meals/page.tsx` - Updated save/edit handlers for new fields
- `backend/app/services/week_plans.py` - Added auto-default logic for first week plan
- `backend/.env` - Created with correct DATABASE_URL (port 5436)

### Decisions
- Day template positions must be 1-based (backend validation requirement)
- First week plan auto-defaults to eliminate "No default week plan" error
- Week view failure is expected behavior when setup incomplete (not a bug)

### Blockers
- None

### Next
- Complete setup flow: create meal types → day templates → week plan
- Import 11 meals from CSV
- Consider implementing ADR-010 for frontend nutrient display

---

## Session: 2026-02-07

**Role**: backend + data migration
**Task**: Add extended nutritional fields + import user meal data
**Branch**: main (direct commits)

### Summary
- Added `sugar_g`, `saturated_fat_g`, `fiber_g` fields to Meal model
- Created Alembic migration for new columns (auto-runs on deploy)
- Updated all backend schemas and services to handle new fields
- Updated CSV import dialog in frontend to show new fields
- Created ADR-010 proposing frontend display options for extended nutrients
- Helped user convert spreadsheet meal data to MealFrame CSV format (11 meals)
- Added ROADMAP item: CSV import should prompt to create missing meal types

### Files Changed
- `backend/app/models/meal.py` - Added 3 new columns
- `backend/app/schemas/meal.py` - Updated all schemas (MealBase, MealUpdate, MealCompact, MealImportRow)
- `backend/app/services/meals.py` - Updated import/create/update functions
- `backend/alembic/versions/20260206_add_nutrient_fields_to_meal.py` - New migration
- `frontend/src/components/mealframe/csv-importer.tsx` - Updated import dialog text
- `docs/ADR.md` - Added ADR-010
- `docs/ROADMAP.md` - Added CSV import enhancement
- `data/import/mealframe_import.csv` - User's meal data (11 meals)
- `scripts/convert_spreadsheet_meals.py` - Conversion script (not committed)

### Decisions
- Extended nutrients are optional fields (backward compatible)
- Migration will run automatically on deploy via `entrypoint.sh`
- Frontend display of new nutrients deferred to ADR-010 discussion
- ADR-010 proposes context-dependent display (compact in Today View, full in Library)

### Blockers
- None

### Next
- User will import the 11 meals via CSV import once deployment completes
- Consider implementing ADR-010 Option D (context-dependent nutrient display)
- May add more meals to the import CSV based on user's ingredient database

---

## Session: 2026-02-04 (Pivot)

**Type**: Pivot session
**Trigger**: MVP complete, need to assess documentation and plan Phase 2

### Documents Reviewed
- ROADMAP.md - Accurate, MVP work complete
- SESSION_LOG.md (last 5 entries) - Consistent progress, no blockers
- VISION.md - Outdated, still referred to MVP as current
- OVERVIEW.md - Missing Yesterday Review, deployment details generic
- ADR.md - ADR-008 (grocery list) appropriately documented as proposed

### Changes Made
- **VISION.md**: Added "Current Phase Status" section marking MVP as complete with deployment date and feature summary
- **OVERVIEW.md**: Updated deployment section with actual architecture (NPM, split DNS, auto-deploy); clarified Yesterday Review modal description
- **ADR.md**: Added ADR-009 for User Management - documents authentication options for multi-user support
- **ROADMAP.md**: Updated phase to "MVP Complete - Evaluating Phase 2"; added two next task options (user management, grocery lists)

### Decisions Made
- MVP is officially complete as of 2026-02-02 deployment
- Two Phase 2 priorities identified: user management (ADR-009) and grocery lists (ADR-008)
- User management required before exposing app to additional users

### Impact
- Documentation now accurately reflects project state
- Clear path forward for Phase 2 work
- ADR-009 provides framework for authentication discussion

### Next
- Decide between user management or grocery list as first Phase 2 feature
- If user management: resolve questions in ADR-009 (scope, auth method)
- If grocery list: resolve questions in ADR-008 (parsing strategy)

---

## Session: 2026-02-03 (16)

**Role**: frontend
**Task**: "Yesterday Review" modal on morning open
**Branch**: feat/yesterday-review-modal

### Summary
- Built yesterday review modal that prompts users to catch up on unmarked meals from the previous day
- Modal appears on first Today View visit each calendar day if yesterday has unmarked slots
- Users can mark status for each meal or dismiss to skip for today
- Dismissal preference saved in localStorage, scoped to current date
- Created TanStack Query hooks for fetching yesterday data and completing slots
- Added 6 E2E tests covering modal appearance, dismissal, and completion flows

### Files Changed
**Frontend (new):**
- [frontend/src/components/mealframe/yesterday-review-modal.tsx](frontend/src/components/mealframe/yesterday-review-modal.tsx) - Modal component with expandable meal cards and status buttons
- [frontend/src/hooks/use-yesterday-review.ts](frontend/src/hooks/use-yesterday-review.ts) - Hooks for yesterday data, first-visit tracking, and slot completion

**Frontend (modified):**
- [frontend/src/app/page.tsx](frontend/src/app/page.tsx) - Integrated yesterday review modal into Today View

**E2E Tests:**
- [frontend/e2e/helpers.ts](frontend/e2e/helpers.ts) - Added getYesterday, resetYesterdayCompletions, completeAllYesterdaySlots helpers
- [frontend/e2e/yesterday-review.spec.ts](frontend/e2e/yesterday-review.spec.ts) - 6 tests for modal behavior

### Implementation Details
- Modal uses existing `/api/v1/yesterday` endpoint (already existed)
- First-visit tracking via localStorage key `mealframe_yesterday_review_dismissed` with today's date
- Modal auto-closes when all yesterday's slots are marked
- Compact status buttons (Followed, Adjusted, Skipped, Replaced, Social) in expandable cards
- Optimistic updates for completing yesterday's slots

### Decisions
- Show modal on first Today View visit per calendar day (not app launch)
- Dismissing modal leaves meals unmarked (user can catch up via Week View later)
- No time cutoff - show review whenever first opened that day
- Modal slides up from bottom (consistent with CompletionSheet pattern)

### Testing Performed
- Frontend build passes (8 static pages)
- 26 E2E tests discovered (6 new yesterday-review tests)
- TypeScript compilation clean

### Status: COMPLETE

### Next
- Pick next task from Later section in ROADMAP

---

## Session: 2026-02-02 (15)

**Role**: devops
**Task**: Enable SSH-based auto-deployment from GitHub Actions
**Branch**: feat/ssh-auto-deploy

### Summary
- Switched from webhook-based to SSH-based deployment (same approach as finance-dashboard)
- Updated GitHub Actions workflow to use appleboy/ssh-action for direct SSH deployment
- Updated deploy.sh to use the NPM-compatible docker-compose config
- Removed webhook infrastructure (hooks.json.template, webhook service setup)
- Updated all deployment documentation to reflect SSH-based approach

### Files Changed
**GitHub Actions:**
- [.github/workflows/deploy.yml](.github/workflows/deploy.yml) - Replaced webhook curl with SSH-based deployment using appleboy/ssh-action

**Deployment Scripts:**
- [deploy/deploy.sh](deploy/deploy.sh) - Updated to use NPM-compatible compose files, added DEPLOY_DIR env var
- [deploy/ct-setup.sh](deploy/ct-setup.sh) - Removed webhook service setup, added git install

**Documentation:**
- [deploy/QUICK_START.md](deploy/QUICK_START.md) - Replaced webhook setup with SSH key and port forwarding instructions
- [deploy/README.md](deploy/README.md) - Updated architecture diagram and deployment flow for SSH approach

**Deleted:**
- deploy/hooks.json.template - No longer needed with SSH deployment

### GitHub Secrets Required
| Secret | Purpose |
|--------|---------|
| `HOMELAB_SSH_KEY_BASE64` | Base64-encoded SSH private key for deployment |
| `HOMELAB_WAN_IP` | Public IP or DDNS hostname of homelab |
| `HOMELAB_SSH_PORT` | SSH port (forwarded through router) |
| `HOMELAB_USERNAME` | SSH username (e.g., root) |

### Why SSH over Webhook
- More reliable: SSH is a proven, battle-tested protocol
- Simpler secrets: Reuses existing SSH infrastructure (same as finance-dashboard)
- Better debugging: Can see full deployment output in GitHub Actions logs
- No extra service: Don't need webhook listener running on CT

### Router Configuration Required
- Forward external SSH port (e.g., 2222) to CT's SSH port 22 at 192.168.1.100

### Status: COMPLETE ✅

### Issues Resolved
- GitHub Actions runner unavailable (GitHub infrastructure outage - resolved by waiting)
- Docker permission denied for user `jure` → Fixed with `sudo usermod -aG docker jure`
- Base64 encoding issues on macOS → Fixed with `base64 -b 0` flag (no line wrapping)

### Next
- Pick next task from Later section in ROADMAP

---

## Session: 2026-02-02 (14)

**Role**: infrastructure/devops
**Task**: Homelab deployment with Nginx Proxy Manager
**Branch**: main (direct commits)

### Summary
- Deployed MealFrame to Proxmox VM (192.168.1.100) with production Docker Compose
- Configured Nginx Proxy Manager (192.168.1.50) as reverse proxy with SSL
- Fixed backend API connectivity issue (NPM couldn't reach FastAPI)
- Configured split DNS in OPNsense to avoid DNS rebind warnings
- App now accessible at https://meals.bordon.family from anywhere

### Files Changed
**Deployment Configuration (created):**
- [deploy/TROUBLESHOOTING_BACKEND.md](deploy/TROUBLESHOOTING_BACKEND.md) - Comprehensive backend connectivity troubleshooting guide
- [deploy/diagnose.sh](deploy/diagnose.sh) - Automated diagnostic script for quick issue detection
- [deploy/NPM_FIX.md](deploy/NPM_FIX.md) - Step-by-step NPM proxy configuration fix

**Deployment Configuration (modified):**
- [docker-compose.npm.yml](docker-compose.npm.yml:22-23) - Exposed API container on port 8003 for NPM to reach
- [deploy/QUICK_START.md](deploy/QUICK_START.md) - Added troubleshooting section references
- [deploy/README.md](deploy/README.md) - Added backend connectivity troubleshooting section

**Documentation:**
- [docs/ROADMAP.md](docs/ROADMAP.md) - Added auto-deployment enablement to Next queue, documented completed work

### Implementation Details
**Problem:**
- Frontend loaded through domain but API calls returned 404
- Next.js standalone doesn't proxy `/api/` requests in production
- NPM was only forwarding to web container (port 3000), not the API

**Solution:**
1. Exposed API container on port 8003 in production Docker Compose
2. Configured NPM Advanced tab with nginx location block for `/api/`
3. NPM now routes:
   - `/` → web:3000 (Next.js frontend)
   - `/api/*` → api:8003 (FastAPI backend)

**DNS Configuration:**
- Split DNS in OPNsense: `meals.bordon.family` → 192.168.1.50 (NPM) on local network
- DNS rebind exception added for `meals.bordon.family`
- External traffic routes through public IP → router port forward → NPM

### Decisions
- Chose to expose API port (8003) rather than bundle Nginx in web container (simpler architecture)
- NPM handles all routing and SSL termination (single point of configuration)
- Split DNS preferred over disabling DNS rebind check (maintains security)
- Created comprehensive troubleshooting docs for future reference

### Architecture
```
Browser → meals.bordon.family
  ↓ (DNS: local=192.168.1.50, external=public IP)
  ↓
NPM (192.168.1.50) - SSL termination, reverse proxy
  ↓
  ├─→ Web: 192.168.1.100:3000 (Next.js)
  └─→ API: 192.168.1.100:8003 (FastAPI)
```

### Troubleshooting Journey
1. Initial issue: API returned OPNsense error (port forwarding reached firewall instead of NPM)
2. Second issue: Frontend loaded but API 404 (NPM not configured for /api/ routing)
3. Third issue: DNS rebind warning from OPNsense (local network accessing domain that resolves to local IP)
4. Solutions applied in order, each resolving one layer of the problem

### Testing Performed
- Verified containers running: `docker ps` shows all 3 containers up
- Local API test: `curl http://localhost:8003/api/v1/meal-types` returns `[]`
- Domain API test: `curl -k https://meals.bordon.family/api/v1/meal-types` returns `[]`
- Browser access: Frontend loads, app functional (empty database)
- Mobile access: Works from external network via mobile data

### Status: COMPLETE

### Next
- Enable auto-deployment webhook in GitHub Actions (uncomment webhook call in deploy.yml)
- Optionally: Set up port forwarding or NPM proxy for webhook endpoint (port 9000)
- Populate database with initial meal data through web interface

---

## Session: 2026-02-01 (13)

**Role**: frontend
**Task**: Fix: Undo action for completed meals (wrong status selected)
**Branch**: fix/undo-completion-status

### Summary
- Users can now tap completed meals to change their status (not just undo to pending)
- CompletionSheetAnimated shows "Change status" header when editing existing completion
- Current status highlighted with "Current" badge and ring indicator
- Toast message says "Changed to {status}" when editing vs "Marked as {status}" for new
- Existing undo-to-pending via toast button preserved

### Files Changed
**Frontend (modified):**
- [frontend/src/app/page.tsx](frontend/src/app/page.tsx) - Allow tapping completed meals, pass currentStatus to sheet
- [frontend/src/components/mealframe/completion-sheet-animated.tsx](frontend/src/components/mealframe/completion-sheet-animated.tsx) - Added currentStatus prop, "Change status" header, "Current" badge

**E2E Tests (modified):**
- [frontend/e2e/daily-flow.spec.ts](frontend/e2e/daily-flow.spec.ts) - Added test for status change flow

### Implementation Details
- Completed meals now have `onClick` handler (previously `undefined`)
- CompletionSheetAnimated receives `currentStatus` prop to detect edit mode
- `isEditing` flag triggers different header text and "Current" badge display
- `wasAlreadyCompleted` check in handler determines toast message wording
- Quick-complete gestures (long-press, swipe) remain disabled for completed meals

### Decisions
- Option C implemented: both undo (reset to pending via toast) and direct status change (tap meal)
- "Current" badge uses subtle `ring-2 ring-foreground/20` to indicate without being too prominent
- Kept animation for status changes (same celebration animation as initial completion)

### Testing Performed
- Frontend build passes with no TypeScript errors
- Added E2E test: "Tapping completed meal allows status change"
- Existing "Undo via toast resets completion" test still valid

### Status: COMPLETE

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
