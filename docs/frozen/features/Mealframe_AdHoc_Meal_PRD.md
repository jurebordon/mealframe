# Mealframe PRD -- Ad Hoc Meal Capture (Image + Voice)

## 1. Problem Statement

Mealframe currently supports structured meal tracking via:

-   Week templates\
-   Day templates\
-   Predefined database meals

When the user deviates from the plan and consumes a meal not in the
database, logging becomes friction-heavy. This creates under-tracking
and reduces reliability of daily macro evaluation.

The system needs a low-friction way to log real-world, off-plan meals
using photo or dictation, with approximate macro estimation.

------------------------------------------------------------------------

## 2. Goal

Enable users to log ad hoc meals in under 5 seconds of interaction,
without manual macro entry, while maintaining approximate macro tracking
accuracy at the daily level.

The system must:

1.  Capture real-world meal input (image first, voice optional in Phase
    2)
2.  Estimate macronutrients (kcal, protein, carbs, fat)
3.  Assign meal type (user-selected or inferred)
4.  Store results without requiring confirmation
5.  Update daily totals automatically

------------------------------------------------------------------------

## 3. Non-Goals

1.  No per-meal macro bounding
2.  No "healthy meal generation"
3.  No meal optimization toward daily targets
4.  No manual correction loop in MVP
5.  No micronutrient tracking
6.  No precision nutrition targeting

This is ground-truth approximation only.

------------------------------------------------------------------------

## 4. User Experience Flow

### 4.1 Entry Point

Inside Daily Plan view:

User taps: **Add Meal**

Two options:

1.  Select from Database\
2.  Add Ad Hoc Meal

------------------------------------------------------------------------

### 4.2 Ad Hoc Meal Flow -- Image (MVP Primary)

1.  User selects "Add Ad Hoc Meal"
2.  User optionally selects meal type (Breakfast / Lunch / Dinner /
    Snack)
    -   If not selected → agent infers
3.  User takes photo
4.  User presses Upload
5.  App can be closed

Processing happens fully in background.

No waiting screen required.\
No confirmation screen required.

Meal appears in daily list once processed.

------------------------------------------------------------------------

### 4.3 Voice Dictation (Phase 2)

1.  User selects "Add Ad Hoc Meal"
2.  Optional meal type selection
3.  User dictates ingredients
4.  Confirm
5.  Background processing

------------------------------------------------------------------------

## 5. Functional Requirements

### 5.1 FR1 -- Background Processing

1.  Image upload triggers async AI pipeline.
2.  User does not wait for macro estimation.
3.  Meal record created immediately with status = "processing".

------------------------------------------------------------------------

### 5.2 FR2 -- AI Estimation

Agent must:

1.  Identify food items.
2.  Estimate portion sizes.
3.  Estimate:
    -   Calories
    -   Protein
    -   Carbohydrates
    -   Fat
4.  Return estimated confidence score.
5.  Return structured JSON.

No adjustment based on daily targets.

------------------------------------------------------------------------

### 5.3 FR3 -- Meal Type Logic

Priority:

1.  User-selected meal type (if provided)
2.  Agent inference (fallback)

------------------------------------------------------------------------

### 5.4 FR4 -- Storage

Each meal must store:

    Meal {
      id
      name
      meal_type
      macros: {
        kcal
        protein
        carbs
        fat
      }
      source: "ad_hoc_image" | "ad_hoc_voice"
      confidence_score
      raw_input_reference
      processing_status
      created_at
    }

Final schema will align with existing production models.

------------------------------------------------------------------------

### 5.5 FR5 -- Raw Input Retention

System must store:

1.  Image file reference OR
2.  Raw transcription text

Purpose:

-   Future reprocessing
-   Model improvement
-   Debugging

------------------------------------------------------------------------

## 6. AI Pipeline -- MVP

### 6.1 Image Processing

1.  Vision model analysis
2.  Identify foods + portion estimates
3.  Estimate macros using inference + web search (if needed)
4.  Return structured JSON

------------------------------------------------------------------------

### 6.2 Voice Processing

1.  Whisper transcription
2.  Structured extraction of ingredients
3.  Macro estimation

------------------------------------------------------------------------

## 7. Expected AI Output Contract

Agent must return:

``` json
{
  "meal_name": "Grilled chicken with rice and salad",
  "meal_type": "lunch",
  "macros": {
    "kcal": 720,
    "protein": 55,
    "carbs": 70,
    "fat": 22
  },
  "confidence_score": 0.78,
  "identified_items": [
    {
      "name": "grilled chicken breast",
      "estimated_quantity": "200g"
    },
    {
      "name": "white rice",
      "estimated_quantity": "250g"
    },
    {
      "name": "mixed salad",
      "estimated_quantity": "100g"
    }
  ]
}
```

Strict JSON response required.

------------------------------------------------------------------------

## 8. Success Metrics

### 8.1 Primary Metric

-   \% of days with at least one ad hoc meal successfully processed

### 8.2 Secondary Metrics

-   Processing time \< 10 seconds (background)
-   Failure rate \< 5%
-   Average confidence score \> 0.7

### 8.3 Behavioral Success

-   User does not avoid logging off-plan meals

------------------------------------------------------------------------

## 9. Accuracy Philosophy

Optimizes for:

-   Behavioral compliance
-   Daily-level macro awareness
-   ±10--20% macro accuracy tolerance

Not for:

-   Competitive bodybuilding precision
-   Clinical nutrition tracking

------------------------------------------------------------------------

## 10. Edge Cases

1.  Multiple meals in one photo
2.  Mixed dishes (e.g., stew)
3.  Unclear portion sizes
4.  Packaged food with visible label
5.  Low-quality image

Fallback behavior:

-   Return best estimate with lower confidence score
-   Never fail silently
-   If AI fails → log meal with status = "estimation_failed"

------------------------------------------------------------------------

## 11. Phase Breakdown

### 11.1 Phase 1 -- Image Only

-   Upload
-   Background processing
-   JSON output
-   Store raw image

### 11.2 Phase 2 -- Voice Dictation

-   Whisper transcription
-   Ingredient parsing
-   Same estimation pipeline

### 11.3 Phase 3 -- Improvements

-   Confidence-based reprocessing
-   Learning from historical corrections
-   Auto-detection of repeated meals
-   Optional correction UI

------------------------------------------------------------------------

## 12. Architectural Considerations

1.  Async job queue required
2.  Idempotent processing
3.  Versioned AI model tracking
4.  Store model version per meal for traceability

------------------------------------------------------------------------

## 13. Offline Mode Handling (MVP: Disabled)

### 13.1 Product Decision

Ad Hoc Meal Capture does not support offline mode in MVP.

Rationale:

-   AI inference requires cloud processing.
-   Background architecture assumes network availability.
-   Offline support would require:
    -   Local storage queue
    -   Sync reconciliation
    -   Deferred inference logic
    -   Retry and conflict resolution policies

This adds complexity disproportionate to MVP value.

------------------------------------------------------------------------

### 13.2 UX Behavior When Offline

If user attempts to:

-   Open Ad Hoc Meal Capture
-   Upload image
-   Submit voice dictation

System behavior:

1.  Detect network unavailability before upload.

2.  Show blocking message:

    "Internet connection required to process ad hoc meals."

3.  Disable upload action until connectivity is restored.

No local caching.\
No queued background submission.

------------------------------------------------------------------------

### 13.3 Connectivity Drop During Upload

If connection fails mid-upload:

1.  Upload fails.

2.  No meal record is created.

3.  User sees:

    "Upload failed. Please try again."

No partial records stored.

------------------------------------------------------------------------

### 13.4 Future Consideration (Phase 3+)

Potential offline support:

-   Temporary local image storage
-   Deferred upload when online
-   Background sync queue
-   Status badge ("Pending Processing")

Not included in MVP scope.

------------------------------------------------------------------------

## 14. Open Technical Decisions

To finalize in Tech Spec:

1.  Vision model selection
2.  Web search usage policy
3.  Max image size
4.  Queue implementation strategy
5.  Retry logic policy
6.  Cost control strategy
