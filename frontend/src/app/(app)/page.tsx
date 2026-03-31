'use client'

import { useState, useCallback, useRef } from 'react'
import { MealCardGesture } from '@/components/mealframe/meal-card-gesture'
import { ProgressRing } from '@/components/mealframe/progress-ring'
import { StreakBadge } from '@/components/mealframe/streak-badge'
import { CompletionSheetAnimated } from '@/components/mealframe/completion-sheet-animated'
import { CompletionAnimation } from '@/components/mealframe/completion-animation'
import { YesterdayReviewModal } from '@/components/mealframe/yesterday-review-modal'
import { MealPicker } from '@/components/mealframe/meal-picker'
import { AddMealSheet } from '@/components/mealframe/add-meal-sheet'
import { DeviatedMealSheet } from '@/components/mealframe/deviated-meal-sheet'
import { AiCaptureSheet, type AiCaptureSheetHandle } from '@/components/mealframe/ai-capture-sheet'
import { Toast } from '@/components/mealframe/toast'
import { Button } from '@/components/ui/button'
import { Loader2, RefreshCw, Calendar, Plus, ArrowLeftRight } from 'lucide-react'
import { useToday, useCompleteSlot, useUncompleteSlot, useOfflineSync, useAddAdhocSlot, useDeleteAdhocSlot, useReassignSlot } from '@/hooks/use-today'
import { useYesterdayReview, useCompleteYesterdaySlot } from '@/hooks/use-yesterday-review'
import type { CompletionStatus, WeeklyPlanSlotWithNext, MealListItem } from '@/lib/types'
import Link from 'next/link'

export default function TodayView() {
  const { data, isLoading, isError, error, refetch } = useToday()
  const completeSlotMutation = useCompleteSlot()
  const uncompleteSlotMutation = useUncompleteSlot()
  const addAdhocSlotMutation = useAddAdhocSlot()
  const deleteAdhocSlotMutation = useDeleteAdhocSlot()
  const reassignSlotMutation = useReassignSlot()
  useOfflineSync()

  // Yesterday review
  const {
    yesterdayData,
    shouldShowReview,
    dismissReview,
    unmarkedSlots: yesterdayUnmarkedSlots,
  } = useYesterdayReview()
  const completeYesterdaySlotMutation = useCompleteYesterdaySlot()
  const [showYesterdayReview, setShowYesterdayReview] = useState(true)

  const [showCompletionSheet, setShowCompletionSheet] = useState(false)
  const [selectedSlot, setSelectedSlot] = useState<WeeklyPlanSlotWithNext | null>(null)
  const [showAnimation, setShowAnimation] = useState(false)
  const [animationType, setAnimationType] = useState<CompletionStatus>('followed')
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')
  const [lastCompletedSlotId, setLastCompletedSlotId] = useState<string | null>(null)
  const [showAddMealSheet, setShowAddMealSheet] = useState(false)
  const [showMealPicker, setShowMealPicker] = useState(false)
  const [showAiCaptureSheet, setShowAiCaptureSheet] = useState(false)
  const aiCaptureRef = useRef<AiCaptureSheetHandle>(null)
  const [showReassignPicker, setShowReassignPicker] = useState(false)
  const [reassignSlot, setReassignSlot] = useState<WeeklyPlanSlotWithNext | null>(null)
  const [showDeviatedSheet, setShowDeviatedSheet] = useState(false)
  const [showDeviatedPicker, setShowDeviatedPicker] = useState(false)
  const [showDeviatedCapture, setShowDeviatedCapture] = useState(false)
  const deviatedCaptureRef = useRef<AiCaptureSheetHandle>(null)
  const [deviatedSlot, setDeviatedSlot] = useState<WeeklyPlanSlotWithNext | null>(null)

  const handleMarkComplete = useCallback((slot: WeeklyPlanSlotWithNext) => {
    setSelectedSlot(slot)
    setShowCompletionSheet(true)
  }, [])

  const completeSlotWithAnimation = useCallback((slotId: string, status: CompletionStatus, wasAlreadyCompleted: boolean, actualMealId?: string) => {
    completeSlotMutation.mutate({ slotId, status, actualMealId })

    setAnimationType(status)
    setShowAnimation(true)
    setLastCompletedSlotId(slotId)

    setTimeout(() => {
      setShowAnimation(false)
      const label = status.charAt(0).toUpperCase() + status.slice(1)
      setToastMessage(wasAlreadyCompleted ? `Changed to ${label.toLowerCase()}` : `Marked as ${label.toLowerCase()}`)
      setShowToast(true)
    }, 1000)
  }, [completeSlotMutation])

  const handleCompletionSelect = useCallback((status: Exclude<CompletionStatus, 'pending'>) => {
    if (!selectedSlot) return
    setShowCompletionSheet(false)

    // Intercept deviated: ask what user ate instead
    if (status === 'deviated') {
      setDeviatedSlot(selectedSlot)
      setShowDeviatedSheet(true)
      return
    }

    const wasAlreadyCompleted = selectedSlot.completion_status !== null
    completeSlotWithAnimation(selectedSlot.id, status, wasAlreadyCompleted)
  }, [selectedSlot, completeSlotWithAnimation])

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

  const handleClearStatus = useCallback(() => {
    if (!selectedSlot) return
    setShowCompletionSheet(false)
    uncompleteSlotMutation.mutate(selectedSlot.id)
    setToastMessage('Status cleared')
    setShowToast(true)
  }, [selectedSlot, uncompleteSlotMutation])

  const handleUndo = useCallback(() => {
    if (lastCompletedSlotId) {
      uncompleteSlotMutation.mutate(lastCompletedSlotId)
      setLastCompletedSlotId(null)
    }
  }, [lastCompletedSlotId, uncompleteSlotMutation])

  const handleSelectFromLibrary = useCallback(() => {
    setShowAddMealSheet(false)
    setShowMealPicker(true)
  }, [])

  const handleCaptureWithPhoto = useCallback(() => {
    setShowAddMealSheet(false)
    setShowAiCaptureSheet(true)
    // Trigger file picker synchronously in the same user gesture to satisfy iOS Safari
    aiCaptureRef.current?.triggerFilePicker()
  }, [])

  const handleAiMealSaved = useCallback(() => {
    setToastMessage('Meal captured and added')
    setShowToast(true)
  }, [])

  const handleAddAdhocMeal = useCallback((meal: MealListItem) => {
    addAdhocSlotMutation.mutate(meal.id, {
      onSuccess: () => {
        setToastMessage(`Added ${meal.name}`)
        setShowToast(true)
      },
    })
  }, [addAdhocSlotMutation])

  const handleRemoveAdhocSlot = useCallback(() => {
    if (!selectedSlot) return
    setShowCompletionSheet(false)
    deleteAdhocSlotMutation.mutate(selectedSlot.id, {
      onSuccess: () => {
        setToastMessage('Meal removed')
        setShowToast(true)
      },
    })
  }, [selectedSlot, deleteAdhocSlotMutation])

  const handleReassignStart = useCallback((slot: WeeklyPlanSlotWithNext) => {
    setShowCompletionSheet(false)
    setReassignSlot(slot)
    setShowReassignPicker(true)
  }, [])

  const handleReassignMeal = useCallback((meal: MealListItem) => {
    if (!reassignSlot) return
    reassignSlotMutation.mutate(
      { slotId: reassignSlot.id, mealId: meal.id },
      {
        onSuccess: () => {
          setToastMessage(`Changed to ${meal.name}`)
          setShowToast(true)
        },
      }
    )
    setReassignSlot(null)
  }, [reassignSlot, reassignSlotMutation])

  // Deviated flow handlers
  const handleDeviatedFromLibrary = useCallback(() => {
    setShowDeviatedSheet(false)
    setShowDeviatedPicker(true)
  }, [])

  const handleDeviatedCapturePhoto = useCallback(() => {
    setShowDeviatedSheet(false)
    setShowDeviatedCapture(true)
    // Trigger file picker synchronously in the same user gesture to satisfy iOS Safari
    deviatedCaptureRef.current?.triggerFilePicker()
  }, [])

  const handleDeviatedSkip = useCallback(() => {
    if (!deviatedSlot) return
    setShowDeviatedSheet(false)
    const wasAlreadyCompleted = deviatedSlot.completion_status !== null
    completeSlotWithAnimation(deviatedSlot.id, 'deviated', wasAlreadyCompleted)
    setDeviatedSlot(null)
  }, [deviatedSlot, completeSlotWithAnimation])

  const handleDeviatedMealSelected = useCallback((meal: MealListItem) => {
    if (!deviatedSlot) return
    const wasAlreadyCompleted = deviatedSlot.completion_status !== null
    completeSlotWithAnimation(deviatedSlot.id, 'deviated', wasAlreadyCompleted, meal.id)
    setToastMessage(`Deviated — ${meal.name}`)
    setDeviatedSlot(null)
  }, [deviatedSlot, completeSlotWithAnimation])

  const handleDeviatedMealCaptured = useCallback((mealId: string) => {
    if (!deviatedSlot) return
    const wasAlreadyCompleted = deviatedSlot.completion_status !== null
    completeSlotWithAnimation(deviatedSlot.id, 'deviated', wasAlreadyCompleted, mealId)
    setDeviatedSlot(null)
  }, [deviatedSlot, completeSlotWithAnimation])

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

  const macroMeals = data.slots
    .filter(slot => slot.completion_status !== 'skipped')
    .map(slot =>
      slot.completion_status === 'deviated' && slot.actual_meal
        ? slot.actual_meal
        : slot.meal
    )

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

          {/* Daily Macro Totals */}
          {hasSlots && (
            <div className="mt-4 flex flex-wrap gap-x-3 gap-y-1 text-sm text-muted-foreground">
              <span className="font-semibold">
                {macroMeals.reduce((s, meal) => s + (Number(meal?.calories_kcal) || 0), 0)} kcal
              </span>
              <span>
                {Math.round(macroMeals.reduce((s, meal) => s + (Number(meal?.protein_g) || 0), 0))}g P
              </span>
              <span>
                {Math.round(macroMeals.reduce((s, meal) => s + (Number(meal?.carbs_g) || 0), 0))}g C
              </span>
              <span>
                {Math.round(macroMeals.reduce((s, meal) => s + (Number(meal?.sugar_g) || 0), 0))}g sugar
              </span>
              <span>
                {Math.round(macroMeals.reduce((s, meal) => s + (Number(meal?.fat_g) || 0), 0))}g F
              </span>
              <span>
                {Math.round(macroMeals.reduce((s, meal) => s + (Number(meal?.saturated_fat_g) || 0), 0))}g sat.F
              </span>
              <span>
                {Math.round(macroMeals.reduce((s, meal) => s + (Number(meal?.fiber_g) || 0), 0))}g fiber
              </span>
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
              {nextSlot.is_adhoc && (
                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                  <Plus className="h-3 w-3" />
                  Added
                </span>
              )}
              {nextSlot.is_manual_override && !nextSlot.is_adhoc && (
                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                  <ArrowLeftRight className="h-3 w-3" />
                  Changed
                </span>
              )}
            </div>

            <div className="relative">
              {nextSlot.is_adhoc && (
                <div className="absolute -left-2 top-0 bottom-0 w-1 rounded-full bg-primary/40" />
              )}
              {/* Note: next slot is never deviated (it's unmarked), but keeping for completeness */}
              <MealCardGesture
                mealName={nextSlot.meal?.name ?? 'Unassigned'}
                portionDescription={nextSlot.meal?.portion_description ?? ''}
                mealType={nextSlot.meal_type?.name ?? ''}
                calories={nextSlot.meal?.calories_kcal != null ? Number(nextSlot.meal.calories_kcal) : undefined}
                protein={nextSlot.meal?.protein_g != null ? Number(nextSlot.meal.protein_g) : undefined}
                carbs={nextSlot.meal?.carbs_g != null ? Number(nextSlot.meal.carbs_g) : undefined}
                sugar={nextSlot.meal?.sugar_g != null ? Number(nextSlot.meal.sugar_g) : undefined}
                fat={nextSlot.meal?.fat_g != null ? Number(nextSlot.meal.fat_g) : undefined}
                saturatedFat={nextSlot.meal?.saturated_fat_g != null ? Number(nextSlot.meal.saturated_fat_g) : undefined}
                fiber={nextSlot.meal?.fiber_g != null ? Number(nextSlot.meal.fiber_g) : undefined}
                status="next"
                onClick={() => handleMarkComplete(nextSlot)}
                onQuickComplete={() => handleQuickComplete(nextSlot)}
                enableGestures={true}
                className="shadow-lg shadow-primary/5"
              />
            </div>

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
              {data.slots
                .filter((slot) => !slot.is_next)
                .sort((a, b) => {
                  const aCompleted = a.completion_status !== null ? 1 : 0
                  const bCompleted = b.completion_status !== null ? 1 : 0
                  if (aCompleted !== bCompleted) return aCompleted - bCompleted
                  return a.position - b.position
                })
                .map((slot) => {
                const isCompleted = slot.completion_status !== null

                return (
                  <div key={slot.id} className="relative">
                    {slot.is_adhoc && (
                      <div className="absolute -left-2 top-0 bottom-0 w-1 rounded-full bg-primary/40" />
                    )}
                    <MealCardGesture
                      mealName={slot.meal?.name ?? 'Unassigned'}
                      portionDescription={slot.meal?.portion_description ?? ''}
                      mealType={slot.meal_type?.name ?? ''}
                      calories={slot.meal?.calories_kcal != null ? Number(slot.meal.calories_kcal) : undefined}
                      protein={slot.meal?.protein_g != null ? Number(slot.meal.protein_g) : undefined}
                      carbs={slot.meal?.carbs_g != null ? Number(slot.meal.carbs_g) : undefined}
                      sugar={slot.meal?.sugar_g != null ? Number(slot.meal.sugar_g) : undefined}
                      fat={slot.meal?.fat_g != null ? Number(slot.meal.fat_g) : undefined}
                      saturatedFat={slot.meal?.saturated_fat_g != null ? Number(slot.meal.saturated_fat_g) : undefined}
                      fiber={slot.meal?.fiber_g != null ? Number(slot.meal.fiber_g) : undefined}
                      status={isCompleted ? 'completed' : 'default'}
                      completionStatus={slot.completion_status ?? undefined}
                      onClick={() => handleMarkComplete(slot)}
                      onQuickComplete={!isCompleted ? () => handleQuickComplete(slot) : undefined}
                      enableGestures={!isCompleted}
                    />
                    {slot.is_adhoc && (
                      <span className="mt-1 inline-flex items-center gap-1 text-xs text-muted-foreground">
                        <Plus className="h-3 w-3" />
                        Added
                      </span>
                    )}
                    {slot.is_manual_override && !slot.is_adhoc && (
                      <span className="mt-1 inline-flex items-center gap-1 text-xs text-muted-foreground">
                        <ArrowLeftRight className="h-3 w-3" />
                        Changed
                      </span>
                    )}
                    {slot.completion_status === 'deviated' && slot.actual_meal && (
                      <span className="mt-1 block text-xs text-muted-foreground">
                        Actually ate: {slot.actual_meal.name}
                      </span>
                    )}
                  </div>
                )
              })}
            </div>

            {/* Add Meal Button */}
            <Button
              variant="outline"
              onClick={() => setShowAddMealSheet(true)}
              className="mt-4 w-full gap-2"
            >
              <Plus className="h-4 w-4" />
              Add meal
            </Button>
          </section>
        )}
      </div>

      {/* Completion Sheet */}
      <CompletionSheetAnimated
        open={showCompletionSheet}
        onOpenChange={setShowCompletionSheet}
        onSelect={handleCompletionSelect}
        onClear={selectedSlot?.completion_status ? handleClearStatus : undefined}
        mealName={selectedSlot?.meal?.name ?? ''}
        currentStatus={selectedSlot?.completion_status}
        isAdHoc={selectedSlot?.is_adhoc}
        onRemove={selectedSlot?.is_adhoc ? handleRemoveAdhocSlot : undefined}
        onReassign={selectedSlot?.meal ? () => handleReassignStart(selectedSlot) : undefined}
      />

      {/* Add Meal Action Sheet */}
      <AddMealSheet
        open={showAddMealSheet}
        onOpenChange={setShowAddMealSheet}
        onSelectFromLibrary={handleSelectFromLibrary}
        onCaptureWithPhoto={handleCaptureWithPhoto}
      />

      {/* Meal Picker Sheet (Add Adhoc) */}
      <MealPicker
        open={showMealPicker}
        onOpenChange={setShowMealPicker}
        onSelectMeal={handleAddAdhocMeal}
      />

      {/* AI Capture Sheet */}
      <AiCaptureSheet
        ref={aiCaptureRef}
        open={showAiCaptureSheet}
        onOpenChange={setShowAiCaptureSheet}
        onMealSaved={handleAiMealSaved}
      />

      {/* Deviated Meal Sheet */}
      <DeviatedMealSheet
        open={showDeviatedSheet}
        onOpenChange={setShowDeviatedSheet}
        onSelectFromLibrary={handleDeviatedFromLibrary}
        onCaptureWithPhoto={handleDeviatedCapturePhoto}
        onSkip={handleDeviatedSkip}
      />

      {/* Meal Picker Sheet (Deviated) */}
      <MealPicker
        open={showDeviatedPicker}
        onOpenChange={setShowDeviatedPicker}
        onSelectMeal={handleDeviatedMealSelected}
      />

      {/* AI Capture Sheet (Deviated — create only, no adhoc slot) */}
      <AiCaptureSheet
        ref={deviatedCaptureRef}
        open={showDeviatedCapture}
        onOpenChange={setShowDeviatedCapture}
        onMealSaved={handleDeviatedMealCaptured}
        skipAdhocSlot
      />

      {/* Meal Picker Sheet (Reassign) */}
      <MealPicker
        open={showReassignPicker}
        onOpenChange={setShowReassignPicker}
        onSelectMeal={handleReassignMeal}
        mode="reassign"
        mealTypeId={reassignSlot?.meal_type?.id}
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

      {/* Yesterday Review Modal */}
      {yesterdayData && (
        <YesterdayReviewModal
          open={shouldShowReview && showYesterdayReview}
          onOpenChange={setShowYesterdayReview}
          yesterdayDate={yesterdayData.date}
          unmarkedSlots={yesterdayUnmarkedSlots}
          onCompleteSlot={(slotId, status) => {
            completeYesterdaySlotMutation.mutate({ slotId, status })
          }}
          onDismiss={dismissReview}
        />
      )}
    </div>
  )
}
