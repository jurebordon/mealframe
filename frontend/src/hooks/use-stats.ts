'use client'

import { useQuery } from '@tanstack/react-query'
import { getStats } from '@/lib/api'
import type { StatsResponse } from '@/lib/types'

export function useStats(days: number = 30) {
  return useQuery<StatsResponse>({
    queryKey: ['stats', days],
    queryFn: () => getStats(days),
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}
