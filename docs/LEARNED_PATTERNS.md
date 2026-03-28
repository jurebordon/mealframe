# Learned Patterns

> Patterns discovered during development sessions. AI assistants read this to avoid repeating mistakes and to reuse proven solutions.
> Tag entries with `[feature: name]` for filtering.

---

## Codebase Patterns

### Service layer always accepts user_id [feature: infrastructure]
- **Pattern**: All backend service functions accept `user_id: UUID` as first parameter. All DB queries filter by user_id.
- **Example**: `async def list_meals(db, user_id: UUID, ...) -> list[Meal]`
- **Discovered**: 2026-02-28

### API routes use dependency_overrides for test auth [feature: auth]
- **Pattern**: Tests inject test user via `app.dependency_overrides[get_current_user] = lambda: test_user`. Never generate real JWT tokens in tests.
- **Example**: In `conftest.py` client fixture: `app.dependency_overrides[get_current_user] = lambda: test_user`
- **Discovered**: 2026-02-28

### Frontend auth: access token in Zustand, never localStorage [feature: auth]
- **Pattern**: JWT access token stored in Zustand store (in-memory). Refresh token in HTTP-only cookie. `useAuthStore.getState().accessToken` for out-of-React-tree access (e.g., from `api.ts`).
- **Discovered**: 2026-03-01

### Number() wrapping for Pydantic Decimal fields [feature: infrastructure]
- **Pattern**: Pydantic `Decimal` fields serialize as strings in JSON (e.g., `"18.0"` not `18`). Always wrap with `Number()` before arithmetic in frontend.
- **Example**: `Number(slot.meal?.protein_g) || 0` in reduce/sum operations
- **Discovered**: 2026-02-08

### TanStack Query + page_size limit [feature: infrastructure]
- **Pattern**: Backend `/meals` endpoint has hard `page_size` max of 100. Exceeding causes silent 422 → TanStack Query error state → `data` is `undefined` → empty list.
- **Rule**: Always use `pageSize: 100` or less in frontend hooks
- **Discovered**: 2026-02-24

---

## Anti-Patterns

### Don't use datetime.utcnow() [feature: auth]
- **Problem**: `datetime.utcnow()` returns naive datetime. Comparing with timezone-aware datetimes causes TypeError in lockout window calculations.
- **Instead**: `datetime.now(timezone.utc)` — always timezone-aware
- **Discovered**: 2026-03-01

### Don't trigger file input from useEffect/setTimeout on iOS Safari [feature: ai-capture]
- **Problem**: iOS Safari requires file input `.click()` to be called synchronously during a user gesture. `useEffect` + `setTimeout` disqualifies it as a gesture.
- **Instead**: Use `forwardRef` + `useImperativeHandle` to expose `triggerFilePicker()` method; parent calls it directly in `onClick` handler.
- **Discovered**: 2026-03-08

### Don't use volume overrides without !override in docker-compose.prod.yml [feature: infrastructure]
- **Problem**: Without `volumes: !override`, dev bind mounts from docker-compose.yml merge into prod, overwriting chmod'd `entrypoint.sh` → permission denied on container startup.
- **Instead**: Use `volumes: !override` in `docker-compose.prod.yml` for services that need clean volume definitions
- **Discovered**: 2026-03-08

### Don't rename enum values without dropping CHECK constraint first [feature: infrastructure]
- **Problem**: PostgreSQL CHECK constraints validate values. Running `UPDATE ... SET status = 'new_value'` before dropping the constraint fails.
- **Instead**: In Alembic migration: DROP constraint → UPDATE data → ADD new constraint
- **Discovered**: 2026-02-23

---

## Conventions

### Ownership violations return 404, not 403 [feature: auth]
- **Convention**: When a user tries to access another user's resource, return 404 to prevent leaking that the resource exists.
- **Applies to**: All API routes that look up resources by ID
- **Discovered**: 2026-02-28

### Alembic migration naming [feature: infrastructure]
- **Convention**: `YYYYMMDD_description.py` for custom migrations. Alembic-generated ones use the revision hash.
- **Discovered**: 2026-02-27

### Deterministic admin UUID for tests [feature: auth]
- **Convention**: Admin user UUID is `00000000-0000-4000-a000-000000000001` — reproducible across environments and referenced by both migration and tests.
- **Discovered**: 2026-02-27

### React 18 forwardRef requirement for shadcn components [feature: infrastructure]
- **Convention**: shadcn/ui Input and Textarea need explicit `React.forwardRef` in React 18 for react-hook-form's `ref` to propagate correctly. React 19 removed this requirement.
- **Applies to**: Any shadcn UI component used with react-hook-form
- **Discovered**: 2026-03-03

---

## Performance Notes

### Sheet height: use fixed h-[85dvh] not max-h [feature: infrastructure]
- **Context**: Bottom sheets that show search results shrink as results reduce (content-driven height with max-h).
- **Rule**: Use fixed `h-[85dvh]` for sheets so they don't resize as content changes
- **Discovered**: 2026-02-24

---

## Tool & Environment Notes

### slowapi rate limiting disabled in tests [feature: auth]
- **Pattern**: `limiter.enabled = False` in test client fixture setup, `limiter.enabled = True` in teardown. Otherwise rate limit tests interfere with each other.
- **Discovered**: 2026-03-01

### Geist font: use npm package not next/font/google [feature: landing]
- **Context**: Geist font is not available via `next/font/google` in Next.js 14 (only in Next.js 15+).
- **Workaround**: Install `geist` npm package; apply via `GeistSans.className` on layout div
- **Discovered**: 2026-02-25

---

## How to Add Entries

When you discover a pattern during a session:
1. Add it under the appropriate section above
2. Tag with `[feature: name]` matching the feature you're working on
3. Include a concrete example or code snippet
4. Note the discovery date
