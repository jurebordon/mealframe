/**
 * E2E test helpers.
 *
 * Works with existing seeded data. Provides utilities for resetting state
 * and creating additional fixtures when needed.
 */

const API_BASE = process.env.E2E_API_URL || 'http://localhost:8003/api/v1'

async function api<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  })
  if (res.status === 204) return undefined as T
  const data = await res.json()
  if (!res.ok) throw new Error(`API ${res.status}: ${JSON.stringify(data)}`)
  return data as T
}

// ---------------------------------------------------------------------------
// Today / Slots
// ---------------------------------------------------------------------------

export interface TodayData {
  date: string
  weekday: string
  template: { id: string; name: string } | null
  is_override: boolean
  slots: Array<{
    id: string
    position: number
    meal_type: { id: string; name: string } | null
    meal: { id: string; name: string; portion_description: string } | null
    completion_status: string | null
    is_next: boolean
  }>
  stats: { completed: number; total: number; streak_days: number }
}

export async function getToday(): Promise<TodayData> {
  return api('/today')
}

export async function uncompleteSlot(slotId: string): Promise<void> {
  await api(`/slots/${slotId}/complete`, { method: 'DELETE' })
}

/**
 * Reset all completed slots for today back to pending (null status).
 * Returns the refreshed today data.
 */
export async function resetTodayCompletions(): Promise<TodayData> {
  const today = await getToday()
  for (const slot of today.slots) {
    if (slot.completion_status !== null) {
      await uncompleteSlot(slot.id)
    }
  }
  return getToday()
}

// ---------------------------------------------------------------------------
// Weekly Plans
// ---------------------------------------------------------------------------

export interface WeeklyPlanData {
  id: string
  week_start_date: string
  week_plan: { id: string; name: string } | null
  days: Array<{
    date: string
    weekday: string
    template: { id: string; name: string } | null
    is_override: boolean
    override_reason: string | null
    slots: Array<{
      id: string
      meal: { name: string } | null
      meal_type: { name: string } | null
      completion_status: string | null
    }>
  }>
}

export async function getCurrentWeek(): Promise<WeeklyPlanData> {
  return api('/weekly-plans/current')
}

export async function generateWeek(): Promise<WeeklyPlanData> {
  try {
    return await api('/weekly-plans/generate', {
      method: 'POST',
      body: JSON.stringify({}),
    })
  } catch (e) {
    if (e instanceof Error && e.message.includes('409')) {
      return getCurrentWeek()
    }
    throw e
  }
}

// ---------------------------------------------------------------------------
// Day Templates
// ---------------------------------------------------------------------------

export interface DayTemplateListItem {
  id: string
  name: string
  slot_count: number
}

export async function getDayTemplates(): Promise<DayTemplateListItem[]> {
  return api('/day-templates')
}

export async function createDayTemplate(
  name: string,
  slots: { meal_type_id: string; position: number }[]
): Promise<{ id: string; name: string }> {
  return api('/day-templates', {
    method: 'POST',
    body: JSON.stringify({ name, slots }),
  })
}

// ---------------------------------------------------------------------------
// Meal Types & Meals (for creating additional fixtures)
// ---------------------------------------------------------------------------

export async function createMealType(name: string): Promise<{ id: string; name: string }> {
  return api('/meal-types', {
    method: 'POST',
    body: JSON.stringify({ name, display_order: 0 }),
  })
}

export async function createMeal(
  name: string,
  portionDescription: string,
  mealTypeIds: string[]
): Promise<{ id: string; name: string }> {
  return api('/meals', {
    method: 'POST',
    body: JSON.stringify({
      name,
      portion_description: portionDescription,
      meal_type_ids: mealTypeIds,
    }),
  })
}

// ---------------------------------------------------------------------------
// Ensure a week plan exists (idempotent)
// ---------------------------------------------------------------------------

/**
 * Ensure a weekly plan exists for the current week.
 * If one already exists, returns it. Otherwise generates a new one.
 */
export async function ensureWeeklyPlan(): Promise<WeeklyPlanData> {
  return generateWeek()
}
