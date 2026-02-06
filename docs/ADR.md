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
**Status**: Proposed (Needs Discussion)
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
