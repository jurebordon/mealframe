# Architecture Decision Records

> Append-only log of significant technical decisions. Newest entries first.

---

## ADR-001: Tech Stack Selection

**Date**: 2026-01-19
**Status**: Accepted
**Context**: Greenfield project, need to choose backend, frontend, and database technologies.

### Decision

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js 14+ (React, TypeScript)
- **Database**: PostgreSQL 15+
- **Deployment**: Docker Compose

### Rationale

**Backend (FastAPI)**:
- Async support for concurrent requests
- Automatic OpenAPI documentation
- Pydantic validation built-in
- Fast development velocity
- Python ecosystem for future ML/analytics

**Frontend (Next.js)**:
- PWA support via next-pwa
- SSR for fast initial load
- App Router for modern patterns
- TypeScript for type safety
- Large ecosystem

**Database (PostgreSQL)**:
- JSONB for flexibility (future feature flags, metadata)
- UUID support for distributed IDs
- Robust, mature, well-understood
- Strong constraints and validation

**Deployment (Docker Compose)**:
- Simple single-host deployment for MVP
- Easy local development environment
- Can migrate to Kubernetes later if needed

### Alternatives Considered

- **Django** - Too heavyweight, REST framework adds boilerplate
- **Node.js backend** - Less familiar, async patterns more verbose
- **MongoDB** - Don't need schema flexibility, prefer relational
- **SQLite** - Not suitable for concurrent writes
- **Native apps** - PWA sufficient for MVP, faster to develop

### Consequences

- Need to maintain two languages (Python + TypeScript)
- Docker Compose limits horizontal scaling (acceptable for MVP)
- PWA may have limitations vs native apps (will monitor)

---

## ADR-002: Round-Robin Algorithm for Meal Selection

**Date**: 2026-01-19 (from PRD)
**Status**: Accepted
**Context**: Need to assign meals to slots while providing variety without user decisions.

### Decision

Use simple round-robin rotation per Meal Type:
1. Order meals by `(created_at ASC, id ASC)` for determinism
2. Track last-used meal ID per Meal Type
3. Select next meal as `(last_index + 1) % total_meals`

### Rationale

- **Deterministic**: Same inputs always produce same outputs (easier to debug, test, reason about)
- **Fair**: Every meal gets equal rotation
- **Simple**: No complex algorithms or weights
- **Extensible**: New meals automatically enter rotation
- **Resilient**: Deleted meals don't break state (graceful degradation)

### Alternatives Considered

- **Random selection** - Not deterministic, harder to debug, users might see same meal twice
- **Smart rotation** (avoid recently used) - Added complexity, diminishing returns for MVP
- **Adherence-weighted** (deprioritize skipped meals) - Deferred to Phase 3

### Consequences

- Meals rotate predictably (might feel mechanical)
- No optimization for user preferences (Phase 3 feature)
- State management required (round_robin_state table)

---

## ADR-003: No Per-Meal Editing in Weekly Plans

**Date**: 2026-01-19 (from PRD)
**Status**: Accepted
**Context**: Users might want to swap individual meals in generated plans.

### Decision

Weekly plans are **read-only at the meal level**. Users can only:
- Switch entire day templates
- Mark days as "No Plan" overrides
- NOT swap individual meals

### Rationale

- **Preserves "no decisions" philosophy** - Allowing swaps reintroduces decision fatigue
- **Simpler data model** - No meal swap history or undo logic needed
- **Clearer UX** - One way to adapt: change the template
- **Sufficient flexibility** - Template switching handles schedule changes (workout cancelled, etc.)

### Alternatives Considered

- **Allow meal swaps** - Defeats core value proposition
- **"Skip this meal"** - Use completion status instead (mark as "skipped")
- **Manual meal picker** - Same as swaps, adds decision burden

### Consequences

- Users must accept assigned meals or change entire day
- Might feel restrictive to some users (monitor feedback)
- "No Plan" override is escape valve for exceptional days

---

## ADR-004: PWA Over Native Apps for MVP

**Date**: 2026-01-19 (from Tech Spec)
**Status**: Accepted
**Context**: Need mobile experience; choose between PWA or native iOS/Android apps.

### Decision

Build as PWA (Progressive Web App) using next-pwa, NOT native apps.

### Rationale

- **Single codebase** - One frontend serves both desktop and mobile
- **Faster development** - No App Store approvals, instant updates
- **Good enough for MVP** - Offline support, installable, home screen icon
- **Easy migration** - Can build React Native later if needed (shared API)

### Alternatives Considered

- **React Native** - Cross-platform but more complex, slower iteration
- **Native Swift/Kotlin** - Best UX but 2x development effort, App Store friction

### Consequences

- No push notifications (requires native or service worker tricks)
- Slightly worse performance vs native
- No watch app complications (deferred to Phase 3)
- Must ensure PWA capabilities meet user needs (monitor)

---

## ADR-005: Single-User MVP with Multi-User Data Model

**Date**: 2026-01-19 (from Tech Spec)
**Status**: Accepted
**Context**: Need to ship fast for personal use, but productization requires multi-user.

### Decision

- **No authentication in MVP** (single-user, localhost deployment)
- **But**: All tables include `user_id` column (nullable FK to future `users` table)
- Data model is multi-user ready; application logic is single-user

### Rationale

- **Ship faster** - No auth complexity (OAuth, sessions, password reset, etc.)
- **Easy migration** - When adding auth, just populate `user_id` and add WHERE clauses
- **Personal tool first** - Validate core value before productization

### Alternatives Considered

- **Multi-user from start** - Over-engineering for unvalidated product
- **No user_id columns** - Would require migration later (schema changes are risky)

### Consequences

- Must remember to scope queries by `user_id` when auth is added
- Current deployment is localhost-only (not secure for internet)
- Migration to multi-user is straightforward (well-defined path)

---

## ADR-006: Manual Weekly Generation

**Date**: 2026-01-19 (from PRD)
**Status**: Accepted
**Context**: When should weekly plans be generated?

### Decision

Manual trigger (user clicks "Generate Next Week"), typically Sunday evening.

### Rationale

- **Explicit control** - User decides when they're ready to plan
- **Simpler implementation** - No cron jobs or background workers needed
- **Review opportunity** - User can check upcoming week before committing

### Alternatives Considered

- **Auto-generate Sunday night** - Might generate during vacation, schedule changes
- **Auto-generate on first missing day** - Less predictable, surprises user

### Consequences

- User must remember to generate (acceptable for motivated user)
- No plan = app shows "no plan" message (not an error state)
- Future: Could add notification/prompt on Sunday evening

---

## ADR-009: User Management for Multi-User Access

**Date**: 2026-02-04
**Status**: Superseded by ADR-014
**Context**: To expose MealFrame to other users beyond the single-user MVP deployment, we need authentication and user management.

### Problem

The MVP was designed for single-user use (ADR-005). The data model includes nullable `user_id` columns for future multi-user support, but no authentication exists. To share the app with others, we need:
1. User registration and login
2. Session management
3. Data isolation (users only see their own data)
4. Secure deployment (currently relies on private network)

### Options Under Consideration

**Option A: Email/Password Authentication**
- Traditional registration with email verification
- Password hashing (bcrypt/argon2)
- JWT or session-based auth
- Pros: Full control, no external dependencies, familiar UX
- Cons: Password reset flow, security responsibility, spam registration

**Option B: OAuth Only (Google/Apple/GitHub)**
- Delegate authentication to trusted providers
- No password management
- Pros: Lower security burden, trusted providers, quick login
- Cons: Dependency on external services, users need accounts elsewhere

**Option C: Magic Link Authentication**
- Email-based passwordless login
- Send login link, valid for short time
- Pros: No passwords to manage, simple UX, secure
- Cons: Requires email service, friction for frequent logins

**Option D: Invite-Only with Simple Auth**
- Admin generates invite codes
- Users register with code + email/password
- Pros: Controlled growth, simple implementation
- Cons: Manual invite management, still need password infrastructure

### Questions to Resolve

1. How many users do we expect? (Family/friends vs. public)
2. Is self-registration required, or invite-only acceptable?
3. Do we need mobile-friendly OAuth (native app consideration)?
4. What's the timeline for multi-user support?
5. Do we want to support account linking (multiple auth methods)?

### Implementation Considerations

- All tables already have `user_id` columns (nullable)
- Need to populate `user_id` for existing data (migration)
- Add `WHERE user_id = :current_user` to all queries
- Consider using established library (e.g., `fastapi-users`, `authlib`)

### Next Steps

- Decide on initial user scope (family vs. public)
- Choose authentication method based on scope
- Prototype chosen approach in isolated branch

---

## ADR-008: Grocery List Ingredient Extraction Strategy

**Date**: 2026-02-03
**Status**: Proposed (Needs Discussion)
**Context**: Users want to generate a grocery list from the weekly meal plan. The challenge is extracting structured ingredient data from unstructured portion descriptions.

### Problem

Meals store portions as free-text strings (e.g., "2 eggs + 1 slice toast + 1 tbsp butter"). To generate a useful grocery list, we need to:
1. Parse these descriptions into individual ingredients
2. Optionally aggregate quantities across the week (e.g., "6 eggs" instead of "2 eggs x3")
3. Group items logically (produce, dairy, proteins, etc.)

### Options Under Consideration

**Option A: Simple Pass-Through (No Parsing)**
- Display each meal's portion description as-is, grouped by day
- Pros: Immediate implementation, no parsing errors
- Cons: No aggregation, no smart grouping, less useful

**Option B: Regex/Rule-Based Parsing**
- Parse common patterns: "2 eggs", "1 cup rice", "200g chicken"
- Maintain ingredient category mappings
- Pros: Deterministic, no API costs
- Cons: Brittle, requires maintenance, limited flexibility

**Option C: AI-Powered Extraction**
- Use LLM to parse portion descriptions into structured ingredients
- Could run on-demand or batch during week generation
- Pros: Handles natural language well, can categorize intelligently
- Cons: API costs, latency, dependency on external service

**Option D: Structured Ingredients Field**
- Add `ingredients` JSON field to meal model
- Users enter structured data during meal creation
- Pros: Clean data, reliable aggregation
- Cons: Migration required, more work during meal entry, existing meals need backfill

### Questions to Resolve

1. How accurate does parsing need to be? (80% good enough vs. perfect)
2. Is aggregation essential or nice-to-have?
3. What's the acceptable latency for generating a grocery list?
4. Should this work offline?
5. Budget for external API calls (if AI approach)?

### Next Steps

- Use the app for real meal planning to understand actual pain points
- Evaluate whether simple pass-through (Option A) is sufficient for MVP
- If not, prototype AI extraction with a few sample meals to assess quality

---

## ADR-007: Completion Statuses Are Optional

**Date**: 2026-01-19 (from PRD)
**Status**: Accepted
**Context**: Should users be forced to mark meals as complete?

### Decision

Completion tracking is **encouraged but not enforced**.

Unmarked meals (`completion_status = NULL`) are:
- Valid, not errors
- Excluded from adherence calculations
- Surfaced in "Yesterday Review" for catch-up

### Rationale

- **Forgiving UX** - Life happens, forgetting to mark isn't failure
- **Reduces friction** - App still useful even if tracking is inconsistent
- **Reflection over enforcement** - Stats show patterns, don't judge

### Alternatives Considered

- **Required completion** - Too rigid, creates guilt/friction
- **Auto-mark as skipped after time** - False assumptions (might eat later)

### Consequences

- Adherence stats might be incomplete (acceptable - they're for reflection)
- "Yesterday Review" prompts catch-up (gentle reminder)
- Streaks only count fully-tracked days (avoids gaming)

---

## ADR-010: Extended Nutritional Data Display

**Date**: 2026-02-06
**Status**: Proposed (Needs Discussion)
**Context**: The meal model now supports `sugar_g`, `saturated_fat_g`, and `fiber_g` fields. Need to decide how to display this data in the frontend.

### Problem

We've added three new nutritional fields to meals:
- `sugar_g` - Sugar content (subset of carbohydrates)
- `saturated_fat_g` - Saturated fat content (subset of total fat)
- `fiber_g` - Dietary fiber content

The frontend currently displays only the "big four" macros: calories, protein, carbs, and fat. We need to decide how and where to surface the extended nutritional data.

### Options Under Consideration

**Option A: Expandable Macro Details**
- Keep current compact view (P/C/F)
- Add expandable section showing sugar, sat fat, fiber
- Pros: Clean default view, details available on demand
- Cons: Extra tap to see data, might go unused

**Option B: Always Show All Nutrients**
- Display all 7 values (kcal, protein, carbs, sugar, fat, sat fat, fiber)
- Pros: Transparent, no hidden data
- Cons: Cluttered UI, overwhelming for quick glance

**Option C: Configurable Display**
- User preference in settings: "Show extended nutrients"
- Toggle between compact (4 values) and detailed (7 values)
- Pros: User choice, respects different needs
- Cons: More settings complexity

**Option D: Context-Dependent Display**
- Compact in Today View (quick glance)
- Full details in Meal Library and meal detail views
- Pros: Right level of detail per context
- Cons: Inconsistent display across views

### Questions to Resolve

1. Do users care about sugar/sat fat/fiber for daily use?
2. Should this data affect meal selection or filtering?
3. Is there a standard format users expect (nutrition label style)?
4. Should we show ratios (e.g., sugar as % of carbs)?

### Next Steps

- Gather user feedback on which nutrients matter most
- Prototype Option D (context-dependent) and evaluate
- Consider future: daily totals, weekly averages, targets

---

## ADR-011: Per-Slot Meal Reassignment

**Date**: 2026-02-20
**Status**: Proposed (Needs Discussion)
**Context**: Users need the ability to swap individual meals within their generated weekly plan without switching the entire day template. This relaxes ADR-003 (No Per-Meal Editing).

### Problem

The current system only allows changing meals by switching the entire day template, which regenerates all slots for that day and loses completion statuses. This is too coarse-grained for common scenarios:
- "I don't have ingredients for this specific meal"
- "I want a lighter option for this one slot"
- "I already ate something else for breakfast, assign me a different lunch"

Users need per-slot control while preserving the "no decisions by default" philosophy — the round-robin still assigns meals automatically, but users can override individual slots when needed.

### Decision

Allow per-slot meal reassignment in both Week View and Today View:

1. **Default flow**: Tap a slot → open MealPicker → select a different meal from the same meal type's pool
2. **Advanced flow**: Option to change the slot's meal type first, then pick from the new type's pool
3. **Round-robin independence**: Manual reassignment does NOT advance the round-robin pointer. The override is separate from automatic rotation — it won't affect future week generation
4. **Data tracking**: Add `is_manual_override` boolean to `weekly_plan_slot` to distinguish auto-assigned from user-picked meals. This allows future analytics (how often do users override?) and clear UX indicators

### API Changes

New endpoint:
- `PUT /slots/{slot_id}/reassign` — accepts `meal_id` (required) and `meal_type_id` (optional, for type change)
- Returns updated `WeeklyPlanSlotWithNext` response
- Validates: meal exists, meal belongs to the target meal type, slot exists and is not from a past day

### UX Flow

**Week View**: Tap day card → tap specific meal slot → MealPicker bottom sheet opens (filtered by slot's meal type). Toggle at top to "Change meal type" which shows meal type selector first, then meals for selected type.

**Today View**: Tap meal card → options include "Change meal" alongside completion statuses. Opens same MealPicker flow.

### Rationale

- **Preserves "no decisions" default** — Round-robin still assigns meals. Override is opt-in, not required
- **Granular control** — Users fix one slot without losing completion data on other slots
- **Meal type flexibility** — Schedule changes (e.g., skipping snack, wanting a heavier lunch) are accommodated
- **Trackable** — `is_manual_override` enables future analytics on override frequency

### Alternatives Considered

- **Keep ADR-003 strict (template switching only)** — Too coarse; users report frustration when a single meal doesn't work but the rest of the day is fine
- **Allow free-form meal entry per slot** — Too much freedom; reintroduces decision fatigue. Constraining to library meals maintains the "pick from curated options" philosophy
- **Regenerate just the one slot via round-robin** — Doesn't give user control; they might get an equally unsuitable meal

### Consequences

- **Relaxes ADR-003** — Per-meal editing is now allowed, but constrained to library selection (not free-form)
- **Migration required** — Add `is_manual_override` column to `weekly_plan_slot`
- **MealPicker reuse** — The existing MealPicker component (used for ad-hoc meals) can be adapted for reassignment
- **Stats consideration** — Override meals still count for adherence tracking; the `is_manual_override` flag is metadata only
- **Completion preservation** — Reassigning a slot that was already marked complete should clear the completion status (new meal = fresh tracking)

### References

- Supersedes ADR-003 for per-slot changes (ADR-003 "no in-meal editing" remains the default behavior; this adds an escape hatch)
- MealPicker component: `frontend/src/components/mealframe/meal-picker.tsx`

---

## ADR-012: Revised Completion Statuses

**Date**: 2026-02-20
**Status**: Proposed (Needs Discussion)
**Context**: The current 5 completion statuses need revision to better capture real-world meal deviation patterns and integrate with upcoming AI meal capture capabilities.

### Problem

Current statuses (`followed`, `adjusted`, `skipped`, `replaced`, `social`) are vague in practice:
- **adjusted** vs **replaced** distinction is unclear — "I ate rice instead of pasta" could be either
- No mechanism to record *what* was actually eaten when deviating
- **social** semantics are ambiguous — is it adherence-neutral or negative?
- No integration point for AI-derived meal capture

### Decision

Replace the completion status enum with 5 revised statuses:

| Status | Label | Adherence | Behavior |
|--------|-------|-----------|----------|
| `followed` | Followed | Positive | Ate the planned meal as-is. No additional data captured |
| `skipped` | Skipped | Negative | Did not eat this meal at all |
| `equivalent` | Changed for equivalent | Neutral | Ate something comparable. User selects replacement from meal library or quick-adds a new meal (see below). Replacement meal is linked to the slot for macro tracking |
| `deviated` | Changed for worse | Negative | Ate something off-plan. Triggers AI capture flow (ADR-013) — photo or voice input to estimate macros. Captured meal linked to slot |
| `social` | Social event | Non-adherent (own category) | Social occasion prevented following. No meal details captured — user explicitly doesn't want to track. Counts against adherence in stats but displayed as its own category, separate from skipped/deviated |

### Data Model Changes

1. **Rename enum values**: `adjusted` → `equivalent`, `replaced` → `deviated`
2. **Add `actual_meal_id`** (nullable FK) to `weekly_plan_slot` — references the meal the user actually ate (for `equivalent` and `deviated` statuses). NULL for `followed`, `skipped`, `social`
3. **Migration**: Rename existing `adjusted` rows to `equivalent`, `replaced` to `deviated` in the database. Update CHECK constraint
4. **Quick-add flow**: When marking `equivalent`, user can either:
   - Pick an existing meal from the library (sets `actual_meal_id`)
   - Quick-add a new meal (minimal form: name, portion, meal type, optional macros) — creates a `meal` record, then sets `actual_meal_id`

### Stats Impact

| Status | Adherence calculation |
|--------|----------------------|
| `followed` | Counts as adherent |
| `skipped` | Counts as non-adherent |
| `equivalent` | Counts as neutral (excluded from adherence %) — user made a reasonable swap |
| `deviated` | Counts as non-adherent |
| `social` | Counts as non-adherent, but displayed in its own "Social" category in stats breakdown. Visually separated from skipped/deviated to acknowledge it's contextual, not a failure |

### Rationale

- **Clearer semantics** — Each status has an unambiguous definition and distinct behavior
- **Data capture integration** — `equivalent` and `deviated` both capture what was actually eaten, enabling accurate daily macro totals even when deviating
- **AI integration point** — `deviated` directly triggers the AI capture pipeline (ADR-013)
- **Social acknowledgment** — Social events are tracked for pattern awareness but treated as a distinct category, reducing guilt while maintaining data integrity

### Alternatives Considered

- **Keep current 5 statuses** — Ambiguous in practice, no mechanism to record actual meals eaten
- **Add more granular statuses** (6+) — Over-classification; users won't distinguish between subtle categories
- **Remove social entirely** — Loses useful pattern data (e.g., "I deviate every Friday due to team dinners")
- **Make equivalent negative** — Discourages honest reporting; a reasonable swap shouldn't penalize adherence

### Consequences

- **Breaking change** — Enum values change, requiring DB migration and frontend updates
- **`actual_meal_id` column** — New nullable FK on `weekly_plan_slot`, with migration
- **CompletionSheet UI** — Needs redesign: `equivalent` opens MealPicker, `deviated` opens AI capture
- **Quick-add meal form** — New UI component for inline meal creation during completion flow
- **Stats service** — Adherence calculation logic needs updating for the neutral `equivalent` status
- **Offline** — `followed`, `skipped`, `social` work offline. `equivalent` (library pick) works offline. `deviated` (AI capture) requires network (per ADR-013)

### References

- Current statuses: `backend/app/schemas/common.py` (`CompletionStatus` enum)
- CHECK constraint: `backend/app/models/weekly_plan.py` (`ck_weekly_plan_slot_status`)
- CompletionSheet: `frontend/src/components/mealframe/completion-sheet-animated.tsx`
- AI capture integration: ADR-013
- Quick-add ties into ADR-011 (MealPicker component reuse)

---

## ADR-013: AI-Powered Ad Hoc Meal Capture

**Date**: 2026-02-20
**Status**: Proposed (Needs Discussion)
**Context**: Users need a low-friction way to log off-plan meals using photo or voice input, with approximate macro estimation. Based on PRD: `docs/frozen/features/Mealframe_AdHoc_Meal_PRD.md`.

### Problem

When users deviate from their meal plan, logging what they actually ate is high-friction:
- Manual macro entry is tedious and error-prone
- Users skip logging entirely, making daily totals inaccurate
- No mechanism to capture real-world meals without pre-existing database entries

This creates under-tracking and reduces the reliability of daily macro evaluation.

### Decision

Implement AI-powered meal capture with two entry points and two input methods:

**Entry Points:**
1. **Standalone**: "Add Meal" button → "Add Ad Hoc Meal" → AI capture flow (image or voice)
2. **Completion flow**: Mark slot as "Changed for worse" (`deviated` status per ADR-012) → AI capture flow

**Input Methods (phased):**
- **Phase 1 (MVP)**: Image capture — user takes photo, AI estimates macros
- **Phase 2**: Voice dictation — user describes what they ate, AI parses and estimates

**Processing Model:**
1. User submits image (or voice in Phase 2)
2. Meal record created immediately with `processing_status = "processing"`
3. AI pipeline runs asynchronously in background
4. Meal record updated with estimated macros when complete
5. User does NOT wait — app can be closed

**AI Output Contract:**
```json
{
  "meal_name": "Grilled chicken with rice and salad",
  "portion_description": "200g grilled chicken breast + 250g white rice + 100g mixed salad",
  "macros": {
    "calories_kcal": 720,
    "protein_g": 55,
    "carbs_g": 70,
    "fat_g": 22
  },
  "confidence_score": 0.78,
  "identified_items": [
    {"name": "grilled chicken breast", "estimated_quantity": "200g"},
    {"name": "white rice", "estimated_quantity": "250g"},
    {"name": "mixed salad", "estimated_quantity": "100g"}
  ]
}
```

### Data Model Changes

New fields on `meal` table (or new `ad_hoc_meal` table — see Options):
- `source`: enum — `"manual"`, `"ad_hoc_image"`, `"ad_hoc_voice"` (default `"manual"` for existing meals)
- `confidence_score`: nullable Numeric — AI confidence (0.0–1.0)
- `processing_status`: nullable enum — `"processing"`, `"completed"`, `"failed"`
- `raw_input_reference`: nullable Text — S3/local path to image or raw transcription text
- `ai_model_version`: nullable Text — model identifier for traceability

New table `openai_usage` (per Auth PRD):
- `id`, `user_id`, `model`, `tokens_prompt`, `tokens_completion`, `cost_estimate`, `timestamp`

### API Changes

- `POST /meals/ai-capture` — accepts multipart image upload (or text for voice). Returns meal ID immediately with `processing_status: "processing"`
- `GET /meals/{id}` — existing endpoint; client polls or uses websocket for status updates
- Processing webhook/polling: client checks `processing_status` field until `"completed"` or `"failed"`

### Provider Selection

**To be decided during implementation.** Options evaluated:

| Provider | Vision | Voice | Pros | Cons |
|----------|--------|-------|------|------|
| **OpenAI (GPT-4o)** | Excellent | Whisper built-in | Best vision accuracy, single provider for both | Cost per call, vendor lock-in |
| **Anthropic (Claude)** | Good | No native STT | Strong reasoning, already used in dev workflow | Need separate STT provider for voice |
| **Open-source (LLaVA + Whisper)** | Moderate | Good | No API cost, self-hosted | Accuracy concerns, infrastructure overhead |

Recommendation: **OpenAI GPT-4o for MVP** — best vision accuracy for food identification, Whisper for Phase 2 voice. Revisit if costs become significant.

### Offline Handling

Per PRD: **No offline support in MVP.**
- If offline, show blocking message: "Internet connection required to process ad hoc meals"
- Upload button disabled until connectivity restored
- No local caching or deferred upload queue
- Future (Phase 3+): local image storage + deferred upload when online

### Accuracy Philosophy

- Target: ±10–20% macro accuracy (daily-level awareness, not clinical precision)
- AI returns best estimate with confidence score
- No manual correction loop in MVP (Phase 3 improvement)
- Lower confidence → still stored, never fails silently

### Rationale

- **Low friction** — Under 5 seconds of user interaction (take photo → done)
- **Background processing** — User doesn't wait, meal appears when ready
- **Two entry points** — Captures both "adding extra food" and "replacing planned meal" scenarios
- **Structured output** — AI returns data matching existing meal schema, enabling macro tracking
- **Future-proof** — `source` and `ai_model_version` fields enable reprocessing and model improvement

### Alternatives Considered

- **Manual macro entry only** — Too much friction; users won't bother
- **Barcode scanning** — Only works for packaged food; most deviations are restaurant/homemade
- **Pre-built food databases (USDA)** — Requires users to search and estimate portions; still high friction
- **Client-side ML (on-device)** — Insufficient accuracy for food recognition without cloud models

### Consequences

- **External API dependency** — Requires OpenAI API key and costs per use
- **Image storage** — Need file storage strategy (S3, local volume, or database BLOB)
- **Async processing** — Need background task infrastructure (could use FastAPI BackgroundTasks for MVP, proper queue like Celery later)
- **Cost monitoring** — Per-user usage tracking required (aligns with Auth PRD's `openai_usage` table)
- **Privacy** — Food photos stored server-side; need clear data retention policy
- **Meal library growth** — AI-captured meals become real `meal` records, growing the library. May need "AI-generated" filter/tag

### References

- PRD: `docs/frozen/features/Mealframe_AdHoc_Meal_PRD.md`
- Completion flow integration: ADR-012 (`deviated` status triggers this)
- Existing ad-hoc meal system: `POST /today/slots` + `is_adhoc` flag
- Auth/metering: ADR-014 (OpenAI usage tracking)

---

## ADR-014: Authentication & Multi-User Architecture

**Date**: 2026-02-20
**Status**: Accepted
**Context**: To expose MealFrame to users beyond the single-user MVP, we need authentication, session management, and per-user data isolation. Based on PRD: `docs/frozen/features/Mealframe_Auth_MultiUser_PRD.md`. Supersedes ADR-009.

### Problem

The MVP was designed for single-user use (ADR-005). While all tables include nullable `user_id` columns, there is:
- No authentication or session management
- No data isolation between users
- No secure deployment model (relies on private network)
- No foundation for OpenAI usage metering (needed for ADR-013)

### Decision

**Self-managed authentication** (Option C) with email/password + Google OAuth.

Aligns with the self-hosted Proxmox deployment philosophy — no external auth dependencies, all data stays on own infrastructure, zero recurring vendor cost.

### Auth Methods

**Day one:**
1. **Email/password** — Argon2id hashing, email verification required before access
2. **Google OAuth** — via `authlib` OIDC flow, creates local user record on first login

**Deferred:**
- Magic link / passwordless (evaluate if password reset friction is too high)
- Additional OAuth providers (Apple, GitHub)

### Technical Architecture

**Backend stack:**
- `fastapi-users` library OR custom implementation (evaluate during implementation)
- **Argon2id** password hashing (memory-hard, recommended over bcrypt)
- **JWT access tokens** — short-lived (15 min), stateless, sent in Authorization header
- **Refresh tokens** — long-lived (7 days), stored in HTTP-only secure cookie, rotated on use
- **Google OAuth** — `authlib` for OIDC flow, verified email used as account identifier
- **Email service** — Resend (free tier: 100 emails/day, sufficient for <50 users) for verification and password reset

**Frontend stack:**
- Auth context provider wrapping the app
- Login / Register / Forgot Password pages
- Protected route middleware (redirect to login if no valid token)
- Token refresh handled transparently via interceptor

**Session security:**
- HTTPS only (already have SSL via Nginx Proxy Manager)
- HTTP-only + Secure + SameSite=Lax cookies for refresh tokens
- CSRF protection via SameSite cookie attribute + Origin header validation
- Access token expiry: 15 min
- Refresh token expiry: 7 days, single-use with rotation
- Rate limiting on auth endpoints (login: 5 attempts/min, register: 3/min)
- Account lockout after 10 failed attempts (15 min cooldown)

### Auth Flows

**Registration:**
1. User submits email + password (min 8 chars)
2. Password hashed with Argon2id, user record created with `email_verified=false`
3. Verification email sent via Resend with time-limited token (24h)
4. User clicks link → `email_verified=true` → can now login
5. If unverified user tries to login → "Please verify your email" message

**Login (email/password):**
1. Validate credentials against Argon2id hash
2. Issue JWT access token (15 min) + refresh token (7 days, HTTP-only cookie)
3. Return access token in response body, set refresh cookie

**Login (Google OAuth):**
1. Frontend redirects to Google consent screen
2. Google returns authorization code to callback URL
3. Backend exchanges code for tokens, validates OIDC ID token
4. If email exists → login. If new email → create user with `email_verified=true` (Google verifies)
5. Issue JWT + refresh token as above

**Password Reset:**
1. User requests reset → time-limited token (1h) emailed
2. User clicks link → enters new password
3. Password updated, all existing refresh tokens invalidated

**Token Refresh:**
1. Frontend detects 401 → sends refresh token cookie to `/auth/refresh`
2. Backend validates refresh token, issues new access + refresh token pair
3. Old refresh token invalidated (rotation)

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/register` | POST | Create account (email + password) |
| `/auth/login` | POST | Login (email + password) |
| `/auth/logout` | POST | Invalidate refresh token |
| `/auth/refresh` | POST | Rotate tokens |
| `/auth/verify-email` | POST | Verify email with token |
| `/auth/forgot-password` | POST | Request password reset |
| `/auth/reset-password` | POST | Reset password with token |
| `/auth/google/authorize` | GET | Redirect to Google OAuth |
| `/auth/google/callback` | GET | Handle Google OAuth callback |
| `/auth/me` | GET | Get current user profile |

### Data Model

**New table: `users`**
- `id` (UUID, PK)
- `email` (Text, unique, indexed)
- `password_hash` (Text, nullable — NULL for Google OAuth-only users)
- `email_verified` (Boolean, default false)
- `is_active` (Boolean, default true)
- `auth_provider` (Text, default "email" — "email" or "google")
- `google_sub` (Text, nullable, unique — Google subject ID for OAuth users)
- `created_at` (DateTime, timezone-aware)
- `updated_at` (DateTime, timezone-aware)

**New table: `refresh_tokens`**
- `id` (UUID, PK)
- `user_id` (FK → users.id, indexed)
- `token_hash` (Text, unique — hashed refresh token for lookup)
- `expires_at` (DateTime)
- `created_at` (DateTime)
- `is_revoked` (Boolean, default false)

**New table: `openai_usage`**
- `id` (UUID, PK)
- `user_id` (FK → users.id, indexed)
- `model` (Text)
- `tokens_prompt` (Integer)
- `tokens_completion` (Integer)
- `cost_estimate` (Numeric)
- `created_at` (DateTime)

**Existing tables:** Populate nullable `user_id` FK columns (already present in schema)

### New User Onboarding

New users start with an **empty account** — no sample meals, no templates. This keeps data clean and avoids confusion about what's "theirs" vs. pre-loaded. Users create their own meal library and templates from scratch (or via CSV import).

### Migration Strategy

1. Create `users`, `refresh_tokens`, `openai_usage` tables
2. Create admin user record for existing data (your account)
3. Backfill `user_id` on all existing rows (meals, templates, plans, etc.)
4. Make `user_id` NOT NULL on all tables (with FK constraint to `users`)
5. Add `get_current_user` dependency to all API routes
6. Add `user_id` parameter to all service methods
7. Hard cutover (no feature flag — user base is ~1)

### Alternatives Considered

- **Clerk (Option A)** — Fastest to ship, but adds cloud dependency to self-hosted stack. Overkill for <50 users, creates vendor lock-in
- **Auth0 (Option B)** — Enterprise-grade but complex dashboard, Universal Login redirect UX feels less native. External dependency
- **Supabase Auth (Option D)** — Interesting middle ground, but using their auth without their DB is an unusual pattern. Adds service dependency
- **No auth (keep single-user)** — Can't share the app with anyone. Blocks the entire multi-user roadmap

### Consequences

- **Every API endpoint changes** — All service methods gain a `user_id` parameter from `get_current_user` dependency
- **Frontend auth state** — Auth context provider, protected routes, login/register/forgot-password pages
- **Security responsibility** — Must handle password storage, token management, brute force protection correctly. Mitigated by using Argon2id (proven algorithm) and following OWASP guidelines
- **Email dependency** — Resend for transactional email. If Resend goes down, new registrations and password resets are blocked (login still works)
- **Seed data** — Existing data assigned to admin user. New users get empty accounts
- **Testing** — All tests need auth fixtures (authenticated test client with mock user)
- **~5-7 sessions of work** — Largest single feature. Can be broken into: (1) backend auth endpoints + middleware, (2) data migration, (3) frontend auth pages + context, (4) settings page, (5) testing

### Open Items (Resolve During Implementation)

- `fastapi-users` vs. custom auth implementation — evaluate library maturity and fit
- Resend vs. SendGrid — both have similar free tiers, pick based on developer experience
- CORS cookie configuration with Nginx Proxy Manager — test refresh token cookie flow end-to-end before committing to cookie-based approach
- Google OAuth client ID — needs Google Cloud Console project setup

### References

- PRD: `docs/frozen/features/Mealframe_Auth_MultiUser_PRD.md`
- Supersedes: ADR-009 (User Management for Multi-User Access)
- Related: ADR-005 (Single-User MVP with Multi-User Data Model)
- OpenAI metering: ADR-013 (AI-Powered Ad Hoc Meal Capture)

---

<!-- Append new ADRs above this line -->

## Template for New ADRs

```markdown
## ADR-XXX: [Decision Title]

**Date**: YYYY-MM-DD
**Status**: Proposed / Accepted / Deprecated / Superseded
**Context**: What problem are we solving?

### Decision

Clear statement of the decision.

### Rationale

Why this approach?

### Alternatives Considered

- Option A - Why not?
- Option B - Why not?

### Consequences

What does this enable? What does it constrain?
```
