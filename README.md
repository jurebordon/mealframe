# MealFrame

> Meal planning that eliminates decision fatigue with authoritative, pre-planned meals.

MealFrame provides exact portions and clear instructions on what to eat, removing in-the-moment decisions that lead to overconsumption. It's designed for mobile-first consumption with desktop tools for setup and planning.

## Features (Planned)

- **Mobile-First Today View**: See your daily meal plan at a glance, optimized for quick consumption
- **Round-Robin Meal Selection**: Automated variety without requiring decisions
- **Day Template System**: Reusable patterns for different types of days (workout days, rest days, etc.)
- **PWA Support**: Offline access to your daily plan
- **Completion Tracking**: Optional tracking with flexible statuses (completed, skipped, partial)
- **Weekly Planning**: Generate complete weeks based on your templates and meal library

## Tech Stack

- **Backend**: FastAPI (Python) with async PostgreSQL
- **Frontend**: Next.js 14+ (React/TypeScript) with PWA support
- **Database**: PostgreSQL 15+
- **Deployment**: Docker Compose

## Project Structure

```
mealframe/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # Route handlers
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── alembic/         # Database migrations
│   └── Dockerfile
├── frontend/            # Next.js application
│   ├── src/
│   │   ├── app/        # Next.js App Router
│   │   ├── components/ # React components
│   │   ├── lib/        # Utilities
│   │   └── hooks/      # Custom hooks
│   └── Dockerfile
├── docs/               # SpecFlow documentation
└── docker-compose.yml  # Local development setup
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/jurebordon/meal-frame.git
   cd meal-frame
   ```

2. Copy environment template (when available):
   ```bash
   cp .env.example .env
   ```

3. Start services:
   ```bash
   docker-compose up
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Documentation

- [ROADMAP.md](docs/ROADMAP.md) - Current priorities and task list
- [OVERVIEW.md](docs/OVERVIEW.md) - System architecture and design
- [ADR.md](docs/ADR.md) - Architecture decision records
- [VISION.md](docs/VISION.md) - Product direction and philosophy
- [CLAUDE.md](CLAUDE.md) - AI assistant context

### Frozen Specs (Reference)

- [PRD_v0.md](docs/frozen/PRD_v0.md) - Original product requirements
- [TECH_SPEC_v0.md](docs/frozen/TECH_SPEC_v0.md) - Original technical specification

## Development Workflow

This project uses [SpecFlow](https://github.com/jurebordon/specflow) for structured AI-assisted development:

- `/plan-session` - Review roadmap and plan work
- `/start-session` - Begin implementation
- `/end-session` - Wrap up and commit
- `/pivot-session` - Reassess direction

See [CLAUDE.md](CLAUDE.md) for full development guidelines.

## Current Status

**Phase**: MVP - Foundation
**Status**: Initial setup and scaffolding

See [ROADMAP.md](docs/ROADMAP.md) for detailed progress and next steps.

## License

Private project - All rights reserved

## Contact

Jure Bordon - [@jurebordon](https://github.com/jurebordon)
