# Roadmap

**Last Updated**: 2026-03-22
**Current Phase**: Phase 2 — Feature Expansion & Multi-User

## Now (Current Work)

<!-- Tag each task with [feature: name] -->

| Feature | ADR | Branch | Status |
|---------|-----|--------|--------|
| AI meal capture — deviated meal display + history | ADR-013 | main | Next up (Session 3) |

**Remaining AI capture work [feature: ai-capture]:**
- [ ] Session 3: Frontend deviated meal display + history (captured meals in library, source badge) [feature: ai-capture]
- [ ] Session 4 (optional): User meal context injection into vision prompt [feature: ai-capture]

## Next (Queued)

<!-- Priority ordered - top item is next -->

1. [ ] Grocery list from weekly plan — Session 1: `needs_groceries` DB foundation + template editor toggle [feature: grocery-list]
3. [ ] Grocery list — Session 2: AI extraction service + grocery list API [feature: grocery-list]
4. [ ] Grocery list — Session 3: Frontend grocery list page + navigation [feature: grocery-list]

## Later (Backlog)

<!-- Ideas and future work, not prioritized -->

- AI meal capture Phase 2: voice dictation via Whisper (ADR-013 Phase 2) [feature: ai-capture]
- Push notification reminders (requires native app consideration) [feature: infrastructure]
- Adherence-weighted round-robin (deprioritize skipped meals) [feature: infrastructure]
- Watch complications for "next meal" [feature: infrastructure]
- Template export/import for sharing [feature: infrastructure]
- Public template library [feature: infrastructure]
- Per-slot reassignment UI polish (ADR-011) [feature: meal-reassignment]

## Done (Recent)

<!-- Recently completed, for context -->

- [x] ADR-014 Session 6: Google OAuth — authlib OIDC flow, auto-link accounts, conditional UI (2026-03-22) [feature: auth]
- [x] Mobile UI polish: 9 fixes from real-device iOS testing (2026-03-12) [feature: infrastructure]
- [x] ADR-013 Session 2: Frontend capture UI — AddMealSheet, AiCaptureSheet, iOS Safari gesture fix, client-side compression (2026-03-08) [feature: ai-capture]
- [x] ADR-013 Session 1: OpenAI GPT-4o vision, DB migration, ai-capture endpoint, image storage, round-robin exclusion (2026-03-05) [feature: ai-capture]
- [x] Resend email service setup — domain verification, DNS records, production config (2026-03-03) [feature: auth]
- [x] Auth session 5: email verification, password reset, rate limiting, account lockout (2026-03-01) [feature: auth]
- [x] Privacy policy page for waitlist landing (2026-02-25) [feature: landing]
- [x] Track C: Waitlist landing page + self-hosted pageview analytics (2026-02-25) [feature: landing]
- [x] Track A: Revised completion statuses — ADR-012 (backend + frontend + stats) (2026-02-23) [feature: completion-statuses]
- [x] Track B: Per-slot meal reassignment — ADR-011 (backend + frontend) (2026-02-23) [feature: meal-reassignment]
- [x] ADR-014 (Auth) sessions 1-4: users table, JWT/refresh tokens, frontend auth pages, settings, data migration (2026-02-23) [feature: auth]
- [x] Phase 1 MVP — fully deployed to meals.bordon.family (2026-02-02) [feature: infrastructure]

## Blockers

<!-- Anything preventing progress -->

- None

---

## Dependency Graph

```
Wave 1 ✅:
  Track A: ADR-012 (Completion Statuses) ── merged
  Track B: ADR-011 (Meal Reassignment) ──── merged
  Track C: Waitlist Page + Analytics ──────── merged

Wave 2 ✅:
  ADR-014 (Auth) — users table → middleware → data migration
                 → frontend auth → settings page

Wave 3 (in progress):
  ADR-013 (AI Capture) ◄── needs ADR-012 ✅, ADR-014 ✅
  Session 1 ✅ | Session 2 ✅ | Session 3 → next

Wave 4 (after AI capture):
  ADR-008 (Grocery List) ◄── needs ADR-013 ✅ LLM infra, ADR-014 ✅ auth
```

## Notes

- Tasks should be small enough to complete in 1-2 sessions
- Move items between sections as priorities change
- Add blockers immediately when encountered
- **Feature tagging**: Every task must be tagged with `[feature: name]`
  - Use `[feature: infrastructure]` for project-wide work
  - AI agents use feature tags to filter tasks when planning sessions
