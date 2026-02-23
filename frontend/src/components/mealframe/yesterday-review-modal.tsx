'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, ChevronRight, Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { WeeklyPlanSlotWithNext, CompletionStatus } from '@/lib/types'

export type SelectableCompletionStatus = Exclude<CompletionStatus, 'pending'>

interface YesterdayReviewModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  yesterdayDate: string
  unmarkedSlots: WeeklyPlanSlotWithNext[]
  onCompleteSlot: (slotId: string, status: SelectableCompletionStatus) => void
  onDismiss: () => void
}

const statusOptions: Array<{
  status: SelectableCompletionStatus
  label: string
  shortLabel: string
  color: string
}> = [
  {
    status: 'followed',
    label: 'Followed',
    shortLabel: 'Followed',
    color: 'bg-success/10 text-success border-success/30 hover:bg-success/20',
  },
  {
    status: 'equivalent',
    label: 'Equivalent',
    shortLabel: 'Equiv.',
    color: 'bg-warning/10 text-warning border-warning/30 hover:bg-warning/20',
  },
  {
    status: 'skipped',
    label: 'Skipped',
    shortLabel: 'Skipped',
    color: 'bg-muted text-muted-foreground border-border hover:bg-muted/80',
  },
  {
    status: 'deviated',
    label: 'Deviated',
    shortLabel: 'Deviated',
    color: 'bg-destructive/10 text-destructive border-destructive/30 hover:bg-destructive/20',
  },
  {
    status: 'social',
    label: 'Social',
    shortLabel: 'Social',
    color: 'bg-primary/10 text-primary border-primary/30 hover:bg-primary/20',
  },
]

export function YesterdayReviewModal({
  open,
  onOpenChange,
  yesterdayDate,
  unmarkedSlots,
  onCompleteSlot,
  onDismiss,
}: YesterdayReviewModalProps) {
  const [expandedSlotId, setExpandedSlotId] = useState<string | null>(null)
  const [completedSlots, setCompletedSlots] = useState<Set<string>>(new Set())

  const handleSelectStatus = (slotId: string, status: SelectableCompletionStatus) => {
    onCompleteSlot(slotId, status)
    setCompletedSlots(prev => new Set(prev).add(slotId))
    setExpandedSlotId(null)
  }

  const handleDismiss = () => {
    onDismiss()
    onOpenChange(false)
  }

  // Format date for display
  const formattedDate = (() => {
    const [year, month, day] = yesterdayDate.split('-').map(Number)
    const d = new Date(year, month - 1, day)
    return d.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })
  })()

  // Filter out slots that have been completed in this session
  const remainingSlots = unmarkedSlots.filter(slot => !completedSlots.has(slot.id))

  // If all slots are completed, auto-close
  if (remainingSlots.length === 0 && open && unmarkedSlots.length > 0) {
    setTimeout(() => onOpenChange(false), 300)
  }

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
            onClick={handleDismiss}
          />

          {/* Modal */}
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed inset-x-0 bottom-0 z-50 mx-auto max-w-[480px] rounded-t-3xl border-t border-border bg-card pb-safe shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-labelledby="yesterday-review-title"
          >
            {/* Drag Handle */}
            <div className="flex justify-center pt-3 pb-2">
              <div className="h-1 w-12 rounded-full bg-muted" aria-hidden="true" />
            </div>

            {/* Header */}
            <div className="border-b border-border px-6 py-4">
              <div className="mb-1 flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-muted-foreground" />
                  <h2 id="yesterday-review-title" className="text-balance text-lg font-semibold text-foreground">
                    Yesterday&apos;s Meals
                  </h2>
                </div>
                <button
                  onClick={handleDismiss}
                  className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground active:scale-95"
                  type="button"
                  aria-label="Close yesterday review"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <p className="text-balance text-sm text-muted-foreground">
                {formattedDate} &bull; {remainingSlots.length} unmarked meal{remainingSlots.length !== 1 ? 's' : ''}
              </p>
            </div>

            {/* Slots List */}
            <div className="max-h-[60vh] overflow-y-auto px-6 py-4">
              <div className="space-y-3">
                {remainingSlots.map((slot, index) => {
                  const isExpanded = expandedSlotId === slot.id

                  return (
                    <motion.div
                      key={slot.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="rounded-xl border border-border bg-background overflow-hidden"
                    >
                      {/* Slot Header - Clickable to expand */}
                      <button
                        onClick={() => setExpandedSlotId(isExpanded ? null : slot.id)}
                        className="flex w-full items-center justify-between gap-3 p-4 text-left transition-colors hover:bg-muted/50"
                        type="button"
                        aria-expanded={isExpanded}
                      >
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-foreground truncate">
                            {slot.meal?.name ?? 'Unassigned'}
                          </p>
                          <p className="text-sm text-muted-foreground truncate">
                            {slot.meal_type?.name ?? ''}
                            {slot.meal?.portion_description && (
                              <> &bull; {slot.meal.portion_description}</>
                            )}
                          </p>
                        </div>
                        <ChevronRight
                          className={cn(
                            'h-5 w-5 text-muted-foreground transition-transform',
                            isExpanded && 'rotate-90'
                          )}
                        />
                      </button>

                      {/* Status Options - Expanded */}
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="border-t border-border"
                          >
                            <div className="p-3 flex flex-wrap gap-2">
                              {statusOptions.map((option) => (
                                <button
                                  key={option.status}
                                  onClick={() => handleSelectStatus(slot.id, option.status)}
                                  className={cn(
                                    'rounded-lg border px-3 py-2 text-sm font-medium transition-all active:scale-95',
                                    option.color
                                  )}
                                  type="button"
                                >
                                  {option.shortLabel}
                                </button>
                              ))}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  )
                })}
              </div>

              {/* No remaining slots message */}
              {remainingSlots.length === 0 && unmarkedSlots.length > 0 && (
                <div className="py-8 text-center">
                  <p className="text-lg font-medium text-foreground">All caught up!</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Yesterday&apos;s meals have been marked.
                  </p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="border-t border-border px-6 py-4">
              <Button
                variant="ghost"
                className="w-full"
                onClick={handleDismiss}
              >
                {remainingSlots.length > 0 ? 'Skip for now' : 'Done'}
              </Button>
            </div>

            {/* Safe area padding for mobile */}
            <div className="h-2" />
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
