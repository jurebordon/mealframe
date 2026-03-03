# Mealframe PRD -- Grocery List from Weekly Plan

## 1. Problem Statement

Mealframe generates a full weekly meal plan with specific meals and portion descriptions for each slot. Users currently have no way to derive a shopping list from this plan — they must manually scan each day's meals, mentally extract ingredients, and compile a grocery list themselves.

This is especially problematic because:

-   Portion descriptions are free-text (e.g., "150g chicken breast + 100g rice + mixed vegetables") — not structured ingredient data
-   Many meals don't require groceries (eaten at a restaurant, available at the office, pre-made items bought as-is)
-   The same meal can need groceries or not depending on context (e.g., "Banana + Protein Drink" needs groceries at home but not at the office)

The system needs to generate an aggregated, categorized grocery list from the weekly plan while intelligently excluding meals that don't require shopping.

------------------------------------------------------------------------

## 2. Goal

Generate a read-only, categorized grocery list from a weekly plan instance that:

1.  Extracts structured ingredients from free-text portion descriptions using AI
2.  Aggregates quantities across the week (e.g., "14 eggs" instead of "2 eggs" x7)
3.  Groups items by grocery store category (Produce, Dairy, Meat, etc.)
4.  Excludes meals marked as not needing groceries (eating out, office meals)
5.  Caches extraction results to avoid repeated AI calls

------------------------------------------------------------------------

## 3. Non-Goals

1.  No interactive checklist (checking off items while shopping)
2.  No manual item addition (adding "paper towels" to the list)
3.  No editing of extracted ingredients
4.  No offline support for grocery list (online-only for MVP)
5.  No recipe/cooking instructions
6.  No price estimation or store integration
7.  No ingredient-level nutritional breakdown

------------------------------------------------------------------------

## 4. Key Design Decision: Slot-Level Grocery Classification

### 4.1 The Problem

A meal like "Banana + Protein Drink" can be:

-   At the office on workdays → no groceries needed (available there)
-   At home on weekends → groceries needed

Tagging the meal itself as "eating out" or "home-cooked" doesn't work because the same meal entry is reused across different day contexts via round-robin.

### 4.2 The Decision

A `needs_groceries` boolean (default: `true`) lives on the **Day Template Slot**, not on the Meal.

-   When setting up "Normal Workday" template, the user marks office snack slots as `needs_groceries = false`
-   When setting up "Weekend" template, all slots default to `needs_groceries = true`
-   The flag propagates to `WeeklyPlanSlot` at generation time
-   The grocery list query simply filters `WHERE needs_groceries = true`

This means the classification is:

-   **Set once** per template (not per week)
-   **Context-aware** — same meal, different behavior depending on the day
-   **Zero friction** during weekly use — no per-week grocery decisions needed

------------------------------------------------------------------------

## 5. User Experience Flow

### 5.1 Setup (One-Time)

Inside Day Template Editor (Setup → Day Templates):

1.  User opens a template (e.g., "Normal Workday")
2.  Each slot row shows a "Groceries" toggle (default: on)
3.  User turns off the toggle for office-based slots
4.  User saves template

This is a one-time setup per template. Changes apply to all future weeks using that template.

------------------------------------------------------------------------

### 5.2 Viewing the Grocery List

Entry points:

-   **Desktop**: Sidebar navigation → "Grocery" link
-   **Mobile**: Week View → "Grocery List" button

Flow:

1.  User navigates to Grocery List page
2.  Page shows current week by default (week selector available)
3.  System fetches the weekly plan and extracts ingredients (first load may take 2-5 seconds for AI processing)
4.  Grocery list displays as categorized, aggregated items
5.  Subsequent views are instant (cached results)

------------------------------------------------------------------------

### 5.3 Display Format

The list is grouped by grocery store category:

```
PRODUCE
  Banana                           7
  Mixed vegetables                 ×3
  Broccoli                         200 g
  Tomato                           4

DAIRY & EGGS
  Egg                              14
  Greek yogurt                     750 g

MEAT & FISH
  Chicken breast                   900 g
  Salmon                           360 g

PANTRY & DRY
  Rice                             700 g
  Oats                             300 g
  Whey protein                     6 scoops
```

Formatting rules:

-   Countable items: just the number (e.g., "14")
-   Weighted/measured items: quantity + unit (e.g., "900 g")
-   Vague items: count multiplier (e.g., "×3" for "mixed vegetables" appearing in 3 meals)

------------------------------------------------------------------------

## 6. Functional Requirements

### 6.1 FR1 -- Needs-Groceries Classification

1.  `DayTemplateSlot` gains a `needs_groceries: boolean` field (default `true`).
2.  Value propagates to `WeeklyPlanSlot` at all generation points:
    -   Initial weekly plan generation
    -   Day template switching
    -   Day override clearing
    -   Weekly plan regeneration
3.  Ad-hoc meals default to `needs_groceries = true`.
4.  Template Editor UI shows a toggle per slot.

------------------------------------------------------------------------

### 6.2 FR2 -- AI Ingredient Extraction

1.  System parses `portion_description` into structured ingredients using an LLM.
2.  Each ingredient has: `name`, `quantity`, `unit`, `category`, `raw_text`, `is_vague`.
3.  Extraction is **lazy** — triggered on first grocery list view, not at plan generation.
4.  Results are cached as JSONB on `WeeklyPlanSlot.parsed_ingredients`.
5.  Cache semantics:
    -   `NULL` → not yet parsed (triggers extraction)
    -   `[]` → parsed, no ingredients found (cached empty)
    -   `[{...}]` → parsed with results (cached)
6.  Extraction runs concurrently for all unparsed slots via `asyncio.gather`.

------------------------------------------------------------------------

### 6.3 FR3 -- Cache Invalidation

The `parsed_ingredients` cache must be cleared (`NULL`) when:

1.  Meal is reassigned via slot picker (manual override)
2.  Weekly plan is regenerated (uncompleted slots get new meals)

This ensures the grocery list always reflects the current meal assignments.

------------------------------------------------------------------------

### 6.4 FR4 -- Aggregation

1.  Ingredients with the same normalized name AND same unit are summed.
2.  Ingredients with the same name but different units are kept as separate line items.
3.  Vague items (`is_vague = true`) are aggregated by occurrence count.
4.  Vague items are NOT expanded into specifics — "mixed vegetables" stays as "mixed vegetables".

------------------------------------------------------------------------

### 6.5 FR5 -- Category Grouping

Items are grouped by grocery store category, in this order:

1.  Produce
2.  Dairy & Eggs
3.  Meat & Fish
4.  Pantry & Dry
5.  Frozen
6.  Condiments & Oils
7.  Other

Categories are assigned by the LLM during extraction.

------------------------------------------------------------------------

### 6.6 FR6 -- Grocery List API

```
GET /api/v1/grocery-list?week_start_date=YYYY-MM-DD
```

-   `week_start_date` optional; defaults to current week's Monday
-   Returns `GroceryListResponse` with categories, items, slot count
-   404 if no weekly plan instance exists for the requested week
-   Requires authentication

------------------------------------------------------------------------

## 7. AI Pipeline

### 7.1 Extraction Prompt

The LLM receives each meal's `portion_description` and must return structured JSON:

```json
[
  {
    "name": "chicken breast",
    "quantity": 150,
    "unit": "g",
    "category": "Meat & Fish",
    "raw_text": "150g chicken breast",
    "is_vague": false
  },
  {
    "name": "mixed vegetables",
    "quantity": null,
    "unit": null,
    "category": "Produce",
    "raw_text": "mixed vegetables",
    "is_vague": true
  }
]
```

Requirements:

-   Normalized ingredient names (lowercase, singular noun)
-   Consistent unit normalization
-   Temperature 0 for deterministic output
-   JSON mode / structured output
-   Graceful degradation on failure (slot excluded from list, retried next request)

### 7.2 LLM Provider

Provider is abstracted behind an interface (TBD — will be decided alongside ADR-013 AI Capture, which shares the same infrastructure). The extraction task is simple and suitable for small/fast models.

### 7.3 Cost Considerations

-   Extraction runs once per slot per meal assignment (cached thereafter)
-   A typical week: ~15-25 slots needing groceries
-   Each extraction: ~100 input tokens, ~200 output tokens
-   Total per week: negligible cost with any provider

------------------------------------------------------------------------

## 8. Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Slot with no meal (`meal_id = NULL`) | Skipped entirely |
| Ad-hoc meal (`is_adhoc = true`) | Included; defaults to `needs_groceries = true` |
| Manual override meal | Included; user explicitly chose this meal |
| Empty `portion_description` | Extraction returns `[]`; cached as empty |
| LLM failure (timeout, API error) | `parsed_ingredients` stays `NULL`; slot excluded from list; no error surfaced to user; retried on next request |
| LLM returns invalid JSON | Treated same as LLM failure |
| Same ingredient, different units | Kept as separate line items (e.g., "100g oats" and "1 cup oats") |
| Meal swapped mid-week | Cache invalidated; re-extracted on next grocery list view |
| Week with no plan generated | 404 response; frontend shows "no plan" empty state |
| All slots marked `needs_groceries = false` | Empty grocery list; frontend shows appropriate message |

------------------------------------------------------------------------

## 9. Data Model Changes

### 9.1 DayTemplateSlot (existing table)

New column:

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `needs_groceries` | `boolean NOT NULL` | `true` | Include this slot's meals in the grocery list |

### 9.2 WeeklyPlanSlot (existing table)

New columns:

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `needs_groceries` | `boolean NOT NULL` | `true` | Copied from DayTemplateSlot at generation time |
| `parsed_ingredients` | `JSONB NULL` | `NULL` | Cached AI extraction result; NULL = not parsed |

------------------------------------------------------------------------

## 10. UI Specifications

### 10.1 Grocery List Page

-   Mobile-first layout, max-width container
-   Page header: "Grocery List" with shopping cart icon
-   Week selector for navigating between weeks
-   Category cards with item rows
-   Loading skeleton during first extraction (2-5 second latency)
-   Empty state when no ingredients or no plan

### 10.2 Template Editor Enhancement

-   Each slot row gains a "Groceries" toggle (Switch component)
-   Default: on (true)
-   Visual: small, non-intrusive — secondary to the meal type selector
-   Persists on save with existing template save flow

### 10.3 Navigation

-   **Sidebar** (desktop): Add "Grocery" link with ShoppingCart icon
-   **Bottom nav** (mobile): NOT added (already 5 items). Instead, a contextual "Grocery List" button on the Week View page
-   **Week View**: Button/link to grocery list for the displayed week

------------------------------------------------------------------------

## 11. Phase Breakdown

### 11.1 Phase 1 -- MVP (This PRD)

-   `needs_groceries` classification on template slots
-   AI ingredient extraction with JSONB caching
-   Aggregated, categorized, read-only grocery list
-   Online-only

### 11.2 Phase 2 -- Interactivity (Future)

-   Checkable shopping list (tick items off while shopping)
-   State persistence (checked items survive app close)
-   Manual item addition ("paper towels", "cleaning supplies")

### 11.3 Phase 3 -- Intelligence (Future)

-   Smart unit conversion and normalization improvements
-   Learning from user corrections
-   Pantry tracking (exclude items you already have)
-   Multi-store optimization
-   Cost estimation

------------------------------------------------------------------------

## 12. Implementation Sessions

### Session 1: Database & Backend Foundation

-   Alembic migration (3 new columns)
-   Model and schema updates
-   `needs_groceries` propagation through all 4 slot-creation paths
-   Cache invalidation on meal reassignment
-   Frontend type updates
-   Template editor toggle UI

### Session 2: AI Extraction & Grocery List API

-   LLM client abstraction
-   Ingredient extraction service with concurrent processing
-   Aggregation algorithm
-   `GET /api/v1/grocery-list` endpoint
-   Grocery schemas

### Session 3: Frontend Grocery List Page

-   API client function and TanStack Query hook
-   `/grocery` page with category cards
-   Loading, error, and empty states
-   Navigation updates (sidebar + Week View button)

------------------------------------------------------------------------

## 13. Dependencies

| Dependency | Status | Required For |
|------------|--------|-------------|
| ADR-014 (Auth) | Complete | `get_current_user` on grocery endpoint |
| ADR-012 (Completion Statuses) | Complete | `social` status context |
| ADR-008 (Grocery Strategy) | Proposed → to be Accepted | This PRD resolves ADR-008 |
| LLM Provider SDK | TBD | Shared with ADR-013 (AI Capture) |

------------------------------------------------------------------------

## 14. Success Metrics

### 14.1 Primary Metric

-   % of weeks where the grocery list is viewed at least once

### 14.2 Secondary Metrics

-   AI extraction success rate > 95% (per slot)
-   First-load latency < 5 seconds
-   Subsequent-load latency < 500ms (cached)

### 14.3 Behavioral Success

-   User stops maintaining a separate shopping list outside the app

------------------------------------------------------------------------

## 15. Open Technical Decisions

To finalize during implementation:

1.  LLM provider selection (shared decision with ADR-013)
2.  Exact LLM prompt wording (iterate during Session 2)
3.  Whether to batch all portion descriptions in one LLM call vs. one call per slot
4.  Week View button placement and styling for mobile grocery entry point
5.  Category icon/color assignments for visual distinction
