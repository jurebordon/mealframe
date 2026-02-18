'use client'

import { useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getToday, completeSlot, uncompleteSlot, addAdhocSlot, deleteAdhocSlot } from '@/lib/api'
import { enqueueComplete, enqueueUncomplete, flushQueue } from '@/lib/offline-queue'
import { useOnlineStatus } from '@/hooks/use-online-status'
import type { TodayResponse, CompletionStatus } from '@/lib/types'

export function useToday() {
  return useQuery<TodayResponse>({
    queryKey: ['today'],
    queryFn: getToday,
    staleTime: 1000 * 60 * 5,
  })
}

/**
 * Hook that flushes the offline queue when connectivity is restored.
 * Should be used once at the top level of the Today View.
 */
export function useOfflineSync() {
  const isOnline = useOnlineStatus()
  const queryClient = useQueryClient()

  useEffect(() => {
    if (isOnline) {
      flushQueue().then((synced) => {
        if (synced > 0) {
          // Refetch today data to get server-authoritative state
          queryClient.invalidateQueries({ queryKey: ['today'] })
        }
      })
    }
  }, [isOnline, queryClient])
}

export function useCompleteSlot() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ slotId, status }: { slotId: string; status: CompletionStatus }) =>
      completeSlot(slotId, { status }),
    // Allow mutation to fire even when offline (for optimistic update)
    networkMode: 'always',
    onMutate: async ({ slotId, status }) => {
      await queryClient.cancelQueries({ queryKey: ['today'] })

      const previous = queryClient.getQueryData<TodayResponse>(['today'])

      if (previous) {
        const updatedSlots = previous.slots.map((slot) => {
          if (slot.id === slotId) {
            return {
              ...slot,
              completion_status: status,
              completed_at: new Date().toISOString(),
              is_next: false,
            }
          }
          return slot
        })

        // Recompute is_next: first slot with null completion_status
        const nextSlotIndex = updatedSlots.findIndex((s) => s.completion_status === null)
        const finalSlots = updatedSlots.map((slot, i) => ({
          ...slot,
          is_next: i === nextSlotIndex,
        }))

        const completed = finalSlots.filter((s) => s.completion_status !== null).length

        queryClient.setQueryData<TodayResponse>(['today'], {
          ...previous,
          slots: finalSlots,
          stats: {
            ...previous.stats,
            completed,
          },
        })
      }

      return { previous }
    },
    onError: (_err, { slotId, status }, context) => {
      // Network failure: enqueue for later sync, keep optimistic update
      if (!navigator.onLine) {
        enqueueComplete(slotId, status)
        return
      }
      // Server error while online: rollback
      if (context?.previous) {
        queryClient.setQueryData(['today'], context.previous)
      }
    },
    onSettled: () => {
      // Only refetch if online
      if (navigator.onLine) {
        queryClient.invalidateQueries({ queryKey: ['today'] })
      }
    },
  })
}

export function useUncompleteSlot() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (slotId: string) => uncompleteSlot(slotId),
    networkMode: 'always',
    onMutate: async (slotId) => {
      await queryClient.cancelQueries({ queryKey: ['today'] })

      const previous = queryClient.getQueryData<TodayResponse>(['today'])

      if (previous) {
        const updatedSlots = previous.slots.map((slot) => {
          if (slot.id === slotId) {
            return {
              ...slot,
              completion_status: null,
              completed_at: null,
              is_next: false,
            }
          }
          return slot
        })

        // Recompute is_next
        const nextSlotIndex = updatedSlots.findIndex((s) => s.completion_status === null)
        const finalSlots = updatedSlots.map((slot, i) => ({
          ...slot,
          is_next: i === nextSlotIndex,
        }))

        const completed = finalSlots.filter((s) => s.completion_status !== null).length

        queryClient.setQueryData<TodayResponse>(['today'], {
          ...previous,
          slots: finalSlots,
          stats: {
            ...previous.stats,
            completed,
          },
        })
      }

      return { previous }
    },
    onError: (_err, slotId, context) => {
      if (!navigator.onLine) {
        enqueueUncomplete(slotId)
        return
      }
      if (context?.previous) {
        queryClient.setQueryData(['today'], context.previous)
      }
    },
    onSettled: () => {
      if (navigator.onLine) {
        queryClient.invalidateQueries({ queryKey: ['today'] })
      }
    },
  })
}

export function useAddAdhocSlot() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (mealId: string) => addAdhocSlot({ meal_id: mealId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['today'] })
    },
  })
}

export function useDeleteAdhocSlot() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (slotId: string) => deleteAdhocSlot(slotId),
    onMutate: async (slotId) => {
      await queryClient.cancelQueries({ queryKey: ['today'] })

      const previous = queryClient.getQueryData<TodayResponse>(['today'])

      if (previous) {
        const updatedSlots = previous.slots.filter((slot) => slot.id !== slotId)

        // Recompute is_next
        const nextSlotIndex = updatedSlots.findIndex((s) => s.completion_status === null)
        const finalSlots = updatedSlots.map((slot, i) => ({
          ...slot,
          is_next: i === nextSlotIndex,
        }))

        const completed = finalSlots.filter((s) => s.completion_status !== null).length

        queryClient.setQueryData<TodayResponse>(['today'], {
          ...previous,
          slots: finalSlots,
          stats: {
            ...previous.stats,
            completed,
            total: finalSlots.length,
          },
        })
      }

      return { previous }
    },
    onError: (_err, _slotId, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['today'], context.previous)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['today'] })
    },
  })
}
