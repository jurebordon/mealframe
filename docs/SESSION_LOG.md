# Session Log

> Append-only journal of development sessions. Newest entries first.
> Each session gets one entry - prepend new entries at the top.

---

## [infrastructure] 2026-04-13

**Task**: Today View quick fixes — safe-area bottom padding + change-meal photo-capture option [feature: infrastructure]
**Branch**: feat/ai-onboarding

### Summary
- Fix 1: Extended `<main>` bottom padding in `app-shell.tsx` from `pb-16` to `pb-[calc(4rem+env(safe-area-inset-bottom))]` so the scroll buffer matches the fixed bottom nav, which has its own `pb-safe` home-indicator inset. Previously the last in-flow element (e.g. "Add meal" button on Today View) was occluded on iPhones.
- Fix 2: The "Change meal" action from the completion sheet used to jump directly into the library `MealPicker`. Now it opens a chooser (library vs photo capture) matching the "Add meal" pattern. Photo path reuses `AiCaptureSheet` with `skipAdhocSlot`, then calls the existing `reassignSlotMutation` with the captured meal id.
- Generalized `AddMealSheet` with optional `title` / label / description props so it renders both "Add meal" and "Change meal" flows from one component. Defaults preserve existing call-site behavior.

### Files Changed
- `frontend/src/components/navigation/app-shell.tsx` — main padding uses safe-area calc
- `frontend/src/components/mealframe/add-meal-sheet.tsx` — optional title/label/description props
- `frontend/src/app/(app)/page.tsx` — change-meal chooser state, handlers (`handleChangeMealFromLibrary`, `handleChangeMealCapturePhoto`, `handleChangeMealPhotoSaved`), dedicated `changeMealCaptureRef`, and two new render blocks (chooser sheet + change-meal AiCaptureSheet)

### Decisions
- Put the padding fix in `app-shell.tsx` (layout) rather than `page.tsx` so every authenticated route benefits, not just Today View.
- Reused `AddMealSheet` via optional props instead of creating a new `ChangeMealSheet` component — same visual pattern, no duplication. `DeviatedMealSheet` remains a separate component since its third "Skip" option doesn't fit the two-button chooser.
- Change-meal photo path uses a separate `AiCaptureSheet` instance with its own ref (`changeMealCaptureRef`) so it doesn't collide with the add-meal or deviated capture sheets. Critical for iOS Safari gesture handling.
- "Changed to X" toast from library path vs. generic "Meal changed" from photo path (photo flow doesn't know the meal name at trigger time).

### Blockers
- None

### Next
- Session 2: Nutrition lookup services — USDA FoodData Central + Open Food Facts API clients

---

## [ai-onboarding] 2026-04-08

**Task**: Session 1: DB foundation — `onboarding_state` table + state CRUD API [feature: ai-onboarding]
**Branch**: feat/ai-onboarding

### Summary
- Created `onboarding_state` table with JSONB columns for intake answers, generated setup, chat messages, tool log, imported meals
- Added CHECK constraint on status column (7 valid values) and partial unique index enforcing one active onboarding per user
- Built full CRUD API with singleton resource pattern (no ID in URL — one active per user)
- Service layer includes state machine transition validation (e.g., intake→generating allowed, intake→completed rejected)
- 17 integration tests covering all 5 endpoints, state transitions, conflict handling, and abandon/recreate flow

### Files Changed
- `backend/app/models/onboarding_state.py` — new SQLAlchemy model
- `backend/alembic/versions/20260407_add_onboarding_state.py` — new migration
- `backend/app/schemas/onboarding.py` — response, update, status schemas
- `backend/app/services/onboarding.py` — state CRUD with transition validation
- `backend/app/api/onboarding.py` — 5 endpoints (GET/POST/PATCH/DELETE state + GET status)
- `backend/tests/test_onboarding_state.py` — 17 integration tests
- `backend/app/models/__init__.py` — registered OnboardingState
- `backend/app/api/__init__.py` — registered onboarding_router
- `backend/app/main.py` — included onboarding_router

### Decisions
- Singleton resource pattern: no `{id}` in URLs since only one active onboarding exists per user
- State machine in service layer (not DB triggers): keeps logic testable and explicit
- JSONB replace semantics (no deep merge): frontend sends full objects, simpler to reason about
- `tool_log` excluded from API response (backend-only field for debugging)
- Partial unique index (`WHERE status NOT IN ('completed', 'abandoned')`) allows onboarding history while preventing duplicates

### Blockers
- None

### Next
- Session 2: Nutrition lookup services — USDA FoodData Central + Open Food Facts API clients

---

## [infrastructure] 2026-03-31

**Task**: Fix daily macro totals including skipped meals on Today View [feature: infrastructure]
**Branch**: feat/ai-onboarding

### Summary
- Fixed bug where skipped meals were still counted in the daily macro totals on the Today View
- Added `macroMeals` derived array that filters out skipped slots and uses `actual_meal` macros for deviated meals
- Replaced all 7 inline reduce calls with the filtered calculation

### Files Changed
- `frontend/src/app/(app)/page.tsx` — macro total calculation now excludes skipped, uses actual_meal for deviated

### Decisions
- Deviated meals with `actual_meal` linked now show the actual meal's macros instead of the planned meal's
- Skipped meals are fully excluded from all macro sums (calories, protein, carbs, sugar, fat, saturated fat, fiber)

### Blockers
- None

### Next
- Session 1: DB foundation — `onboarding_state` table + state CRUD API

---

## [ai-onboarding] 2026-03-29

**Task**: ADR-015 — AI-Powered Onboarding feature planning and setup [feature: ai-onboarding]
**Branch**: feat/ai-onboarding

### Summary
- Designed complete AI-powered onboarding feature through detailed requirements discussion
- Created feature SPEC with frozen requirements, acceptance criteria, and success metrics
- Added ADR-015 documenting architectural decisions: dual LLM provider (Claude Sonnet for reasoning, GPT-4o for vision), USDA+OFF for nutrition data, server-side state persistence, standard SSE streaming
- Updated ROADMAP with 9 sessions on long-lived `feat/ai-onboarding` branch
- Created feature branch `feat/ai-onboarding` from main

### Files Changed
- `docs/feature_docs/ai_onboarding/SPEC.md` — new feature SPEC
- `docs/ADR.md` — ADR-015 entry
- `docs/ROADMAP.md` — 9 onboarding sessions in "Now", dependency graph updated to Wave 4

### Decisions
- Claude Sonnet 4 (Anthropic SDK) for onboarding generation + chat; GPT-4o kept for vision only
- USDA FoodData Central + Open Food Facts for real nutrition data, exposed as AI-callable tools
- Server-side `onboarding_state` table with conversation memory, tool log, resume capability
- Hybrid UX: structured intake cards (6 questions) → AI generation → summary review → chat-based meal import
- Standard SSE (not Vercel-proprietary) for native mobile client portability
- Single long-lived feature branch, merged to main only when complete
- Vercel AI SDK `useChat` for frontend streaming chat

### Blockers
- None

### Next
- Session 1: DB foundation — `onboarding_state` table, Alembic migration, state CRUD API endpoints

---

## [ai-capture] 2026-03-29

**Task**: ADR-013 Session 4 — User meal context injection into vision prompt [feature: ai-capture]
**Branch**: feat/ai-capture-session-4

### Summary
- Added `get_meal_context_for_prompt()` — lightweight query fetching user's 30 most recent meals (name + portion_description only)
- Extended `build_vision_prompt()` to inject user meal library as context block with instruction to prefer user's naming
- Added rule: "If the food matches a meal from the user's library, use their exact meal_name and adjust portions to what you see in the photo"
- Threaded `user_meals` parameter through `analyze_food_image()` and the `/ai-capture` route handler
- Created `test_ai_capture.py` with 11 tests (6 unit for prompt builder, 5 integration for DB query)
- Fixed test DB schema — applied missing `source`, `confidence_score`, `image_path`, `ai_model_version` columns and stamped alembic

### Files Changed
- `backend/app/services/ai_capture.py` — `get_meal_context_for_prompt()`, extended `build_vision_prompt()` and `analyze_food_image()`
- `backend/app/api/meals.py` — fetch meal context in route handler, pass to service
- `backend/tests/test_ai_capture.py` — new test file (11 tests)

### Decisions
- 30 meal limit: ~1500 extra prompt tokens, negligible for GPT-4o 128k context
- Most recent ordering (`created_at DESC`): recent meals more likely to be re-eaten
- Name + portion only: macros would bloat prompt without helping visual recognition
- No meal type filtering: can't know meal type before analysis

### Blockers
- None

### Next
- ADR-008 (Grocery List) Session 1: `needs_groceries` DB foundation + template editor toggle

---

## [ai-capture] 2026-03-29

**Task**: ADR-013 Session 3 — Frontend deviated meal display + history [feature: ai-capture]
**Branch**: feat/ai-capture-session-3

### Summary
- Added `source` field to frontend `MealListItem` and `MealResponse` types (aligned with backend schema)
- Added "AI" badge on meal cards in Meals Library for `ai_capture` meals
- Added Source filter dropdown (All / Manual / AI Captured) in Meals Library filter bar
- Added `source` param to `getMeals()` API function and `useMeals` hook
- Threaded `actualMealId` through `useCompleteSlot` mutation to support `actual_meal_id` on deviated completions
- Added `skipAdhocSlot` prop to `AiCaptureSheet` — allows create-only mode without adding adhoc slot
- Created `DeviatedMealSheet` component: "What did you eat instead?" with Pick from Library / Capture with Photo / Skip
- Wired deviated flow in Today View: selecting "Deviated" now opens DeviatedMealSheet instead of immediately completing
- Three deviated paths: library picker → actual_meal_id, AI capture → create meal + actual_meal_id, skip → deviated without linking
- Added "Actually ate: {name}" annotation on deviated slots in Today View

### Files Changed
- `frontend/src/lib/types.ts` — source fields on MealListItem, MealResponse
- `frontend/src/lib/api.ts` — source param in getMeals
- `frontend/src/hooks/use-meals.ts` — source in UseMealsParams
- `frontend/src/hooks/use-today.ts` — actualMealId in useCompleteSlot
- `frontend/src/app/(app)/meals/page.tsx` — source badge + source filter
- `frontend/src/app/(app)/page.tsx` — deviated flow orchestration + actual_meal annotation
- `frontend/src/components/mealframe/ai-capture-sheet.tsx` — skipAdhocSlot prop
- `frontend/src/components/mealframe/deviated-meal-sheet.tsx` — new component

### Decisions
- Deviated flow uses a separate `DeviatedMealSheet` rather than extending CompletionSheetAnimated — cleaner separation of concerns
- Second `AiCaptureSheet` instance with `skipAdhocSlot` for deviated capture — avoids complex conditional logic in a single instance
- iOS Safari file picker trigger pattern reused for deviated capture path (synchronous `.click()` in user gesture handler)

### Blockers
- None

### Next
- ADR-013 Session 4 (optional): User meal context injection into vision prompt
- Or move to ADR-008 (Grocery List) Session 1

---

## [auth] 2026-03-22

**Task**: ADR-014 Session 6 — Google OAuth integration [feature: auth]
**Branch**: direct to main

### Summary
- Implemented Google OAuth via authlib OIDC authorization code flow
- Backend: `/auth/google/enabled`, `/auth/google/authorize`, `/auth/google/callback` endpoints
- OAuth service: Google OIDC discovery, code exchange, ID token validation, user get-or-create with auto-linking
- Frontend: "Continue with Google" button on login/register pages (hidden when not configured)
- Frontend: `/oauth/callback` page handles redirect, stores token, fetches profile
- Auto-links Google account to existing email/password users (safe — Google verifies email)
- No new migration needed — `google_sub` and `auth_provider` columns already existed

### Files Changed
- `backend/requirements.txt` — added authlib
- `backend/app/config.py` — Google OAuth config vars
- `backend/app/services/oauth.py` — new OAuth service
- `backend/app/api/auth.py` — 3 new OAuth routes
- `backend/app/schemas/auth.py` — GoogleOAuthEnabledResponse
- `frontend/src/components/auth/google-sign-in-button.tsx` — new shared component
- `frontend/src/app/(auth)/login/page.tsx` — Google button + OAuth error display + Suspense
- `frontend/src/app/(auth)/register/page.tsx` — Google button
- `frontend/src/app/oauth/callback/page.tsx` — new callback handler
- `frontend/src/lib/auth-store.ts` — handleOAuthCallback action
- `docker-compose.yml`, `docker-compose.prod.yml` — Google env vars

### Decisions
- Server-side OIDC flow (not Google JS SDK) — secrets stay on backend
- In-memory state dict for CSRF tokens — sufficient for single-server deployment
- Conditional UI via `/auth/google/enabled` endpoint — graceful when not configured

### Blockers
- None

### Next
- ADR-013 Session 3: Frontend deviated meal display + history

---

<!--
## [feature-name] YYYY-MM-DD

**Role**: backend / frontend / qa / architecture
**Task**: [Task from ROADMAP.md with feature tag]
**Branch**: type/branch-name
**Feature**: feature-name

### Summary
- What was accomplished

### Files Changed
- path/to/file

### Decisions
- Any design decisions (consider ADR if significant)

### Blockers
- Issues encountered (or "None")

### Next
- Suggested focus for next session

---
-->

## [infrastructure] 2026-03-12

**Role**: frontend
**Task**: Mobile UI polish — 9 fixes from real-device iOS testing [feature: infrastructure]
**Branch**: direct to main (solo flow)

### Summary
- Fixed 9 mobile UX issues from iOS Safari real-device testing
- Stats chart: angled x-axis labels (-45deg), increased interval, reduced font size
- Bottom nav: removed `hover:text-foreground` on mobile (long-press ghost state)
- Settings gear: removed from global app-shell bar, moved to Setup page header only
- Template editor: prevented auto-focus, responsive slot rows, `overflow-x-hidden`
- Setup tabs: stacked description + action button vertically on mobile
- Today View: outline variant for "+ Add meal" button, removed pull-to-refresh hint
- Image compression: two-pass (1600px/0.80, fallback 1280px/0.70 if >8MB), errors now throw

### Files Changed
- `frontend/src/app/(app)/stats/page.tsx`
- `frontend/src/components/navigation/bottom-nav.tsx`
- `frontend/src/components/navigation/app-shell.tsx`
- `frontend/src/app/(app)/setup/page.tsx`
- `frontend/src/components/mealframe/day-template-editor.tsx`
- `frontend/src/app/(app)/page.tsx`
- `frontend/src/lib/api.ts`

### Decisions
- Settings gear in Setup only: cleaner than global bar
- Two-pass image compression covers 48MP phone cameras
- No pull-to-refresh text: iOS users expect native behavior

### Blockers
- None

### Next
- ADR-013 Session 3: Frontend deviated meal display + history (captured meals in library, source badge)

---

## [ai-capture] 2026-03-08

**Role**: frontend + debugging
**Task**: ADR-013 Session 2 — AI Capture Frontend UI [feature: ai-capture]
**Branch**: direct to main

### Summary
- Built `AddMealSheet` action sheet and full `AiCaptureSheet` state machine (idle/analyzing/confirming/error)
- Wired capture flow into Today View "Add Meal" button
- Backend: injected user's meal type names into vision prompt
- Fixed: iOS Safari file input `.click()` requires synchronous user gesture — `forwardRef` + `useImperativeHandle` pattern
- Fixed: sheet z-index overlapping bottom nav (z-50 → z-[60])
- Fixed: client-side image compression (canvas, max 1920px, JPEG 85%) before upload
- Fixed: docker-compose.prod.yml `!override` tag for volumes to prevent dev bind mount merge

### Files Changed
- `backend/app/services/ai_capture.py`, `backend/app/api/meals.py`
- `frontend/src/components/mealframe/add-meal-sheet.tsx` (new)
- `frontend/src/components/mealframe/ai-capture-sheet.tsx` (new)
- `frontend/src/app/(app)/page.tsx`, `frontend/src/lib/api.ts`, `frontend/src/lib/types.ts`
- `docker-compose.prod.yml`

### Decisions
- iOS Safari gesture: `forwardRef` exposes `triggerFilePicker()` to parent, called synchronously in `onClick`
- Client-side compression: canvas + `toBlob` at max 1920px, stays well under 10MB

### Blockers
- None

### Next
- ADR-013 Session 3: Frontend deviated meal display + history

---

## [ai-capture] 2026-03-05

**Role**: backend + architecture
**Task**: ADR-013 Session 1 — AI Infrastructure + LLM Backend [feature: ai-capture]
**Branch**: feat/ai-capture → merged to main

### Summary
- OpenAI GPT-4o vision integration: `analyze_food_image` with base64 encoding, structured JSON output
- Alembic migration: `source`, `confidence_score`, `image_path`, `ai_model_version` on `meal`; new `openai_usage` table
- `POST /meals/ai-capture` endpoint (stateless: analyze-only, does not auto-save)
- Image storage: resize to 1920px, JPEG q=85, local volume `/data/captures`
- Round-robin updated to exclude `source = "ai_capture"` meals from rotation
- Vision prompt injects date/time + Europe location context

### Files Changed
- `backend/requirements.txt`, `backend/app/config.py`
- `backend/app/services/ai_capture.py` (new), `backend/app/services/image_storage.py` (new)
- `backend/app/models/openai_usage.py` (new), `backend/app/models/meal.py`
- `backend/app/schemas/meal.py`, `backend/app/api/meals.py`
- `backend/app/services/round_robin.py`
- `docker-compose.yml`, `docker-compose.prod.yml`

### Decisions
- Chat Completions over Responses API: stateless single-turn image→JSON doesn't benefit from thread management
- No LLMService class yet: revisit when 3+ LLM features share the client

### Blockers
- None

### Next
- ADR-013 Session 2: Frontend capture UI

---

## [auth] 2026-03-03

**Role**: debugging + devops
**Task**: Fix auth form validation bug, Resend email setup, deployment fixes [feature: auth]
**Branch**: main (direct commits)

### Summary
- Fixed login "Required" validation bug: shadcn Input used React 19 pattern but project is React 18 — `forwardRef` missing, react-hook-form `ref` dropped silently
- Fixed Input and Textarea with `React.forwardRef`
- Set up Resend: domain verification (mealframe.io), DNS records (DKIM, SPF, MX, DMARC)
- Fixed deploy.sh container rename conflict by splitting build → down → up

### Files Changed
- `frontend/src/components/ui/input.tsx`, `frontend/src/components/ui/textarea.tsx`
- `docker-compose.prod.yml`, `deploy/deploy.sh`

### Decisions
- Input/Textarea need `forwardRef` in React 18 for react-hook-form `ref` to work

### Blockers
- None

### Next
- ADR-013 Session 1: LLM infrastructure + backend

---

## [auth] 2026-03-01

**Role**: backend + frontend
**Task**: ADR-014 Session 5 — Email verification, password reset, rate limiting [feature: auth]
**Branch**: feat/auth-session5

### Summary
- Resend email service with console fallback when API key unset
- EmailToken model (shared for verification + password reset, SHA-256 hashed, single-use)
- FailedLoginAttempt model for DB-persisted account lockout
- Rate limiting via slowapi: register (3/min), login (5/min), forgot-password (3/min)
- 3 new frontend pages: verify-email, forgot-password, reset-password
- 29 backend auth tests pass (was 15)

### Decisions
- Shared EmailToken table with `token_type` field — simpler than separate tables
- DB-persisted lockout over in-memory: survives server restarts, works across workers
- Forgot-password always returns 200 regardless of email existence (enumeration prevention)

---

## [auth] 2026-03-01

**Role**: frontend
**Task**: ADR-014 Session 4 — Frontend auth pages + auth store [feature: auth]
**Branch**: feat/auth-frontend

### Summary
- Zustand auth store with in-memory access token, HTTP-only cookie refresh
- API client token injection + auto-retry on 401 after refresh
- Login + register pages with react-hook-form + zod
- AuthGuard component wrapping all `(app)` routes
- Settings page + desktop sidebar user/logout UI

### Decisions
- Access token in memory only (not localStorage) — XSS protection
- Zustand over React Context: auth state must be readable from `api.ts` outside React tree
- `authFetch` separate from `fetchApi` to avoid circular dependency

---

## [auth] 2026-02-28

**Role**: backend
**Task**: ADR-014 Session 3 — Protect all API routes with mandatory auth [feature: auth]
**Branch**: feat/auth-route-protection

### Summary
- All 35+ endpoints require valid JWT via `get_current_user`
- All service functions filter by `user_id` for data isolation
- Ownership violations return 404 (not 403) to avoid leaking resource existence
- 4 new cross-user isolation tests; all 184 tests pass

---

## [auth] 2026-02-27

**Role**: backend
**Task**: ADR-014 Session 2 — Auth data migration [feature: auth]
**Branch**: feat/auth-data-migration

### Summary
- `user_id` FK (NOT NULL) added to 6 tables via Alembic multi-step migration: seed admin → add nullable → backfill → NOT NULL
- Per-user composite unique constraints (meal_type.name, day_template.name, week_start_date)
- round_robin_state PK changed to `(user_id, meal_type_id)`
- Deterministic admin UUID: `00000000-0000-4000-a000-000000000001`
- All 180 tests pass

---

## [auth] 2026-02-27

**Role**: backend
**Task**: ADR-014 Session 1 — Authentication backend [feature: auth]
**Branch**: feat/auth

### Summary
- User + RefreshToken models, Alembic migration
- Argon2id password hashing, JWT HS256 access tokens (15 min), rotated refresh tokens (7 days, HTTP-only cookie)
- Auth API: `/register`, `/login`, `/refresh`, `/logout`, `/me`
- 15 integration tests

### Decisions
- Custom auth over fastapi-users: narrow scope, full control more valuable for <50 users
- Refresh token in HTTP-only cookie scoped to `/api/v1/auth` path only

---

## [landing] 2026-02-25

**Role**: full-stack
**Task**: Waitlist landing page + privacy policy + self-hosted analytics [feature: landing]
**Branch**: feat/landing-page

### Summary
- Next.js route groups: `(app)` and `(landing)` separation
- Waitlist page at `/waitlist` with 6 sections, Google Apps Script integration, localStorage persistence
- Self-hosted pageview analytics: `POST /api/v1/analytics/pageview`, privacy-friendly IP hashing (SHA-256 daily salt)
- Privacy policy page at `/privacy`

### Decisions
- `geist` npm package (not `next/font/google`) — Geist not in Next.js 14
- `fetch` with `keepalive` over `sendBeacon` — CORS preflight issue with sendBeacon + JSON

---

## [meal-reassignment] 2026-02-23

**Role**: full-stack
**Task**: ADR-011 + ADR-012 — Meal reassignment + revised completion statuses [feature: meal-reassignment]
**Branch**: feat/meal-reassignment, feat/completion-statuses (git worktrees, merged to main)

### Summary
- ADR-011: `is_manual_override` column + `PUT /slots/{id}/reassign` endpoint + MealPicker in reassign mode
- ADR-012: Migration `adjusted→equivalent`, `replaced→deviated` + `actual_meal_id` FK + updated adherence formula
- Migration must drop CHECK constraint before renaming enum data values
- All 165 tests pass

---

## [architecture] 2026-02-20

**Role**: architecture
**Task**: Phase 2 planning — ADR-011 through ADR-014 [feature: infrastructure]
**Branch**: main (docs only)

### Summary
- Wrote ADR-011 (Meal Reassignment), ADR-012 (Completion Statuses), ADR-013 (AI Capture), ADR-014 (Auth)
- Established Wave 1/2/3/4 dependency graph

---

## Earlier sessions (see docs_archived/SESSION_LOG.md for full history)

Pre-2026-02-20 sessions include: Phase 1 MVP build (Jan 2026), deployment to homelab, all initial features.

<!-- Prepend new session entries above this line -->
