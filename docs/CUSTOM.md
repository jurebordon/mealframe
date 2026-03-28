# Project-Specific Context

> Custom instructions and context that extend SpecFlow's defaults. All commands read this file.

---

## External References

- **Production app**: `meals.bordon.family` (homelab Proxmox VM, Nginx Proxy Manager, SSL via Let's Encrypt)
- **Waitlist landing**: `mealframe.io` and `www.mealframe.io` (same server)
- **Email service**: Resend (mealframe.io domain, DKIM/SPF/DMARC configured on Namecheap)
- **GitHub**: `mealframe.git` (GitHub redirect from `meal-frame.git` still works)
- **OpenAI**: GPT-4o used for AI meal capture vision API

---

## Custom Commands

```bash
# Deploy to production (SSH into VM, pull, rebuild)
# deploy/deploy.sh — split into build/down/up to avoid container rename conflicts

# Backend tests
cd backend && pytest

# Frontend checks
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run test:e2e  # Playwright e2e tests
```

---

## Project Conventions

- **Backend service pattern**: All service functions in `backend/app/services/` accept `user_id: UUID` as first param
- **Ownership violations return 404**: Not 403, to prevent resource existence leaking
- **Alembic migration naming**: `YYYYMMDD_description.py`
- **Seed data admin UUID**: `00000000-0000-4000-a000-000000000001` — deterministic, reproducible
- **Tests use `app.dependency_overrides`**: Override `get_current_user` to inject test user — no real JWT in tests
- **Rate limiting disabled in tests**: `limiter.enabled = False` in test client fixture, re-enabled in teardown
- **Round-robin excludes AI-captured meals**: Only `source = "manual"` meals enter rotation
- **Image storage**: Local volume `/data/captures` in Docker, resize to 1920px JPEG q=85

---

## Known Gotchas

- **Pydantic Decimal → JS string**: `Decimal` fields serialize as strings in JSON. Always wrap with `Number()` before arithmetic in frontend (protein_g, fat_g, carbs_g, etc.)
- **Backend page_size max is 100**: `/meals` endpoint has `le=100`. Requests >100 get silent 422 → TanStack Query error state → empty list. Always use `pageSize: 100` or less.
- **iOS Safari file input**: `fileInputRef.current?.click()` from `useEffect`/`setTimeout` doesn't qualify as user gesture. Use `forwardRef` + `useImperativeHandle` pattern — parent calls `triggerFilePicker()` synchronously in `onClick`.
- **React 18 forwardRef**: shadcn/ui components (Input, Textarea) need explicit `React.forwardRef` in React 18 for react-hook-form `ref` to work. React 19 doesn't need it.
- **Docker Compose prod volumes**: Use `!override` tag on volumes in `docker-compose.prod.yml` to prevent dev bind mount merging into prod (overwrites chmod'd entrypoint.sh → permission denied on startup)
- **Test DB isolation**: Tests share PostgreSQL with seed data. Fixtures creating rows with unique constraints (e.g., `is_default=True` on WeekPlan) must clear conflicting seed data inside the savepoint.
- **Timezone-aware datetimes**: Use `datetime.now(timezone.utc)` not `datetime.utcnow()` in models. Naive vs aware comparison causes mismatches in lockout window calculations.
- **Migration CHECK constraint order**: Must DROP CHECK constraint before UPDATEing enum data values in migration, then ADD new CHECK.

---

## AI Guidelines

- Read ROADMAP.md before planning — current wave and dependencies matter
- When touching auth code, check `backend/app/api/auth.py`, `backend/app/services/auth.py`, and `frontend/src/lib/auth-store.ts`
- ADR entries are append-only — never modify existing ones
- Feature docs (PRDs) live in `docs/feature_docs/<feature-name>/`
