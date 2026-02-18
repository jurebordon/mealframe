/**
 * API client for MealFrame backend.
 *
 * All API calls are centralized here for consistency.
 * Uses fetch with proper error handling and type safety.
 */

import type {
  TodayResponse,
  YesterdayReviewResponse,
  AddAdhocSlotRequest,
  WeeklyPlanSlotWithNext,
  CompleteSlotRequest,
  CompleteSlotResponse,
  WeeklyPlanInstanceResponse,
  WeeklyPlanGenerateRequest,
  SwitchTemplateRequest,
  SetOverrideRequest,
  OverrideResponse,
  WeeklyPlanInstanceDayResponse,
  MealResponse,
  MealCreate,
  MealUpdate,
  MealListItem,
  MealImportResult,
  MealTypeResponse,
  MealTypeCreate,
  MealTypeUpdate,
  MealTypeWithCount,
  DayTemplateResponse,
  DayTemplateCreate,
  DayTemplateUpdate,
  DayTemplateListItem,
  WeekPlanResponse,
  WeekPlanCreate,
  WeekPlanUpdate,
  WeekPlanListItem,
  StatsResponse,
  PaginatedResponse,
  ErrorResponse,
} from './types'

// API base URL - configured via environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003/api/v1'

/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
  status: number
  code: string
  details?: { field: string; message: string }[]

  constructor(status: number, code: string, message: string, details?: { field: string; message: string }[]) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

/**
 * Generic fetch wrapper with error handling.
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  // Handle no-content responses
  if (response.status === 204) {
    return undefined as T
  }

  const data = await response.json()

  if (!response.ok) {
    const errorResponse = data as ErrorResponse
    throw new ApiError(
      response.status,
      errorResponse.error?.code || 'UNKNOWN_ERROR',
      errorResponse.error?.message || 'An error occurred',
      errorResponse.error?.details
    )
  }

  return data as T
}

// ============================================================================
// Today/Daily Use Endpoints
// ============================================================================

/**
 * Get today's meal plan with completion status.
 * Primary daily use endpoint.
 */
export async function getToday(): Promise<TodayResponse> {
  return fetchApi<TodayResponse>('/today')
}

/**
 * Get yesterday's plan for review/catch-up.
 */
export async function getYesterday(): Promise<TodayResponse> {
  return fetchApi<TodayResponse>('/yesterday')
}

/**
 * Mark a slot as complete with status.
 */
export async function completeSlot(
  slotId: string,
  request: CompleteSlotRequest
): Promise<CompleteSlotResponse> {
  return fetchApi<CompleteSlotResponse>(`/slots/${slotId}/complete`, {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Undo completion (reset to null).
 */
export async function uncompleteSlot(slotId: string): Promise<CompleteSlotResponse> {
  return fetchApi<CompleteSlotResponse>(`/slots/${slotId}/complete`, {
    method: 'DELETE',
  })
}

/**
 * Add an ad-hoc meal to today's plan.
 */
export async function addAdhocSlot(request: AddAdhocSlotRequest): Promise<WeeklyPlanSlotWithNext> {
  return fetchApi<WeeklyPlanSlotWithNext>('/today/slots', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Delete an ad-hoc meal slot. Only ad-hoc slots can be deleted.
 */
export async function deleteAdhocSlot(slotId: string): Promise<void> {
  return fetchApi<void>(`/slots/${slotId}`, {
    method: 'DELETE',
  })
}

// ============================================================================
// Weekly Planning Endpoints
// ============================================================================

/**
 * Get a week's plan by start date.
 * @param weekStartDate - Optional Monday of the target week. Defaults to current week.
 */
export async function getWeek(weekStartDate?: string): Promise<WeeklyPlanInstanceResponse> {
  const params = weekStartDate ? `?week_start_date=${weekStartDate}` : ''
  return fetchApi<WeeklyPlanInstanceResponse>(`/weekly-plans/current${params}`)
}

/**
 * Get the current week's plan.
 * @deprecated Use getWeek() instead
 */
export async function getCurrentWeek(): Promise<WeeklyPlanInstanceResponse> {
  return getWeek()
}

/**
 * Generate a new week's plan.
 */
export async function generateWeek(
  request?: WeeklyPlanGenerateRequest
): Promise<WeeklyPlanInstanceResponse> {
  return fetchApi<WeeklyPlanInstanceResponse>('/weekly-plans/generate', {
    method: 'POST',
    body: JSON.stringify(request || {}),
  })
}

/**
 * Switch a day's template.
 */
export async function switchDayTemplate(
  date: string,
  request: SwitchTemplateRequest
): Promise<WeeklyPlanInstanceDayResponse> {
  return fetchApi<WeeklyPlanInstanceDayResponse>(
    `/weekly-plans/current/days/${date}/template`,
    {
      method: 'PUT',
      body: JSON.stringify(request),
    }
  )
}

/**
 * Mark day as "no plan" override.
 */
export async function setDayOverride(
  date: string,
  request?: SetOverrideRequest
): Promise<OverrideResponse> {
  return fetchApi<OverrideResponse>(`/weekly-plans/current/days/${date}/override`, {
    method: 'PUT',
    body: JSON.stringify(request || {}),
  })
}

/**
 * Remove override, restore plan.
 */
export async function clearDayOverride(date: string): Promise<OverrideResponse> {
  return fetchApi<OverrideResponse>(`/weekly-plans/current/days/${date}/override`, {
    method: 'DELETE',
  })
}

// ============================================================================
// Meals Endpoints
// ============================================================================

/**
 * List all meals (paginated, with optional search and meal type filter).
 */
export async function getMeals(
  page = 1,
  pageSize = 20,
  search?: string,
  mealTypeId?: string
): Promise<PaginatedResponse<MealListItem>> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  })
  if (search) params.set('search', search)
  if (mealTypeId) params.set('meal_type_id', mealTypeId)

  return fetchApi<PaginatedResponse<MealListItem>>(`/meals?${params}`)
}

/**
 * Get a single meal by ID.
 */
export async function getMeal(id: string): Promise<MealResponse> {
  return fetchApi<MealResponse>(`/meals/${id}`)
}

/**
 * Create a new meal.
 */
export async function createMeal(request: MealCreate): Promise<MealResponse> {
  return fetchApi<MealResponse>('/meals', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Update a meal.
 */
export async function updateMeal(
  id: string,
  request: MealUpdate
): Promise<MealResponse> {
  return fetchApi<MealResponse>(`/meals/${id}`, {
    method: 'PUT',
    body: JSON.stringify(request),
  })
}

/**
 * Delete a meal.
 */
export async function deleteMeal(id: string): Promise<void> {
  return fetchApi<void>(`/meals/${id}`, {
    method: 'DELETE',
  })
}

/**
 * Import meals from a CSV file.
 * Uses multipart/form-data (not JSON).
 */
export async function importMeals(file: File): Promise<MealImportResult> {
  const url = `${API_BASE_URL}/meals/import`
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(url, {
    method: 'POST',
    body: formData,
    // Do NOT set Content-Type header — browser sets it with boundary for multipart
  })

  const data = await response.json()

  if (!response.ok) {
    const errorResponse = data as ErrorResponse
    throw new ApiError(
      response.status,
      errorResponse.error?.code || 'UNKNOWN_ERROR',
      errorResponse.error?.message || 'An error occurred',
      errorResponse.error?.details
    )
  }

  return data as MealImportResult
}

// ============================================================================
// Meal Types Endpoints
// ============================================================================

/**
 * List all meal types.
 */
export async function getMealTypes(): Promise<MealTypeWithCount[]> {
  return fetchApi<MealTypeWithCount[]>('/meal-types')
}

/**
 * Get a single meal type by ID.
 */
export async function getMealType(id: string): Promise<MealTypeResponse> {
  return fetchApi<MealTypeResponse>(`/meal-types/${id}`)
}

/**
 * Create a new meal type.
 */
export async function createMealType(
  request: MealTypeCreate
): Promise<MealTypeResponse> {
  return fetchApi<MealTypeResponse>('/meal-types', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Update a meal type.
 */
export async function updateMealType(
  id: string,
  request: MealTypeUpdate
): Promise<MealTypeResponse> {
  return fetchApi<MealTypeResponse>(`/meal-types/${id}`, {
    method: 'PUT',
    body: JSON.stringify(request),
  })
}

/**
 * Delete a meal type.
 */
export async function deleteMealType(id: string): Promise<void> {
  return fetchApi<void>(`/meal-types/${id}`, {
    method: 'DELETE',
  })
}

// ============================================================================
// Day Templates Endpoints
// ============================================================================

/**
 * List all day templates.
 */
export async function getDayTemplates(): Promise<DayTemplateListItem[]> {
  return fetchApi<DayTemplateListItem[]>('/day-templates')
}

/**
 * Get a single day template by ID.
 */
export async function getDayTemplate(id: string): Promise<DayTemplateResponse> {
  return fetchApi<DayTemplateResponse>(`/day-templates/${id}`)
}

/**
 * Create a new day template.
 */
export async function createDayTemplate(
  request: DayTemplateCreate
): Promise<DayTemplateResponse> {
  return fetchApi<DayTemplateResponse>('/day-templates', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Update a day template.
 */
export async function updateDayTemplate(
  id: string,
  request: DayTemplateUpdate
): Promise<DayTemplateResponse> {
  return fetchApi<DayTemplateResponse>(`/day-templates/${id}`, {
    method: 'PUT',
    body: JSON.stringify(request),
  })
}

/**
 * Delete a day template.
 */
export async function deleteDayTemplate(id: string): Promise<void> {
  return fetchApi<void>(`/day-templates/${id}`, {
    method: 'DELETE',
  })
}

// ============================================================================
// Week Plans Endpoints
// ============================================================================

/**
 * List all week plans.
 */
export async function getWeekPlans(): Promise<WeekPlanListItem[]> {
  return fetchApi<WeekPlanListItem[]>('/week-plans')
}

/**
 * Get a single week plan by ID.
 */
export async function getWeekPlan(id: string): Promise<WeekPlanResponse> {
  return fetchApi<WeekPlanResponse>(`/week-plans/${id}`)
}

/**
 * Create a new week plan.
 */
export async function createWeekPlan(
  request: WeekPlanCreate
): Promise<WeekPlanResponse> {
  return fetchApi<WeekPlanResponse>('/week-plans', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Update a week plan.
 */
export async function updateWeekPlan(
  id: string,
  request: WeekPlanUpdate
): Promise<WeekPlanResponse> {
  return fetchApi<WeekPlanResponse>(`/week-plans/${id}`, {
    method: 'PUT',
    body: JSON.stringify(request),
  })
}

/**
 * Delete a week plan.
 */
export async function deleteWeekPlan(id: string): Promise<void> {
  return fetchApi<void>(`/week-plans/${id}`, {
    method: 'DELETE',
  })
}

/**
 * Set a week plan as the default.
 */
export async function setDefaultWeekPlan(id: string): Promise<WeekPlanResponse> {
  return fetchApi<WeekPlanResponse>(`/week-plans/${id}/set-default`, {
    method: 'POST',
  })
}

// ============================================================================
// Stats Endpoints
// ============================================================================

/**
 * Get adherence statistics for a given period.
 */
export async function getStats(days = 30): Promise<StatsResponse> {
  return fetchApi<StatsResponse>(`/stats?days=${days}`)
}

// Convenience object for importing all API functions
export const api = {
  // Today/Daily
  getToday,
  getYesterday,
  completeSlot,
  uncompleteSlot,
  addAdhocSlot,
  deleteAdhocSlot,

  // Weekly
  getWeek,
  getCurrentWeek,
  generateWeek,
  switchDayTemplate,
  setDayOverride,
  clearDayOverride,

  // Meals
  getMeals,
  getMeal,
  createMeal,
  updateMeal,
  deleteMeal,
  importMeals,

  // Meal Types
  getMealTypes,
  getMealType,
  createMealType,
  updateMealType,
  deleteMealType,

  // Day Templates
  getDayTemplates,
  getDayTemplate,
  createDayTemplate,
  updateDayTemplate,
  deleteDayTemplate,

  // Week Plans
  getWeekPlans,
  getWeekPlan,
  createWeekPlan,
  updateWeekPlan,
  deleteWeekPlan,
  setDefaultWeekPlan,

  // Stats
  getStats,
}

export default api
