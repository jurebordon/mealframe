# Project Vision

**Last Updated**: 2026-02-04

## 1. Problem Statement

Decision fatigue and stress-induced overeating, particularly during high-stress evening periods, undermine nutrition goals. The core issue isn't *what* to eat, but *how much* and the in-the-moment decisions that lead to overconsumption. Target users know nutrition well but struggle with stress-driven overeating, eating correct foods in excessive quantities, decision paralysis when willpower is depleted, and high-friction planning workflows (Google Sheets).

## 2. Solution Hypothesis

Remove in-the-moment decisions by pre-planning exact meals and portions when calm, then following authoritative instructions at meal time. Automated round-robin rotation eliminates weekly planning effort. Mobile-first PWA provides instant access at meal time.

## 3. Target Users

Health-conscious individuals (initially personal use) who know their nutrition needs, struggle with adherence under stress, and want a "tell me what to eat" system rather than a discovery or suggestion tool.

## 4. Success Metrics

- Evening overeating incidents decrease significantly
- Decision fatigue at meal time eliminated
- Plan adherence >80% "Followed" rate
- Daily engagement: open app 3+ times/day
- Completion rate: >70% of slots marked per day
- Streak length: average >5 days

## 5. Non-Goals

- Not a calorie tracker replacement (used alongside existing tracker)
- Not a recipe discovery app (user already knows their meals)
- Not focused on social features or food logging clinical accuracy
- Not enforcing macro targets (reflection only, never enforcement)
- Not a barcode scanner or food database (free-text portions, user-defined)

## 6. Tech Stack

- **Backend**: FastAPI (Python), PostgreSQL 15+, SQLAlchemy async, Alembic
- **Frontend**: Next.js 14+ (React/TypeScript), Tailwind CSS, Zustand + TanStack Query, next-pwa
- **Infrastructure**: Docker Compose, GitHub Actions → Proxmox homelab VM, Nginx Proxy Manager
- **AI**: OpenAI GPT-4o (meal capture), Resend (email), authlib (Google OAuth)

## 7. Pivot History

- 2026-01-19 — Initial concept defined; greenfield MVP for personal use
- 2026-02-04 — Phase 1 (MVP) complete. Phase 2 begins: multi-user auth, AI meal capture
- 2026-03-17 — SpecFlow documentation migrated to new framework structure

<!-- Append new entries when direction changes significantly -->
