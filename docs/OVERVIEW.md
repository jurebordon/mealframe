# System Overview

**Last Updated**: 2026-03-17

## 1. What This Product Does

MealFrame is a mobile-first meal planning PWA that eliminates decision fatigue by automating weekly meal assignments. Users define meal types, day templates, and a weekly plan once — then the app generates weekly meal schedules via round-robin rotation and tracks daily completion.

## 2. Core User Journeys

- **UJ1 (Daily)**: Open Today View → see next meal with exact portions → mark meals complete as the day progresses
- **UJ2 (Weekly)**: Every Sunday, generate next week → review assigned meals → optionally switch day templates if schedule changes
- **UJ3 (Setup)**: Create meal library (CSV import or manual) → define meal types → build day templates → configure weekly plan
- **UJ4 (Deviation)**: Mark meal as "deviated" → capture photo via AI capture → AI estimates macros → meal logged in library

## 3. Architecture at 10,000 ft

### Backend

- **Stack**: FastAPI (Python), SQLAlchemy async, Alembic migrations, PostgreSQL 15+
- **Structure**:
  ```
  backend/
  ├── app/
  │   ├── main.py              # FastAPI app entry point
  │   ├── config.py            # Pydantic settings
  │   ├── database.py          # Async SQLAlchemy session
  │   ├── models/              # SQLAlchemy ORM models
  │   ├── schemas/             # Pydantic request/response schemas
  │   ├── api/                 # Route handlers (auth, meals, today, weekly, etc.)
  │   └── services/            # Business logic (round-robin, ai_capture, oauth)
  ├── alembic/                 # DB migrations
  ├── tests/                   # pytest test suite (async)
  └── Dockerfile
  ```
- **Main modules**: `api/auth.py`, `api/meals.py`, `api/today.py`, `api/weekly.py`, `api/setup.py`, `services/ai_capture.py`

### Frontend

- **Stack**: Next.js 14+ (App Router), React, TypeScript, Tailwind CSS, Zustand + TanStack Query, next-pwa
- **Structure**:
  ```
  frontend/src/
  ├── app/
  │   ├── (app)/               # Authenticated app pages (today, week, meals, setup, stats)
  │   ├── (auth)/              # Login/register/verify pages
  │   ├── (landing)/           # Waitlist landing page
  │   └── oauth/               # Google OAuth callback
  ├── components/
  │   ├── mealframe/           # Domain components (MealCard, CompletionSheet, AiCaptureSheet, etc.)
  │   ├── auth/                # Auth form components
  │   ├── navigation/          # AppShell, BottomNav, Sidebar
  │   └── ui/                  # Radix UI primitives (Button, Card, Sheet, etc.)
  ├── lib/                     # API client, types, auth-store (Zustand), query hooks
  └── hooks/                   # Custom React hooks
  ```

### Data

- **Primary database**: PostgreSQL 15+
- **Key entities**:
  - `users` — email/password + Google OAuth users with JWT/refresh token auth
  - `meal` — foods with exact portions and macros (calories, protein, carbs, fat, sugar, sat_fat, fiber); supports `source` (manual/ai_capture), `processing_status`, `confidence_score`
  - `meal_type` — functional eating slots (e.g., "Pre-Workout Snack")
  - `day_template` / `day_template_slot` — reusable day patterns
  - `week_plan` / `week_plan_day` — mapping of templates to weekdays
  - `weekly_plan_instance` / `weekly_plan_slot` — generated week with completion tracking and `is_manual_override` flag
  - `round_robin_state` — tracks last-used meal per meal type
  - `refresh_tokens` — HTTP-only cookie-based session management
  - `openai_usage` — per-user AI API cost tracking

### Integrations

- **OpenAI GPT-4o** — AI meal capture: food photo → macro estimation
- **Resend** — transactional email (verification, password reset)
- **Google OAuth** — social login via `authlib` OIDC flow
- **GitHub Actions** — SSH-based auto-deployment to Proxmox homelab VM

## 4. External Contracts

### API

- REST API at `/api/v1/` with automatic OpenAPI docs at `/docs`
- Primary endpoints: `/today`, `/weekly-plans/*`, `/meals/*`, `/auth/*`, `/slots/*`
- Auth: JWT access token (15 min) in `Authorization` header; refresh token in HTTP-only cookie

### Events

- Not applicable (no event bus)

### Data

- Alembic migrations in `backend/alembic/versions/`
- Key invariant: all data rows have `user_id` NOT NULL FK to `users`

## 5. Invariants

- **Portion descriptions are mandatory** — Every meal must have exact portions (e.g., "2 eggs + 1 slice toast")
- **Round-robin is deterministic** — Same inputs always produce same meal assignments; meals ordered by `(created_at ASC, id ASC)`
- **Completion tracking is optional** — Unmarked meals are valid, excluded from adherence stats, not errors
- **All API endpoints require authentication** — `get_current_user` dependency on all routes; `user_id` scopes all queries
- **Mobile-first Today View** — Must load from offline cache; completion status actions work without network
