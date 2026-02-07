# Vision

**Last Updated**: 2026-02-04

## Current Phase Status

**Phase 1 (MVP): COMPLETE** - Deployed 2026-02-02

The MVP is fully functional and deployed at `meals.bordon.family`. All core features are working:
- Today View with completion tracking and streaks
- Week View with template switching and regeneration
- Meals Library with CSV import
- Setup screens for Meal Types, Day Templates, Week Plans
- Stats view with adherence tracking
- Offline support with sync queue
- Yesterday Review modal for catch-up
- Auto-deployment via GitHub Actions

**Next Phase**: Evaluating Phase 2 features (user management, grocery lists, template sharing)

---

## Problem Statement

Decision fatigue and stress-induced overeating, particularly during high-stress evening periods, undermine nutrition goals. The core issue isn't *what* to eat, but *how much* and the in-the-moment decisions that lead to overconsumption.

Target users know nutrition well but struggle with:
- Stress-driven overeating in evenings
- Eating correct foods but in excessive quantities
- Decision paralysis when willpower is depleted
- High-friction planning workflows (Google Sheets)

## Product Intent

### Phase 1: MVP (Personal Tool)

Replace high-friction Google Sheets workflow with a mobile-first experience that eliminates decision-making at meal time.

**Core Philosophy**: Psychological offloading
- Plan meals when calm and cognitive resources are abundant
- Follow predefined instructions during high-stress periods
- Remove in-the-moment decisions that lead to overconsumption

### Phase 2: Productized Version (Future)

- User accounts and authentication
- Template export/import for sharing
- Onboarding flow with default templates
- Public template library
- Grocery list generation
- Multi-user support

### Phase 3: Intelligence (Future)

- Adherence-weighted round-robin (deprioritize often-skipped meals)
- Contextual suggestions (weather, calendar integration)
- Macro balancing across day/week

## Value Proposition

| Current State (Google Sheets) | Target State (MealFrame) |
|-------------------------------|--------------------------|
| High friction to enter meals | Quick meal library with CSV import |
| Slow mobile loading, poor UX | Mobile-first PWA, instant access |
| Manual planning required daily | Auto-generated weekly plans |
| Vague plans ("2 eggs and bread") | Precise portions ("2 eggs + 1 slice toast") |
| No tracking or accountability | Completion tracking with streaks |
| Easy to ignore | Gamified dopamine loop on completion |

## Success Criteria

### Primary (User-Measured)

- Evening overeating incidents decrease 50%+
- Decision fatigue significantly reduced
- Plan adherence >80% "Followed" rate

### Secondary (App-Measured)

- Daily engagement: Open app 3+ times/day
- Completion rate: >70% of slots marked
- Week generation: 100% of weeks generated
- Streak length: Average >5 days

## Principles

### 1. Authoritative, Not Suggestive

The app tells you what to eat. It does not ask, suggest, or offer alternatives. Removing choice removes cognitive load.

### 2. Mobile-First for Consumption

- Primary interaction is quick glances on mobile
- Today View must load instantly
- Completion requires one tap
- Desktop is for setup and planning only

### 3. Forgiving, Not Judgmental

- Missed completions are "unknown," not failures
- "Social" status acknowledges life happens
- Override days are tracked, not penalized
- Streaks pause rather than break on overrides

### 4. Progressive Disclosure

- Today View shows minimal info (name, portion)
- Tap to expand for macros and notes
- Week View shows structure; tap for detail
- Stats available but not prominent

### 5. Satisfying Completion

- Marking meals complete should feel rewarding
- Visual and haptic feedback (animation, vibration)
- Progress visible ("3/5 meals")
- Streaks create positive anticipation

## Non-Goals

- Not a calorie tracker replacement (use alongside existing tracker)
- Not a recipe discovery app (user knows their meals)
- Not focused on social features or food logging accuracy
- Not a grocery list generator (deferred to Phase 2)
- Not enforcing macro targets (reflection only)

## Strategic Bets

1. **Exact portions are non-negotiable** - This is the key differentiator from other meal planning apps
2. **Round-robin is sufficient** - No need for complex optimization algorithms in MVP
3. **PWA over native** - Acceptable trade-off for MVP to move faster
4. **Template switching only** - No per-meal editing maintains the "no decisions" philosophy
5. **Single-user first** - Multi-user adds complexity without validating core value

## Evolution Path

```
MVP (Now)           Phase 2              Phase 3
├─ Personal tool    ├─ Multi-user        ├─ Smart rotation
├─ Manual CSV       ├─ Template sharing  ├─ Context-aware
├─ PWA only         ├─ Grocery lists     ├─ Macro balancing
├─ Basic tracking   ├─ Native apps       ├─ Calendar integration
└─ Solo workflow    └─ Onboarding flow   └─ Advanced analytics
```

## Measuring Success

We'll know we're on the right track when:
- Users consistently generate weekly plans every week
- Adherence rates stay above 70%
- Evening overeating self-reports decrease
- Users describe feeling "relieved" rather than "controlled"
- The app becomes invisible infrastructure (quick glances, no thought)

## What Could Go Wrong

| Risk | Mitigation |
|------|------------|
| Users reject authoritative approach | Allow template switching as escape valve |
| PWA performance insufficient on mobile | Be ready to build native apps in Phase 2 |
| Round-robin gets boring | Phase 3: adherence-weighted rotation |
| Too rigid for real life | "No Plan" override days, "Social" status |
| Manual weekly generation forgotten | Future: auto-generate on Sunday evening |

---

*This vision guides all product decisions. When in doubt, optimize for reducing decision fatigue.*
