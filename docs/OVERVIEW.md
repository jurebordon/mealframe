# System Overview

**Last Updated**: 2026-02-04

## Architecture

### High-Level Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Next.js PWA (Mobile-First)                  │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │   │
│  │  │ Today   │  │ Week    │  │ Meals   │  │ Setup   │    │   │
│  │  │ View    │  │ View    │  │ Library │  │ Screens │    │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │   │
│  │                      │                                   │   │
│  │              Service Worker (Offline Cache)              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS / REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         SERVER                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Backend                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │ API Routes  │  │ Services    │  │ Round-Robin │     │   │
│  │  │ (Pydantic)  │  │ (Business)  │  │ Algorithm   │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              │ SQLAlchemy / asyncpg             │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    PostgreSQL                            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 14+ (React) | PWA support, SSR, TypeScript |
| **Backend** | FastAPI (Python) | Async API, automatic OpenAPI docs |
| **Database** | PostgreSQL 15+ | JSONB flexibility, UUID support |
| **Deployment** | Docker Compose | Simple single-host deployment |
| **PWA** | next-pwa | Service worker, offline support |
| **State** | Zustand + TanStack Query | Client state + server cache |
| **Styling** | Tailwind CSS | Utility-first, mobile-first |

## Data Model

### Core Abstractions

```
┌─────────────────────────────────────────────────────────────────┐
│                        PLANNING LAYER                           │
│  (Configured once, reused weekly)                               │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌───────────┐             │
│  │ Meal     │───▶│ Day          │───▶│ Week      │             │
│  │ Type     │    │ Template     │    │ Plan      │             │
│  └──────────┘    └──────────────┘    └───────────┘             │
│       │                                                         │
│       │ assigned to                                             │
│       ▼                                                         │
│  ┌──────────┐                                                   │
│  │ Meal     │ (with portions + macros)                         │
│  └──────────┘                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ generates
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       EXECUTION LAYER                           │
│  (Generated weekly, consumed daily)                             │
│                                                                 │
│  ┌────────────────────┐    ┌─────────────────┐                 │
│  │ Weekly Plan        │───▶│ Daily Slots     │                 │
│  │ Instance           │    │ (with meals)    │                 │
│  └────────────────────┘    └─────────────────┘                 │
│                                   │                             │
│                                   │ tracked via                 │
│                                   ▼                             │
│                            ┌─────────────────┐                 │
│                            │ Completion      │                 │
│                            │ Status          │                 │
│                            └─────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Tables

| Table | Purpose |
|-------|---------|
| `meal_type` | Functional eating slots (e.g., "Pre-Workout Snack") |
| `meal` | Specific foods with exact portions and macros |
| `meal_to_meal_type` | Many-to-many: meals assigned to meal types |
| `day_template` | Reusable day patterns (e.g., "Morning Workout Workday") |
| `day_template_slot` | Ordered meal type slots within a template |
| `week_plan` | Mapping of day templates to weekdays |
| `week_plan_day` | Days within a week plan |
| `weekly_plan_instance` | Generated week (specific dates) |
| `weekly_plan_instance_day` | Day within generated week (supports template switching) |
| `weekly_plan_slot` | Individual meal slots with completion tracking |
| `round_robin_state` | Tracks rotation state per meal type |
| `app_config` | Single-row configuration |

## Core Algorithms

### Round-Robin Meal Selection

**Purpose**: Provide variety without requiring decisions.

**How it works**:
1. Meals for a Meal Type are ordered by `(created_at ASC, id ASC)` for determinism
2. System tracks the last-used meal ID for each Meal Type
3. On generation, next meal = `meals[(last_index + 1) % total_meals]`
4. State is updated after each assignment

**Properties**:
- Deterministic (same inputs → same outputs)
- Fair (every meal gets equal rotation)
- Extensible (new meals appended to rotation)
- Resilient (deleted meals don't break state)

### Week Generation

**Trigger**: Manual (user clicks "Generate Next Week")

**Process**:
1. Create `weekly_plan_instance` record
2. For each day (Mon-Sun):
   - Get day template from week plan
   - Create `weekly_plan_instance_day` record
   - For each slot in template:
     - Get next meal via round-robin
     - Create `weekly_plan_slot` record with meal assignment

**Result**: Complete week with concrete meal assignments

### Day Template Switching

**Use case**: Schedule change (e.g., workout cancelled)

**Process**:
1. Delete existing slots for that day
2. Update `weekly_plan_instance_day` with new template
3. Generate new slots with round-robin meals
4. Completion statuses are lost (intentional - new plan)

## API Design

### Primary Endpoints (Daily Use)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/today` | GET | Today's meal plan with completion status |
| `/yesterday` | GET | Yesterday's plan for review/catch-up |
| `/slots/{id}/complete` | POST | Mark slot complete with status |
| `/slots/{id}/complete` | DELETE | Undo completion |
| `/stats` | GET | Adherence statistics |

### Weekly Planning Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/weekly-plans/current` | GET | Current week's plan |
| `/weekly-plans/generate` | POST | Generate new week |
| `/weekly-plans/current/days/{date}/template` | PUT | Switch day's template |
| `/weekly-plans/current/days/{date}/override` | PUT | Mark day as "no plan" |

### Setup Endpoints

| Resource | Methods | Purpose |
|----------|---------|---------|
| `/meals` | GET, POST, PUT, DELETE | Meal library CRUD |
| `/meals/import` | POST | CSV meal import |
| `/meal-types` | GET, POST, PUT, DELETE | Meal type CRUD |
| `/day-templates` | GET, POST, PUT, DELETE | Day template CRUD |
| `/week-plans` | GET, POST, PUT, DELETE | Week plan CRUD |

## Frontend Architecture

### Screen Hierarchy

```
App
├── Today View (/)                    [PRIMARY - Mobile First]
│   ├── Header (date, streak, progress)
│   ├── Next Meal Card (prominent)
│   ├── Meal List (remaining slots)
│   └── Yesterday Review Modal (morning prompt for unmarked meals)
│
├── Week View (/week)                 [Secondary]
│   ├── Week Header (date range, generate button)
│   ├── Day Cards (7 days)
│   └── Template Picker Modal
│
├── Meals Library (/meals)            [Setup - Desktop]
│   ├── Search/Filter Bar
│   ├── Meal List
│   ├── Meal Editor Modal
│   └── CSV Import Modal
│
├── Setup (/setup)                    [Setup - Desktop]
│   ├── Meal Types Tab
│   ├── Day Templates Tab
│   └── Week Plan Tab
│
└── Stats (/stats)                    [Secondary]
    ├── Overall Adherence
    ├── Streak History
    └── By Meal Type Breakdown
```

### Offline Strategy

**Cached (Service Worker)**:
- App shell (HTML, CSS, JS)
- `/api/v1/today` response (refreshed on visit)
- Static assets

**Network-first**:
- `/api/v1/weekly-plans/*`
- All write operations

**Offline behavior**:
- Today View readable from cache
- Completion actions queued for sync when online
- Clear "offline" indicator in UI

## Deployment

### Production Architecture (Homelab)

```
Browser → meals.bordon.family
  ↓ (DNS: local=192.168.1.50, external=public IP)
  ↓
Nginx Proxy Manager (192.168.1.50) - SSL termination, reverse proxy
  ↓
  ├─→ Web: 192.168.1.100:3000 (Next.js standalone)
  └─→ API: 192.168.1.100:8003 (FastAPI/Gunicorn)
        ↓
      PostgreSQL (internal)
```

### Docker Compose Services

```yaml
services:
  db:           # PostgreSQL 15
  api:          # FastAPI backend (Gunicorn + Uvicorn workers)
  web:          # Next.js frontend (standalone output)
```

### Auto-Deployment

GitHub Actions triggers SSH-based deployment on push to main:
1. SSH into deployment VM
2. Pull latest code
3. Rebuild and restart containers
4. Migrations run automatically via entrypoint

### Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `DB_PASSWORD` | db, api | PostgreSQL password |
| `DATABASE_URL` | api | Full connection string |
| `CORS_ORIGINS` | api | Allowed origins |
| `NEXT_PUBLIC_API_URL` | web | API base URL |

## Design Principles

1. **Single-user MVP, multi-user ready** - No auth in MVP, but all tables include `user_id` as nullable FK
2. **Offline-first for consumption** - Today View must work without network
3. **API-first** - All business logic exposed via REST API; frontend is a consumer
4. **Deterministic generation** - Same inputs produce identical weekly plans
5. **Mobile-first consumption** - Desktop for setup, mobile for daily use

## File Structure

```
mealframe/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/                 # DB migrations
│   └── app/
│       ├── main.py              # FastAPI app
│       ├── config.py
│       ├── database.py
│       ├── models/              # SQLAlchemy models
│       ├── schemas/             # Pydantic schemas
│       ├── api/                 # Route handlers
│       └── services/            # Business logic
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   ├── public/
│   │   └── manifest.json
│   └── src/
│       ├── app/                 # Next.js App Router
│       ├── components/
│       ├── lib/
│       └── hooks/
└── docs/                        # SpecFlow documentation
```

## Key Invariants

- **Portion descriptions are mandatory** - Every meal must have exact portions
- **Round-robin is deterministic** - Same inputs always produce same meal assignments
- **No in-meal editing** - Users can only switch day templates, not individual meals
- **Completion tracking is optional** - Unmarked meals are valid, not errors
- **Single-user for MVP** - No auth, but data model is multi-user ready

---

*This overview provides the mental model for working on MealFrame. See ADR.md for specific technical decisions.*
