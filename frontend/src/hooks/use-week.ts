'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getWeek,
  getCurrentWeek,
  generateWeek,
  switchDayTemplate,
  setDayOverride,
  clearDayOverride,
} from '@/lib/api'
import type {
  WeeklyPlanInstanceResponse,
  WeeklyPlanGenerateRequest,
} from '@/lib/types'

/**
 * Hook to fetch a specific week's plan by start date.
 * @param weekStartDate - The Monday of the week to fetch (YYYY-MM-DD format)
 */
export function useWeek(weekStartDate?: string) {
  return useQuery<WeeklyPlanInstanceResponse>({
    queryKey: ['week', weekStartDate],
    queryFn: () => getWeek(weekStartDate),
    staleTime: 1000 * 60 * 5,
    retry: (failureCount, error) => {
      // Don't retry on 404 (no plan exists)
      if (error && 'status' in error && (error as { status: number }).status === 404) {
        return false
      }
      return failureCount < 3
    },
  })
}

/**
 * Hook to fetch the current week's plan.
 * @deprecated Use useWeek() instead for more flexibility
 */
export function useCurrentWeek() {
  return useQuery<WeeklyPlanInstanceResponse>({
    queryKey: ['week', undefined],
    queryFn: getCurrentWeek,
    staleTime: 1000 * 60 * 5,
    retry: (failureCount, error) => {
      // Don't retry on 404 (no plan exists)
      if (error && 'status' in error && (error as { status: number }).status === 404) {
        return false
      }
      return failureCount < 3
    },
  })
}

export function useGenerateWeek() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request?: WeeklyPlanGenerateRequest) => generateWeek(request),
    onSuccess: (_data, variables) => {
      // Invalidate the specific week that was generated
      queryClient.invalidateQueries({ queryKey: ['week', variables?.week_start_date] })
      // Also invalidate "current week" query if no specific date was provided
      if (!variables?.week_start_date) {
        queryClient.invalidateQueries({ queryKey: ['week', undefined] })
      }
      queryClient.invalidateQueries({ queryKey: ['today'] })
    },
  })
}

export function useSwitchTemplate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ date, templateId }: { date: string; templateId: string }) =>
      switchDayTemplate(date, { day_template_id: templateId }),
    onSuccess: () => {
      // Invalidate all week queries since we don't know which week was affected
      queryClient.invalidateQueries({ queryKey: ['week'] })
      queryClient.invalidateQueries({ queryKey: ['today'] })
    },
  })
}

export function useSetOverride() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ date, reason }: { date: string; reason?: string }) =>
      setDayOverride(date, reason ? { reason } : undefined),
    onSuccess: () => {
      // Invalidate all week queries since we don't know which week was affected
      queryClient.invalidateQueries({ queryKey: ['week'] })
      queryClient.invalidateQueries({ queryKey: ['today'] })
    },
  })
}

export function useClearOverride() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (date: string) => clearDayOverride(date),
    onSuccess: () => {
      // Invalidate all week queries since we don't know which week was affected
      queryClient.invalidateQueries({ queryKey: ['week'] })
      queryClient.invalidateQueries({ queryKey: ['today'] })
    },
  })
}
