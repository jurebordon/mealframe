'use client'

import { useQuery } from '@tanstack/react-query'
import { getMealTypes } from '@/lib/api'
import type { MealTypeWithCount } from '@/lib/types'

export function useMealTypes() {
  return useQuery<MealTypeWithCount[]>({
    queryKey: ['mealTypes'],
    queryFn: getMealTypes,
    staleTime: 1000 * 60 * 30, // Meal types change infrequently
  })
}
