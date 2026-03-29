# Feature: AI-Powered Onboarding

> Frozen north star for the AI onboarding feature.

---

## Requirements (Frozen)

### Overview
AI-powered onboarding wizard that eliminates the cold-start problem for new MealFrame users. Instead of self-navigating a complex setup chain (meal types, meals, day templates, week plan), users answer structured intake questions and an AI agent generates a personalized meal planning setup. A conversational meal import step lets users describe their favorite meals in natural language, with real nutrition data from USDA FoodData Central and Open Food Facts.

### User Stories
- As a new user, I want guided onboarding so that I can start meal planning without understanding the template system
- As a new user, I want AI to suggest a meal structure based on my schedule and goals so that I get a personalized setup without manual configuration
- As a new user, I want to describe my meals in natural language so that I don't have to manually enter portions and macros
- As an existing user, I want to reset and reconfigure my setup so that I can start fresh if my lifestyle changes

### Acceptance Criteria
- [ ] New users are automatically redirected to onboarding on first login (when no setup exists)
- [ ] 6-step intake questionnaire with selectable options + free-text "Other" on each step
- [ ] AI generates personalized meal types, day templates, and week plan from intake answers
- [ ] Summary review screen shows all generated entities with accept/edit capability
- [ ] Conversational meal import: user describes meals, AI parses + looks up real nutrition data
- [ ] Nutrition data sourced from USDA FoodData Central (whole foods) and Open Food Facts (branded items)
- [ ] Each AI-suggested meal shown as editable card for user confirmation before saving
- [ ] Photo capture available during meal import (reuses existing AI capture infrastructure)
- [ ] Apply step creates all entities and generates first weekly plan in a single transaction
- [ ] Onboarding state persisted server-side for resume capability (user can close and return)
- [ ] "Skip -- I'll set up manually" available on every step
- [ ] Existing users can access "Reset & reconfigure" from Settings page
- [ ] Mobile-first design (iOS Safari compatible)
- [ ] Standard SSE streaming for chat endpoint (native-client compatible)

### Out of Scope
- Voice dictation / Whisper integration (future: ADR-013 Phase 2)
- Native mobile app implementation (backend is API-ready; frontend is web-only for now)
- Full RAG with vector embeddings (lightweight context injection from user's DB data is in scope)
- Automatic nutritional goal calculation from body metrics (user provides targets manually)
- Onboarding analytics dashboard

---

## Implementation Decisions

> Document decisions as you build. Major changes -> also add to central ADR.md

### Technical Approach

**Hybrid onboarding flow**: Structured intake cards (6 questions) -> AI generation -> summary review -> conversational meal import -> apply & generate first week.

**Dual LLM provider strategy**:
- Claude Sonnet 4 (Anthropic SDK) for onboarding generation + meal chat (better structured reasoning)
- GPT-4o (OpenAI SDK, existing) retained for image/vision capture only

**Nutrition data**: AI parses user descriptions into structured ingredients, then calls USDA FoodData Central + Open Food Facts APIs as tools. Macros are calculated from real data, not AI estimates.

**Frontend streaming**: Vercel AI SDK `useChat` for the meal import chat step. Backend exposes standard SSE endpoint compatible with any client.

### Key Decisions
- **Claude Sonnet over GPT-4o for text tasks**: Better at structured reasoning, complex multi-step instructions, comparable cost ($3/1M in, $15/1M out vs $2.50/$10). GPT-4o kept for vision only.
- **USDA + Open Food Facts over AI-generated macros**: Real data is accurate and verifiable. AI handles parsing, external APIs handle nutrition facts.
- **Server-side onboarding state**: Enables resume, supports agentic patterns (tool log, conversation memory, context injection).
- **Standard SSE over Vercel-proprietary format**: Ensures native mobile clients can consume the same streaming endpoint.
- **Single long-lived feature branch**: All 9 sessions on `feat/ai-onboarding`, merged to main only when complete.

---

## Dependencies

### Upstream
- ADR-014 (Auth) -- user accounts, JWT auth, user_id scoping
- ADR-013 (AI Capture) -- OpenAI integration pattern, image capture infrastructure, cost logging
- Existing template system -- meal types, day templates, week plans, weekly generation services

### Downstream
- ADR-008 (Grocery List) -- onboarding creates the meal library that grocery list will parse
- Future native mobile app -- backend API designed for portability (standard SSE, JWT auth)

---

## Success Criteria

### Functional
- [ ] New user can go from registration to generated weekly plan in under 10 minutes
- [ ] AI-generated meal types and templates match user's stated schedule and goals
- [ ] Nutrition data for imported meals matches USDA reference values within 10% tolerance
- [ ] Resume works: user can close browser mid-flow and return to correct step
- [ ] Reset works: existing user can reconfigure from Settings without data corruption

### Non-Functional
- [ ] Performance: AI generation completes in < 15 seconds
- [ ] Performance: Nutrition lookup per ingredient < 2 seconds
- [ ] Performance: Apply step (create all entities + generate week) < 5 seconds
- [ ] Security: All endpoints require authentication, all data user-scoped
- [ ] Mobile: Full flow works on iOS Safari (mobile-first)

---

## Open Questions

- [ ] Should we cache USDA nutrition results in a local table to reduce API calls and improve speed?
- [ ] What happens to onboarding_state rows after completion -- keep forever or clean up after N days?
- [ ] Should the "Reset & reconfigure" flow delete existing data or create alongside?
- [ ] How to handle USDA API downtime -- graceful fallback to AI estimates with confidence flag?

---

*Created*: 2026-03-29
