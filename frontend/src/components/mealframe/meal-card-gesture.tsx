'use client'

import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import type React from 'react'
import { useState, useRef, useEffect } from 'react'

// Module-level guard: prevents swipe from cascading to the next card
// when React re-renders a new card under the same finger
let lastCompletionTime = 0
const COMPLETION_COOLDOWN = 400 // ms

export type MealCardStatus = 'default' | 'next' | 'completed' | 'skipped'

interface MealCardGestureProps {
  mealName: string
  portionDescription: string
  mealType: string
  calories?: number
  protein?: number
  carbs?: number
  sugar?: number
  fat?: number
  saturatedFat?: number
  fiber?: number
  status?: MealCardStatus
  completionStatus?: 'followed' | 'equivalent' | 'skipped' | 'deviated' | 'social'
  className?: string
  onClick?: () => void
  onQuickComplete?: () => void
  enableGestures?: boolean
}

export function MealCardGesture({
  mealName,
  portionDescription,
  mealType,
  calories,
  protein,
  carbs,
  sugar,
  fat,
  saturatedFat,
  fiber,
  status = 'default',
  completionStatus,
  className,
  onClick,
  onQuickComplete,
  enableGestures = true,
}: MealCardGestureProps) {
  const [longPressProgress, setLongPressProgress] = useState(0)
  const [swipeProgress, setSwipeProgress] = useState(0)
  const [showQuickCompleteHint, setShowQuickCompleteHint] = useState(false)
  const longPressTimerRef = useRef<NodeJS.Timeout | null>(null)
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const touchStartRef = useRef<{ x: number; y: number; time: number } | null>(null)

  const LONG_PRESS_DURATION = 600 // ms
  const SWIPE_THRESHOLD = 140 // px (increased from 100 to reduce accidental completions while scrolling)

  const statusStyles = {
    default: 'bg-card border-border',
    next: 'bg-card border-primary shadow-lg ring-2 ring-primary/20',
    completed: 'bg-card border-border opacity-60',
    skipped: 'bg-card border-border opacity-40',
  }

  const handleTouchStart = (e: React.TouchEvent) => {
    if (!enableGestures || status === 'completed' || !onQuickComplete) return
    if (Date.now() - lastCompletionTime < COMPLETION_COOLDOWN) return

    const touch = e.touches[0]
    touchStartRef.current = { x: touch.clientX, y: touch.clientY, time: Date.now() }

    // Start long press timer and progress animation
    longPressTimerRef.current = setTimeout(() => {
      triggerQuickComplete()
    }, LONG_PRESS_DURATION)

    // Animate progress
    let progress = 0
    progressIntervalRef.current = setInterval(() => {
      progress += (16 / LONG_PRESS_DURATION) * 100
      setLongPressProgress(Math.min(progress, 100))
    }, 16)

    setShowQuickCompleteHint(true)
  }

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!enableGestures || !touchStartRef.current || !onQuickComplete) return

    const touch = e.touches[0]
    const deltaX = touch.clientX - touchStartRef.current.x
    const deltaY = Math.abs(touch.clientY - touchStartRef.current.y)

    // If vertical movement is too much, cancel
    if (deltaY > 30) {
      cancelGesture()
      return
    }

    // Right swipe detection
    if (deltaX > 0) {
      const progress = Math.min((deltaX / SWIPE_THRESHOLD) * 100, 100)
      setSwipeProgress(progress)

      if (deltaX >= SWIPE_THRESHOLD) {
        triggerQuickComplete()
      }
    } else {
      cancelGesture()
    }
  }

  const handleTouchEnd = () => {
    if (swipeProgress < 100 && longPressProgress < 100) {
      cancelGesture()
    }
  }

  const handleMouseDown = () => {
    if (!enableGestures || status === 'completed' || !onQuickComplete) return

    // Desktop long-press
    longPressTimerRef.current = setTimeout(() => {
      triggerQuickComplete()
    }, LONG_PRESS_DURATION)

    let progress = 0
    progressIntervalRef.current = setInterval(() => {
      progress += (16 / LONG_PRESS_DURATION) * 100
      setLongPressProgress(Math.min(progress, 100))
    }, 16)

    setShowQuickCompleteHint(true)
  }

  const handleMouseUp = () => {
    if (longPressProgress < 100) {
      cancelGesture()
    }
  }

  const triggerQuickComplete = () => {
    cancelGesture()
    lastCompletionTime = Date.now()
    if (onQuickComplete) {
      onQuickComplete()
    }
  }

  const cancelGesture = () => {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current)
      longPressTimerRef.current = null
    }
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current)
      progressIntervalRef.current = null
    }
    touchStartRef.current = null
    setLongPressProgress(0)
    setSwipeProgress(0)
    setShowQuickCompleteHint(false)
  }

  useEffect(() => {
    return () => {
      cancelGesture()
    }
  }, [])

  const isGestureActive = longPressProgress > 0 || swipeProgress > 0
  const gestureProgress = Math.max(longPressProgress, swipeProgress)

  return (
    <div
      className={cn(
        'relative rounded-lg border p-6 transition-all duration-200',
        statusStyles[status],
        onClick && 'cursor-pointer hover:shadow-md',
        isGestureActive && 'scale-[0.98] shadow-xl ring-2 ring-success/50',
        className
      )}
      style={{
        transform: `translateX(${swipeProgress > 0 ? (swipeProgress / 100) * 20 : 0}px)`,
      }}
      onClick={onClick}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Quick Complete Progress Indicator */}
      {isGestureActive && (
        <>
          {/* Progress Bar */}
          <div className="absolute left-0 top-0 h-1 w-full overflow-hidden rounded-t-lg bg-success/20">
            <div
              className="h-full bg-success transition-all duration-100"
              style={{ width: `${gestureProgress}%` }}
            />
          </div>

          {/* Checkmark Icon */}
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            <div
              className="flex h-12 w-12 items-center justify-center rounded-full bg-success text-success-foreground shadow-lg transition-all duration-100"
              style={{
                opacity: gestureProgress / 100,
                transform: `scale(${gestureProgress / 100})`,
              }}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 16 16"
                fill="currentColor"
                className="h-6 w-6"
              >
                <path
                  fillRule="evenodd"
                  d="M12.416 3.376a.75.75 0 0 1 .208 1.04l-5 7.5a.75.75 0 0 1-1.154.114l-3-3a.75.75 0 0 1 1.06-1.06l2.353 2.353 4.493-6.74a.75.75 0 0 1 1.04-.207Z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
          </div>
        </>
      )}

      {/* Hint Text */}
      {showQuickCompleteHint && !completionStatus && (
        <div className="absolute left-4 top-4 text-xs font-medium text-success">
          Hold or swipe to complete
        </div>
      )}

      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-3">
          {/* Meal Type Badge */}
          <Badge variant="outline" className="text-xs font-normal text-muted-foreground">
            {mealType}
          </Badge>

          {/* Meal Name */}
          <h3 className="text-balance text-xl font-semibold leading-tight text-card-foreground">
            {mealName}
          </h3>

          {/* Portion Description */}
          <p className="text-pretty text-base leading-relaxed text-foreground/90">
            {portionDescription}
          </p>

          {/* Macros Row */}
          {(calories || protein || carbs || fat) && (
            <div className="flex flex-wrap gap-x-4 gap-y-1 pt-2 text-sm text-muted-foreground">
              {calories != null && <span>{calories} kcal</span>}
              {protein != null && <span>{protein}g protein</span>}
              {carbs != null && <span>{carbs}g carbs</span>}
              {sugar != null && <span>{sugar}g sugar</span>}
              {fat != null && <span>{fat}g fat</span>}
              {saturatedFat != null && <span>{saturatedFat}g sat. fat</span>}
              {fiber != null && <span>{fiber}g fiber</span>}
            </div>
          )}
        </div>

        {/* Completion Status Indicator */}
        {completionStatus && !isGestureActive && (
          <div className="flex-shrink-0">
            {completionStatus === 'followed' && (
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-success text-success-foreground">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  className="h-4 w-4"
                >
                  <path
                    fillRule="evenodd"
                    d="M12.416 3.376a.75.75 0 0 1 .208 1.04l-5 7.5a.75.75 0 0 1-1.154.114l-3-3a.75.75 0 0 1 1.06-1.06l2.353 2.353 4.493-6.74a.75.75 0 0 1 1.04-.207Z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            )}
            {completionStatus === 'equivalent' && (
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-warning text-warning-foreground">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  className="h-4 w-4"
                >
                  <path d="M8.75 3.75a.75.75 0 0 0-1.5 0v3.5h-3.5a.75.75 0 0 0 0 1.5h3.5v3.5a.75.75 0 0 0 1.5 0v-3.5h3.5a.75.75 0 0 0 0-1.5h-3.5v-3.5Z" />
                </svg>
              </div>
            )}
            {(completionStatus === 'skipped' || completionStatus === 'deviated') && (
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-muted text-muted-foreground">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  className="h-4 w-4"
                >
                  <path d="M5.28 4.22a.75.75 0 0 0-1.06 1.06L6.94 8l-2.72 2.72a.75.75 0 1 0 1.06 1.06L8 9.06l2.72 2.72a.75.75 0 1 0 1.06-1.06L9.06 8l2.72-2.72a.75.75 0 0 0-1.06-1.06L8 6.94 5.28 4.22Z" />
                </svg>
              </div>
            )}
            {completionStatus === 'social' && (
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  className="h-3.5 w-3.5"
                >
                  <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM12.5 16h.5a2 2 0 0 0 2-2v-.5a2.5 2.5 0 0 0-2.5-2.5h-3v5ZM3.5 11A2.5 2.5 0 0 0 1 13.5v.5a2 2 0 0 0 2 2h.5v-5h-3Z" />
                </svg>
              </div>
            )}
          </div>
        )}
      </div>

      {status === 'next' && !isGestureActive && (
        <div className="mt-4 flex items-center gap-2 text-sm font-medium text-primary">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 16 16"
            fill="currentColor"
            className="h-4 w-4"
          >
            <path
              fillRule="evenodd"
              d="M8 14A6 6 0 1 0 8 2a6 6 0 0 0 0 12Zm.75-8.25a.75.75 0 0 0-1.5 0V8c0 .414.336.75.75.75h2a.75.75 0 0 0 0-1.5h-1.25V5.75Z"
              clipRule="evenodd"
            />
          </svg>
          <span>Next meal</span>
        </div>
      )}
    </div>
  )
}
