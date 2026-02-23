/**
 * TypeScript types matching backend Pydantic schemas.
 * These types are used throughout the frontend for API responses.
 */

// ============================================================================
// Common Types
// ============================================================================

export type CompletionStatus = 'followed' | 'adjusted' | 'skipped' | 'replaced' | 'social'

export type Weekday = 0 | 1 | 2 | 3 | 4 | 5 | 6

export const WEEKDAY_NAMES: Record<Weekday, string> = {
  0: 'Monday',
  1: 'Tuesday',
  2: 'Wednesday',
  3: 'Thursday',
  4: 'Friday',
  5: 'Saturday',
  6: 'Sunday',
}

// ============================================================================
// Meal Type
// ============================================================================

export interface MealTypeCompact {
  id: string
  name: string
}

export interface MealTypeResponse {
  id: string
  name: string
  description: string | null
  tags: string[]
  created_at: string
  updated_at: string
}

export interface MealTypeWithCount extends MealTypeResponse {
  meal_count: number
}

export interface MealTypeCreate {
  name: string
  description?: string | null
  tags?: string[]
}

export interface MealTypeUpdate {
  name?: string
  description?: string | null
  tags?: string[]
}

// ============================================================================
// Meal
// ============================================================================

export interface MealCompact {
  id: string
  name: string
  portion_description: string
  calories_kcal: number | null
  protein_g: number | null
  carbs_g: number | null
  sugar_g: number | null
  fat_g: number | null
  saturated_fat_g: number | null
  fiber_g: number | null
}

export interface MealResponse {
  id: string
  name: string
  portion_description: string
  calories_kcal: number | null
  protein_g: number | null
  carbs_g: number | null
  sugar_g: number | null
  fat_g: number | null
  saturated_fat_g: number | null
  fiber_g: number | null
  notes: string | null
  created_at: string
  updated_at: string
  meal_types: MealTypeCompact[]
}

export interface MealListItem {
  id: string
  name: string
  portion_description: string
  calories_kcal: number | null
  protein_g: number | null
  carbs_g: number | null
  sugar_g: number | null
  fat_g: number | null
  saturated_fat_g: number | null
  fiber_g: number | null
  meal_types: MealTypeCompact[]
}

export interface MealCreate {
  name: string
  portion_description: string
  calories_kcal?: number | null
  protein_g?: number | null
  carbs_g?: number | null
  sugar_g?: number | null
  fat_g?: number | null
  saturated_fat_g?: number | null
  fiber_g?: number | null
  notes?: string | null
  meal_type_ids?: string[]
}

export interface MealUpdate {
  name?: string
  portion_description?: string
  calories_kcal?: number | null
  protein_g?: number | null
  carbs_g?: number | null
  sugar_g?: number | null
  fat_g?: number | null
  saturated_fat_g?: number | null
  fiber_g?: number | null
  notes?: string | null
  meal_type_ids?: string[]
}

// ============================================================================
// Day Template
// ============================================================================

export interface DayTemplateSlotResponse {
  id: string
  position: number
  meal_type: MealTypeCompact
}

export interface DayTemplateCompact {
  id: string
  name: string
}

export interface DayTemplateResponse {
  id: string
  name: string
  notes: string | null
  max_calories_kcal: number | null
  max_protein_g: number | null
  created_at: string
  updated_at: string
  slots: DayTemplateSlotResponse[]
}

export interface DayTemplateListItem {
  id: string
  name: string
  notes: string | null
  max_calories_kcal: number | null
  max_protein_g: number | null
  slot_count: number
  slot_preview: string | null
}

export interface DayTemplateSlotCreate {
  position: number
  meal_type_id: string
}

export interface DayTemplateCreate {
  name: string
  notes?: string | null
  max_calories_kcal?: number | null
  max_protein_g?: number | null
  slots?: DayTemplateSlotCreate[]
}

export interface DayTemplateUpdate {
  name?: string
  notes?: string | null
  max_calories_kcal?: number | null
  max_protein_g?: number | null
  slots?: DayTemplateSlotCreate[]
}

// ============================================================================
// Week Plan (Template)
// ============================================================================

export interface WeekPlanCompact {
  id: string
  name: string
}

export interface WeekPlanDayResponse {
  id: string
  weekday: Weekday
  weekday_name: string
  day_template: DayTemplateCompact
}

export interface WeekPlanResponse {
  id: string
  name: string
  is_default: boolean
  created_at: string
  updated_at: string
  days: WeekPlanDayResponse[]
}

export interface WeekPlanListItem {
  id: string
  name: string
  is_default: boolean
  day_count: number
}

export interface WeekPlanDayCreate {
  weekday: Weekday
  day_template_id: string
}

export interface WeekPlanCreate {
  name: string
  is_default?: boolean
  days?: WeekPlanDayCreate[]
}

export interface WeekPlanUpdate {
  name?: string
  is_default?: boolean
  days?: WeekPlanDayCreate[]
}

// ============================================================================
// Weekly Plan Instance (Generated)
// ============================================================================

export interface WeeklyPlanSlotBase {
  id: string
  position: number
  meal_type: MealTypeCompact | null
  meal: MealCompact | null
  completion_status: CompletionStatus | null
  completed_at: string | null
  is_adhoc: boolean
  is_manual_override: boolean
}

export interface WeeklyPlanSlotWithNext extends WeeklyPlanSlotBase {
  is_next: boolean
}

export interface AddAdhocSlotRequest {
  meal_id: string
}

export interface CompletionSummary {
  completed: number
  total: number
}

export interface WeeklyPlanInstanceDayResponse {
  date: string
  weekday: string
  template: DayTemplateCompact | null
  is_override: boolean
  override_reason: string | null
  slots: WeeklyPlanSlotBase[]
  completion_summary: CompletionSummary
}

export interface WeeklyPlanInstanceResponse {
  id: string
  week_start_date: string
  week_plan: WeekPlanCompact | null
  days: WeeklyPlanInstanceDayResponse[]
}

// ============================================================================
// Today View
// ============================================================================

export interface TodayStats {
  completed: number
  total: number
  streak_days: number
}

export interface TodayResponse {
  date: string
  weekday: string
  template: DayTemplateCompact | null
  is_override: boolean
  override_reason: string | null
  slots: WeeklyPlanSlotWithNext[]
  stats: TodayStats
}

export interface YesterdayReviewResponse {
  date: string
  weekday: string
  unmarked_count: number
  unmarked_slots: WeeklyPlanSlotWithNext[]
}

// ============================================================================
// API Requests
// ============================================================================

export interface CompleteSlotRequest {
  status: CompletionStatus
}

export interface CompleteSlotResponse {
  id: string
  completion_status: CompletionStatus | null
  completed_at: string | null
}

export interface WeeklyPlanGenerateRequest {
  week_start_date?: string | null
}

export interface SwitchTemplateRequest {
  day_template_id: string
}

export interface SetOverrideRequest {
  reason?: string | null
}

export interface ReassignSlotRequest {
  meal_id: string
  meal_type_id?: string | null
}

export interface OverrideResponse {
  date: string
  is_override: boolean
  override_reason: string | null
}

// ============================================================================
// Meal Import
// ============================================================================

export interface MealImportWarning {
  row: number
  message: string
}

export interface MealImportError {
  row: number
  message: string
}

export interface MealImportSummary {
  total_rows: number
  created: number
  skipped: number
  warnings: number
}

export interface MealImportResult {
  success: boolean
  summary: MealImportSummary
  warnings: MealImportWarning[]
  errors: MealImportError[]
}

// ============================================================================
// Stats
// ============================================================================

export interface StatusBreakdown {
  followed: number
  adjusted: number
  skipped: number
  replaced: number
  social: number
  unmarked: number
}

export interface MealTypeAdherence {
  meal_type_id: string
  name: string
  total: number
  followed: number
  adherence_rate: string // Decimal as string from backend
}

export interface DailyAdherence {
  date: string
  total: number
  followed: number
  adherence_rate: string // Decimal as string from backend
}

export interface OverLimitBreakdown {
  template_name: string
  days_over: number
  total_days: number
  exceeded_metric: string // 'calories' | 'protein' | 'both'
}

export interface StatsResponse {
  period_days: number
  total_slots: number
  completed_slots: number
  by_status: StatusBreakdown
  adherence_rate: string // Decimal as string from backend
  current_streak: number
  best_streak: number
  override_days: number
  by_meal_type: MealTypeAdherence[]
  daily_adherence: DailyAdherence[]
  avg_daily_calories: string | null
  avg_daily_protein: string | null
  over_limit_days: number
  days_with_limits: number
  over_limit_breakdown: OverLimitBreakdown[]
}

// ============================================================================
// Pagination
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ============================================================================
// Errors
// ============================================================================

export interface ErrorDetail {
  field: string
  message: string
}

export interface ErrorBody {
  code: string
  message: string
  details?: ErrorDetail[]
}

export interface ErrorResponse {
  error: ErrorBody
}
