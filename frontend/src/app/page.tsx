'use client'

import { useState, useCallback } from 'react'
import { MealCardGesture } from '@/components/mealframe/meal-card-gesture'
import { ProgressRing } from '@/components/mealframe/progress-ring'
import { StreakBadge } from '@/components/mealframe/streak-badge'
import { CompletionSheetAnimated } from '@/components/mealframe/completion-sheet-animated'
import { CompletionAnimation } from '@/components/mealframe/completion-animation'
import { Toast } from '@/components/mealframe/toast'
import { Button } from '@/components/ui/button'
import { Loader2, RefreshCw, Calendar } from 'lucide-react'
import { useToday, useCompleteSlot, useUncompleteSlot, useOfflineSync } from '@/hooks/use-today'
import type { CompletionStatus, WeeklyPlanSlotWithNext } from '@/lib/types'
import Link from 'next/link'

export default function TodayView() {
  const { data, isLoading, isError, error, refetch } = useToday()
  const completeSlotMutation = useCompleteSlot()
  const uncompleteSlotMutation = useUncompleteSlot()
  useOfflineSync()

  const [showCompletionSheet, setShowCompletionSheet] = useState(false)
  const [selectedSlot, setSelectedSlot] = useState<WeeklyPlanSlotWithNext | null>(null)
  const [showAnimation, setShowAnimation] = useState(false)
  const [animationType, setAnimationType] = useState<CompletionStatus>('followed')
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')
  const [lastCompletedSlotId, setLastCompletedSlotId] = useState<string | null>(null)

  const handleMarkComplete = useCallback((slot: WeeklyPlanSlotWithNext) => {
    setSelectedSlot(slot)
    setShowCompletionSheet(true)
  }, [])

  const handleCompletionSelect = useCallback((status: Exclude<CompletionStatus, 'pending'>) => {
    if (!selectedSlot) return
    const wasAlreadyCompleted = selectedSlot.completion_status !== null
    setShowCompletionSheet(false)

    completeSlotMutation.mutate({ slotId: selectedSlot.id, status })

    setAnimationType(status)
    setShowAnimation(true)
    setLastCompletedSlotId(selectedSlot.id)

    setTimeout(() => {
      setShowAnimation(false)
      const label = status.charAt(0).toUpperCase() + status.slice(1)
      setToastMessage(wasAlreadyCompleted ? `Changed to ${label.toLowerCase()}` : `Marked as ${label.toLowerCase()}`)
      setShowToast(true)
    }, 1000)
  }, [selectedSlot, completeSlotMutation])

  const handleQuickComplete = useCallback((slot: WeeklyPlanSlotWithNext) => {
    completeSlotMutation.mutate({ slotId: slot.id, status: 'followed' })

    setAnimationType('followed')
    setShowAnimation(true)
    setLastCompletedSlotId(slot.id)

    setTimeout(() => {
      setShowAnimation(false)
      setToastMessage('Marked as followed')
      setShowToast(true)
    }, 1000)
  }, [completeSlotMutation])

  const handleUndo = useCallback(() => {
    if (lastCompletedSlotId) {
      uncompleteSlotMutation.mutate(lastCompletedSlotId)
      setLastCompletedSlotId(null)
    }
  }, [lastCompletedSlotId, uncompleteSlotMutation])

  // Loading state
  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading today&apos;s plan...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (isError) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-4">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
            <span className="text-2xl">!</span>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Couldn&apos;t load your plan</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {error instanceof Error ? error.message : 'Something went wrong'}
            </p>
          </div>
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Try again
          </Button>
        </div>
      </div>
    )
  }

  if (!data) return null

  const nextSlot = data.slots.find((s) => s.is_next) ?? null
  const hasSlots = data.slots.length > 0
  const allComplete = hasSlots && !nextSlot

  // Format date for display
  const dateStr = (() => {
    const [year, month, day] = data.date.split('-').map(Number)
    const d = new Date(year, month - 1, day)
    return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
  })()

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-[480px] px-4 pb-24 pt-6">
        {/* Header */}
        <header className="mb-6">
          <div className="mb-4">
            <h1 className="text-balance text-xl font-semibold text-foreground sm:text-2xl">
              {dateStr}
            </h1>
            {data.template && (
              <p className="mt-1 text-sm text-muted-foreground">{data.template.name}</p>
            )}
          </div>

          {/* Stats Row */}
          {hasSlots && (
            <div className="flex items-center gap-4">
              <ProgressRing
                value={data.stats.completed}
                max={data.stats.total}
                size={80}
              />
              {data.stats.streak_days > 0 && (
                <StreakBadge days={data.stats.streak_days} />
              )}
            </div>
          )}
        </header>

        {/* Empty State - No Plan */}
        {!hasSlots && !data.is_override && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
              <Calendar className="h-8 w-8 text-muted-foreground" />
            </div>
            <h2 className="mb-2 text-xl font-semibold text-foreground">No plan for today</h2>
            <p className="mb-6 max-w-xs text-balance text-sm text-muted-foreground">
              Generate a weekly plan to get started with your meals.
            </p>
            <Link href="/week">
              <Button variant="outline" size="lg">
                View Week Plan
              </Button>
            </Link>
          </div>
        )}

        {/* Empty State - Override (No Plan day) */}
        {!hasSlots && data.is_override && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
              <Calendar className="h-8 w-8 text-muted-foreground" />
            </div>
            <h2 className="mb-2 text-xl font-semibold text-foreground">No plan for today</h2>
            <p className="mb-6 max-w-xs text-balance text-sm text-muted-foreground">
              {data.override_reason
                ? data.override_reason
                : "You've overridden the template for today."}
            </p>
            <Link href="/week">
              <Button variant="outline" size="lg">
                View Week Plan
              </Button>
            </Link>
          </div>
        )}

        {/* Next Meal - Hero Card */}
        {nextSlot && (
          <section className="mb-8">
            <div className="mb-3 flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                Next
              </span>
              {nextSlot.meal_type && (
                <span className="text-xs text-muted-foreground">{nextSlot.meal_type.name}</span>
              )}
            </div>

            <MealCardGesture
              mealName={nextSlot.meal?.name ?? 'Unassigned'}
              portionDescription={nextSlot.meal?.portion_description ?? ''}
              mealType={nextSlot.meal_type?.name ?? ''}
              calories={nextSlot.meal?.calories_kcal ?? undefined}
              protein={nextSlot.meal?.protein_g ?? undefined}
              carbs={nextSlot.meal?.carbs_g ?? undefined}
              fat={nextSlot.meal?.fat_g ?? undefined}
              status="next"
              onClick={() => handleMarkComplete(nextSlot)}
              onQuickComplete={() => handleQuickComplete(nextSlot)}
              enableGestures={true}
              className="shadow-lg shadow-primary/5"
            />

            <p className="mt-3 text-center text-xs text-muted-foreground">
              Tap to choose status &bull; Long-press or swipe to mark followed
            </p>
          </section>
        )}

        {/* All Day Complete */}
        {allComplete && (
          <section className="mb-8">
            <div className="rounded-2xl border border-success/20 bg-success/10 p-6 text-center">
              <div className="mb-2 text-4xl">&#10003;</div>
              <h2 className="mb-1 text-xl font-semibold text-foreground">Day Complete</h2>
              <p className="text-sm text-muted-foreground">
                All meals completed. Great work today!
              </p>
            </div>
          </section>
        )}

        {/* Remaining Meals */}
        {hasSlots && (
          <section>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              {nextSlot ? 'Remaining Today' : "Today's Meals"}
            </h3>

            <div className="space-y-3">
              {data.slots.map((slot) => {
                if (slot.is_next) return null

                const isCompleted = slot.completion_status !== null

                return (
                  <MealCardGesture
                    key={slot.id}
                    mealName={slot.meal?.name ?? 'Unassigned'}
                    portionDescription={slot.meal?.portion_description ?? ''}
                    mealType={slot.meal_type?.name ?? ''}
                    calories={slot.meal?.calories_kcal ?? undefined}
                    protein={slot.meal?.protein_g ?? undefined}
                    carbs={slot.meal?.carbs_g ?? undefined}
                    fat={slot.meal?.fat_g ?? undefined}
                    status={isCompleted ? 'completed' : 'default'}
                    completionStatus={slot.completion_status ?? undefined}
                    onClick={() => handleMarkComplete(slot)}
                    onQuickComplete={!isCompleted ? () => handleQuickComplete(slot) : undefined}
                    enableGestures={!isCompleted}
                  />
                )
              })}
            </div>
          </section>
        )}

        {/* Pull to Refresh Hint */}
        {hasSlots && (
          <div className="mt-8 flex items-center justify-center gap-2 text-xs text-muted-foreground">
            <RefreshCw className="h-3 w-3" />
            <span>Pull down to refresh</span>
          </div>
        )}
      </div>

      {/* Completion Sheet */}
      <CompletionSheetAnimated
        open={showCompletionSheet}
        onOpenChange={setShowCompletionSheet}
        onSelect={handleCompletionSelect}
        mealName={selectedSlot?.meal?.name ?? ''}
        currentStatus={selectedSlot?.completion_status}
      />

      {/* Completion Animation */}
      <CompletionAnimation show={showAnimation} type={animationType} />

      {/* Toast with Undo */}
      <Toast
        open={showToast}
        message={toastMessage}
        onAction={handleUndo}
        onClose={() => setShowToast(false)}
        duration={3000}
      />
    </div>
  )
}
