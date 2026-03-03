# Mealframe PRD -- AI Meal Capture (Image)

> Supersedes relevant sections of `Mealframe_AdHoc_Meal_PRD.md`. The original PRD covered both "ad-hoc meal from library" (now implemented) and "AI-powered capture" (this PRD). This document covers only the AI capture feature with revised architectural decisions.

## 1. Problem Statement

Mealframe supports ad-hoc meal logging via the existing "Add Meal" flow, but only from meals already in the user's library. When users eat something not in the database — a restaurant meal, a friend's cooking, an improvised dish — they have two bad options:

1.  Manually create a new meal entry with estimated macros (high friction, error-prone)
2.  Skip logging entirely (daily totals become inaccurate)

The system needs a way to capture real-world, off-plan meals from a photo with AI-estimated macros, in under 10 seconds of user interaction.

------------------------------------------------------------------------

## 2. What Already Exists

These features are implemented and this PRD builds on top of them:

| Feature | Status | How it works |
|---------|--------|-------------|
| Ad-hoc meal from library | Done | "Add Meal" → MealPicker → select existing meal → creates `is_adhoc=true` slot |
| Ad-hoc slot deletion | Done | Swipe to remove ad-hoc slots |
| Completion statuses | Done (ADR-012) | 5 statuses: followed, equivalent, skipped, deviated, social |
| `actual_meal_id` tracking | Done | For `equivalent` and `deviated`, user can link what they actually ate |
| Per-slot meal reassignment | Done (ADR-011) | Swap any slot's meal via MealPicker |

------------------------------------------------------------------------

## 3. Goal

Enable users to log off-plan meals by taking a photo:

1.  Take photo of food
2.  AI estimates meal name, portion description, and macros
3.  User reviews and confirms (one tap)
4.  Meal saved to library and linked to slot
5.  Daily totals update automatically

Processing is **synchronous** — user waits 3-5 seconds with a spinner, then sees the result. No background job queue.

------------------------------------------------------------------------

## 4. Non-Goals

1.  No voice dictation in MVP (deferred to Phase 2)
2.  No background/async processing pipeline
3.  No job queue infrastructure
4.  No manual macro editing in the capture flow (edit later in Meal Library)
5.  No micronutrient estimation (sugar, fiber, sat fat)
6.  No barcode/label scanning
7.  No offline support
8.  No multi-meal detection from a single photo (best effort for primary dish)

------------------------------------------------------------------------

## 5. User Experience Flow

### 5.1 Entry Point A -- Standalone (Add Meal)

Inside Today View:

1.  User taps **"Add Meal"** button
2.  Options: "Select from Library" (existing) | **"Capture with Photo"** (new)
3.  User taps "Capture with Photo"
4.  Camera opens (or file picker on desktop)
5.  User takes/selects photo
6.  Spinner: "Analyzing your meal..." (3-5 seconds)
7.  Confirmation screen shows:
    -   AI-generated meal name
    -   Portion description
    -   Estimated macros (kcal, protein, carbs, fat)
    -   Meal type selector (pre-filled by AI, user can change)
8.  User taps **"Save"** → meal created, ad-hoc slot added, daily totals update
9.  Or taps **"Retry"** → back to camera
10. Or taps **"Cancel"** → nothing saved

------------------------------------------------------------------------

### 5.2 Entry Point B -- Deviated Completion

Inside Today View, when marking a planned slot:

1.  User swipes a slot → completion sheet opens
2.  User selects **"Deviated"**
3.  Options: "Pick from Library" (existing `actual_meal_id` flow) | **"Capture with Photo"** (new)
4.  If "Capture with Photo" → same flow as 5.1 steps 4-10
5.  On save: meal linked as `actual_meal_id` on the deviated slot (not a new ad-hoc slot)

------------------------------------------------------------------------

### 5.3 Confirmation Screen

```
┌─────────────────────────────┐
│  ✓ Meal Identified          │
│                             │
│  Grilled Chicken with Rice  │
│                             │
│  200g grilled chicken       │
│  breast + 250g white rice   │
│  + 100g mixed salad         │
│                             │
│  ┌────┐ ┌────┐ ┌────┐      │
│  │720 │ │ 55 │ │ 70 │ │ 22 │
│  │kcal│ │ P  │ │ C  │ │ F  │
│  └────┘ └────┘ └────┘      │
│                             │
│  Meal Type: [Lunch ▾]      │
│                             │
│  [ Retry ]    [ Save ]      │
└─────────────────────────────┘
```

------------------------------------------------------------------------

## 6. Functional Requirements

### 6.1 FR1 -- Synchronous Processing

1.  Frontend sends image to backend via multipart POST.
2.  Backend calls vision model API synchronously (within request lifecycle).
3.  Backend returns structured meal data in the HTTP response.
4.  No background tasks, no job queue, no polling.
5.  Request timeout: 15 seconds. If vision API exceeds this, return error.

------------------------------------------------------------------------

### 6.2 FR2 -- AI Estimation

Vision model must:

1.  Identify food items in the photo.
2.  Estimate portion sizes.
3.  Generate a human-readable meal name.
4.  Generate a portion description matching existing format (e.g., "200g chicken breast + 250g rice + mixed salad").
5.  Estimate macros: calories (kcal), protein (g), carbs (g), fat (g).
6.  Return confidence score (0.0-1.0).
7.  Return identified items with estimated quantities.

No adjustment based on daily targets. Pure estimation of what's in the photo.

------------------------------------------------------------------------

### 6.3 FR3 -- Meal Type Logic

Priority:

1.  User-selected meal type on confirmation screen
2.  AI inference (pre-fills the selector)
3.  Fallback: user's most common meal type for the current time of day

------------------------------------------------------------------------

### 6.4 FR4 -- Meal Persistence

AI-captured meals are saved to the Meal Library as real `Meal` records:

-   `source = "ai_capture"` (new field, distinguishes from `"manual"` entries)
-   Excluded from round-robin rotation by default
-   Visible in Meal Library (filterable by source)
-   User can manually pick them via MealPicker for future use
-   Future: option to "promote" to round-robin rotation (not in MVP)

------------------------------------------------------------------------

### 6.5 FR5 -- Image Storage

Original photos are stored on the server:

-   Storage location: local volume mount (e.g., `/data/captures/{user_id}/{uuid}.jpg`)
-   Path stored in `Meal.image_path` field
-   Images resized/compressed before storage (max 1920px, JPEG quality 85)
-   Purpose: debugging, future reprocessing, potential meal photo display

------------------------------------------------------------------------

### 6.6 FR6 -- Slot Linking

Depending on entry point:

-   **Standalone (Add Meal)**: Creates new `WeeklyPlanSlot` with `is_adhoc=true`, `meal_id` pointing to new meal
-   **Deviated**: Sets `actual_meal_id` on existing slot to the new meal. Does NOT create a new slot.

------------------------------------------------------------------------

## 7. AI Output Contract

Vision model must return:

```json
{
  "meal_name": "Grilled chicken with rice and salad",
  "portion_description": "200g grilled chicken breast + 250g white rice + 100g mixed salad",
  "macros": {
    "calories_kcal": 720,
    "protein_g": 55,
    "carbs_g": 70,
    "fat_g": 22
  },
  "confidence_score": 0.78,
  "identified_items": [
    {"name": "grilled chicken breast", "estimated_quantity": "200g"},
    {"name": "white rice", "estimated_quantity": "250g"},
    {"name": "mixed salad", "estimated_quantity": "100g"}
  ],
  "suggested_meal_type": "lunch"
}
```

Notes:

-   `portion_description` must follow the existing `+`-delimited format so it's compatible with the Grocery List feature (ADR-008), which parses this field for ingredient extraction.
-   `identified_items` is informational and stored for future use. Not displayed in MVP confirmation screen.
-   `suggested_meal_type` should map to the user's existing meal type names if possible.

------------------------------------------------------------------------

## 8. Data Model Changes

### 8.1 Meal Table Extensions

New columns on `meal` table:

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `source` | `Text NOT NULL` | `"manual"` | Origin: `"manual"`, `"ai_capture"` (future: `"ai_voice"`) |
| `confidence_score` | `Numeric(3,2) NULL` | `NULL` | AI confidence (0.00-1.00). NULL for manual meals |
| `image_path` | `Text NULL` | `NULL` | Server path to captured image |
| `ai_model_version` | `Text NULL` | `NULL` | Model identifier (e.g., "gpt-4o-2024-08-06") for traceability |

NOT added (removed from original PRD):

-   `processing_status` — not needed with synchronous processing
-   `raw_input_reference` — replaced by `image_path` (more specific)

### 8.2 Round-Robin Exclusion

The round-robin algorithm in `backend/app/services/weekly.py` (`get_next_meal_for_type`) must filter to `source = "manual"` only. AI-captured meals should not be auto-assigned to future weeks.

### 8.3 OpenAI Usage Logging (Optional)

Simple logging table for cost tracking:

| Column | Type | Description |
|--------|------|-------------|
| `id` | `UUID PK` | |
| `user_id` | `UUID FK` | |
| `model` | `Text` | Model used |
| `tokens_prompt` | `Integer` | Input tokens |
| `tokens_completion` | `Integer` | Output tokens |
| `cost_estimate_usd` | `Numeric(8,6)` | Estimated cost |
| `created_at` | `Timestamp` | |

This is informational only — no enforcement or rate limiting in MVP.

------------------------------------------------------------------------

## 9. API Changes

### 9.1 New Endpoint

```
POST /api/v1/meals/ai-capture
Content-Type: multipart/form-data

Body:
  - image: file (JPEG/PNG, max 10MB)
  - meal_type_id: UUID (optional, user-selected meal type)
```

Response (200):

```json
{
  "meal": {
    "id": "uuid",
    "name": "Grilled chicken with rice and salad",
    "portion_description": "200g grilled chicken breast + ...",
    "calories_kcal": 720,
    "protein_g": 55,
    "carbs_g": 70,
    "fat_g": 22,
    "source": "ai_capture",
    "confidence_score": 0.78,
    "image_path": "/data/captures/user-uuid/meal-uuid.jpg"
  },
  "suggested_meal_type": "lunch",
  "identified_items": [...]
}
```

This endpoint **analyzes but does not save**. The frontend shows the confirmation screen, and on "Save", calls existing endpoints:

-   Standalone: `POST /meals` (create meal) → `POST /today/slots` (create ad-hoc slot)
-   Deviated: `POST /meals` (create meal) → `POST /slots/{id}/complete` with `actual_meal_id`

This keeps the capture endpoint stateless and reuses existing CRUD flows.

### 9.2 Existing Endpoint Modifications

-   `GET /meals` — support filtering by `source` query parameter (for library UI)
-   `POST /meals` — accept `source`, `confidence_score`, `image_path`, `ai_model_version` in create schema
-   Round-robin: filter by `source = "manual"` in `get_next_meal_for_type`

------------------------------------------------------------------------

## 10. Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Unrecognizable food | Return best guess with low confidence. Never fail silently. |
| Multiple dishes in photo | Estimate as single combined meal (best effort). Future: multi-meal detection. |
| Non-food photo | Return error: "Could not identify food in this image." |
| Blurry/dark photo | Best effort estimate with lower confidence score. |
| Packaged food with visible label | Read label if possible, estimate otherwise. |
| Very large image (>10MB) | Reject with 413 error before sending to vision API. |
| Vision API timeout (>15s) | Return 504: "Analysis took too long. Please try again." |
| Vision API error | Return 502: "Could not analyze image. Please try again." |
| User offline | Frontend detects and shows: "Internet connection required." Camera button disabled. |
| Connectivity drops mid-upload | Request fails. No partial records. "Upload failed. Please try again." |

------------------------------------------------------------------------

## 11. Accuracy Philosophy

Optimizes for:

-   Behavioral compliance (user logs the meal instead of skipping)
-   Daily-level macro awareness (±10-20% tolerance)
-   Getting something logged quickly

Not for:

-   Competitive bodybuilding precision
-   Clinical nutrition tracking
-   Exact calorie counting

------------------------------------------------------------------------

## 12. Phase Breakdown

### 12.1 Phase 1 -- Image Capture (This PRD)

-   Synchronous image → AI → confirmation → save
-   Image storage on local volume
-   Two entry points (standalone + deviated)
-   Library persistence with round-robin exclusion
-   LLM infrastructure reusable by Grocery List (ADR-008)

### 12.2 Phase 2 -- Voice Dictation

-   Whisper transcription → structured extraction → same confirmation flow
-   `source = "ai_voice"`
-   Same sync processing model
-   Same confirmation screen (text-based instead of image-based)

### 12.3 Phase 3 -- Intelligence

-   Macro editing on confirmation screen
-   "Promote to rotation" toggle in Meal Library
-   Confidence-based reprocessing
-   Auto-detection of repeated meals ("this looks like your usual lunch")
-   Photo display in meal detail view

------------------------------------------------------------------------

## 13. Implementation Sessions

### Session 1: LLM Infrastructure + Backend

-   LLM client setup (provider TBD, likely OpenAI GPT-4o for vision)
-   Alembic migration: add `source`, `confidence_score`, `image_path`, `ai_model_version` to `meal`
-   Model and schema updates
-   Round-robin filter update (`source = "manual"` only)
-   Image storage utility (resize, compress, write to local volume)
-   `POST /meals/ai-capture` endpoint (analyze only, stateless)
-   Vision prompt design and testing
-   Usage logging table (optional)

### Session 2: Backend Integration + Testing

-   Wire AI capture response into existing `POST /meals` create flow
-   Update `POST /meals` schema to accept new fields
-   `GET /meals` source filter
-   Integration tests (mocked vision API)
-   End-to-end test with real vision API call

### Session 3: Frontend -- Capture UI

-   Camera/file input component
-   "Capture with Photo" option in Add Meal flow
-   Loading spinner during analysis
-   Confirmation screen (meal name, macros, meal type selector)
-   Save/Retry/Cancel actions
-   Error states

### Session 4: Frontend -- Deviated Flow + Polish

-   Wire "Capture with Photo" into deviated completion flow
-   Meal Library: `source` filter/badge for AI-captured meals
-   Offline detection (disable camera button when offline)
-   Image compression on frontend before upload

------------------------------------------------------------------------

## 14. Dependencies

| Dependency | Status | Required For |
|------------|--------|-------------|
| ADR-014 (Auth) | Complete | `get_current_user`, usage metering |
| ADR-012 (Completion Statuses) | Complete | `deviated` entry point |
| Ad-hoc meal CRUD | Complete | Slot creation flow (`POST /today/slots`) |
| Vision API provider | TBD | Core AI functionality |

------------------------------------------------------------------------

## 15. Grocery List Compatibility

The AI output contract includes `portion_description` in the existing `+`-delimited format. This ensures that AI-captured meals are compatible with the Grocery List feature (ADR-008), which parses `portion_description` for ingredient extraction.

When an AI-captured meal has `needs_groceries = true` on its slot, the grocery list will parse its `portion_description` the same way as any manual meal.

------------------------------------------------------------------------

## 16. Success Metrics

### 16.1 Primary Metric

-   % of `deviated` completions that use AI capture (vs. leaving `actual_meal_id` empty)

### 16.2 Secondary Metrics

-   AI analysis latency < 5 seconds (p95)
-   Vision API failure rate < 5%
-   Average confidence score > 0.7
-   % of confirmations accepted without retry

### 16.3 Behavioral Success

-   Users stop skipping off-plan meal logging

------------------------------------------------------------------------

## 17. Open Technical Decisions

To finalize during implementation:

1.  Vision model selection (GPT-4o vs Claude vision vs other)
2.  Exact vision prompt wording (iterate during Session 1)
3.  Image storage path convention and retention policy
4.  Max image dimensions before resize
5.  Whether to show confidence score to user on confirmation screen
6.  Frontend camera API vs file input (mobile camera access patterns)
