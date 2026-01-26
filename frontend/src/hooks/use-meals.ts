'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMeals, getMeal, createMeal, updateMeal, deleteMeal } from '@/lib/api'
import type { MealCreate, MealUpdate, MealListItem, MealResponse, PaginatedResponse } from '@/lib/types'

interface UseMealsParams {
  page?: number
  pageSize?: number
  search?: string
  mealTypeId?: string
}

export function useMeals({ page = 1, pageSize = 50, search, mealTypeId }: UseMealsParams = {}) {
  return useQuery<PaginatedResponse<MealListItem>>({
    queryKey: ['meals', { page, pageSize, search, mealTypeId }],
    queryFn: () => getMeals(page, pageSize, search, mealTypeId),
    staleTime: 1000 * 60 * 5, // 5 min — meals change more often than templates
  })
}

export function useMeal(id: string | null) {
  return useQuery<MealResponse>({
    queryKey: ['meal', id],
    queryFn: () => getMeal(id!),
    enabled: !!id,
  })
}

export function useCreateMeal() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: MealCreate) => createMeal(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meals'] })
    },
  })
}

export function useUpdateMeal() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: MealUpdate }) => updateMeal(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['meals'] })
      queryClient.invalidateQueries({ queryKey: ['meal', variables.id] })
    },
  })
}

export function useDeleteMeal() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteMeal(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meals'] })
    },
  })
}
