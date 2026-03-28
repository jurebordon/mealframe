# Architecture Decision Record

> Append-only log of significant architecture and design decisions.
> Never modify existing entries - only append new ones.

## ADR-0001: Initial Architecture and Tech Stack

- **Date**: 2026-01-19
- **Status**: Accepted

### Context

Greenfield project needing backend, frontend, and database technology selection for a personal meal planning app.

### Decision

- **Backend**: FastAPI (Python) — async support, automatic OpenAPI docs, Pydantic validation, fast development velocity
- **Frontend**: Next.js 14+ (React, TypeScript) — PWA support via next-pwa, SSR, App Router, large ecosystem
- **Database**: PostgreSQL 15+ — JSONB flexibility, UUID support, robust constraints
- **Deployment**: Docker Compose — simple single-host deployment for MVP, easy local dev

### Consequences

- Two languages to maintain (Python + TypeScript)
- Docker Compose limits horizontal scaling (acceptable for MVP)
- PWA may have limitations vs native apps (monitored)

### Related

- `VISION.md`, `OVERVIEW.md`

---

## ADR-002: Round-Robin Algorithm for Meal Selection

- **Date**: 2026-01-19
- **Status**: Accepted

### Context

Need to assign meals to slots while providing variety without user decisions.

### Decision

Simple round-robin rotation per Meal Type: order meals by `(created_at ASC, id ASC)`, track last-used meal ID per type, select next as `(last_index + 1) % total_meals`.

### Consequences

- Deterministic and fair; new meals automatically enter rotation
- Deleted meals don't break state (graceful degradation)
- State management required (`round_robin_state` table)

---

## ADR-003: No Per-Meal Editing in Weekly Plans (Relaxed by ADR-011)

- **Date**: 2026-01-19
- **Status**: Superseded by ADR-011 for per-slot overrides

### Decision

Default: weekly plans are read-only at the meal level. Users switch day templates, not individual meals. ADR-011 adds per-slot override as an opt-in escape hatch.

---

## ADR-004: PWA Over Native Apps for MVP

- **Date**: 2026-01-19
- **Status**: Accepted

### Decision

Build as PWA using next-pwa, not native apps. Single codebase, faster development, no App Store friction.

---

## ADR-005: Single-User MVP with Multi-User Data Model

- **Date**: 2026-01-19
- **Status**: Superseded by ADR-014

### Decision

No auth in MVP, but all tables include nullable `user_id` FK for future multi-user. ADR-014 implements full auth.

---

## ADR-006: Manual Weekly Generation

- **Date**: 2026-01-19
- **Status**: Accepted

### Decision

Manual trigger (user clicks "Generate Next Week"). Explicit control, no cron jobs needed, review before committing.

---

## ADR-007: Completion Statuses Are Optional

- **Date**: 2026-01-19
- **Status**: Accepted

### Decision

Completion tracking is encouraged but not enforced. Unmarked meals are valid, not errors. Excluded from adherence calculations.

---

## ADR-008: Grocery List Ingredient Extraction Strategy

- **Date**: 2026-02-03
- **Status**: Proposed (pending ADR-013 LLM infrastructure)

### Decision

Use AI-powered extraction (Option C) to parse free-text portion descriptions into structured ingredients. Depends on LLM infrastructure from ADR-013. Deferred until after AI capture is complete.

---

## ADR-009: User Management (Superseded)

- **Date**: 2026-02-04
- **Status**: Superseded by ADR-014

---

## ADR-010: Extended Nutritional Data Display

- **Date**: 2026-02-06
- **Status**: Proposed

### Decision

Context-dependent display (Option D): compact in Today View (4-up: kcal/protein/carbs/fat), full details in Meal Library and detail views. `sugar_g`, `saturated_fat_g`, `fiber_g` fields are stored but shown contextually.

---

## ADR-011: Per-Slot Meal Reassignment

- **Date**: 2026-02-20
- **Status**: Accepted

### Decision

Allow per-slot meal reassignment in Week View and Today View. `PUT /slots/{slot_id}/reassign` endpoint. `is_manual_override` boolean added to `weekly_plan_slot`. Round-robin pointer not affected. Relaxes ADR-003 as opt-in escape hatch.

---

## ADR-012: Revised Completion Statuses

- **Date**: 2026-02-20
- **Status**: Accepted

### Decision

5 statuses: `followed` (adherent), `skipped` (non-adherent), `equivalent` (neutral — ate comparable, pick from library), `deviated` (non-adherent — triggers AI capture per ADR-013), `social` (non-adherent own category). `actual_meal_id` FK added to `weekly_plan_slot`.

---

## ADR-013: AI-Powered Ad Hoc Meal Capture

- **Date**: 2026-02-20
- **Status**: Accepted (Session 1 + 2 complete, Session 3 in progress)

### Decision

Image capture → OpenAI GPT-4o vision API → async macro estimation. Two entry points: standalone "Add Meal" and completion flow `deviated` status. New fields on `meal`: `source`, `confidence_score`, `processing_status`, `raw_input_reference`, `ai_model_version`. `POST /meals/ai-capture` endpoint. `openai_usage` table for cost metering.

---

## ADR-014: Authentication & Multi-User Architecture

- **Date**: 2026-02-20
- **Status**: Accepted (Sessions 1-5 complete, Session 6 — Google OAuth — pending)

### Decision

Self-managed auth: email/password (Argon2id) + Google OAuth (authlib). JWT access tokens (15 min) + HTTP-only refresh tokens (7 days, rotated). Email verification via Resend. Rate limiting on auth endpoints. All existing tables backfilled with `user_id` NOT NULL. Supersedes ADR-009.

### Related

- `backend/app/api/auth.py`, `backend/app/services/oauth.py`
- `frontend/src/app/(auth)/`, `frontend/src/components/auth/`, `frontend/src/lib/auth-store.ts`

---

<!-- New ADRs must be appended below this line. Do not modify existing entries. -->
