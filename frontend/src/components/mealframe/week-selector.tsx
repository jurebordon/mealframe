'use client'

import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface WeekSelectorProps {
  /** The Monday of the currently selected week */
  selectedWeekStart: Date
  /** Callback when user navigates to a different week */
  onWeekChange: (weekStart: Date) => void
  /** Number of weeks back allowed (default: 4) */
  maxWeeksBack?: number
  /** Optional class name for styling */
  className?: string
}

/**
 * Get the Monday of the week containing the given date.
 */
function getWeekStart(date: Date): Date {
  const d = new Date(date)
  const day = d.getDay()
  // Sunday = 0, so we need to go back 6 days. Monday = 1, go back 0 days, etc.
  const diff = day === 0 ? 6 : day - 1
  d.setDate(d.getDate() - diff)
  d.setHours(0, 0, 0, 0)
  return d
}

/**
 * Format a week range for display.
 * Examples: "Jan 27 - Feb 2" or "Feb 3 - 9"
 */
function formatWeekRange(weekStart: Date): string {
  const weekEnd = new Date(weekStart)
  weekEnd.setDate(weekEnd.getDate() + 6)

  const startMonth = weekStart.toLocaleDateString('en-US', { month: 'short' })
  const endMonth = weekEnd.toLocaleDateString('en-US', { month: 'short' })
  const startDay = weekStart.getDate()
  const endDay = weekEnd.getDate()

  if (startMonth === endMonth) {
    return `${startMonth} ${startDay} - ${endDay}`
  }
  return `${startMonth} ${startDay} - ${endMonth} ${endDay}`
}

/**
 * Check if two dates are the same week (same Monday).
 */
function isSameWeek(a: Date, b: Date): boolean {
  const aStart = getWeekStart(a)
  const bStart = getWeekStart(b)
  return aStart.getTime() === bStart.getTime()
}

export function WeekSelector({
  selectedWeekStart,
  onWeekChange,
  maxWeeksBack = 4,
  className = '',
}: WeekSelectorProps) {
  const today = new Date()
  const currentWeekStart = getWeekStart(today)

  // Calculate the minimum allowed week (4 weeks back from current)
  const minWeekStart = new Date(currentWeekStart)
  minWeekStart.setDate(minWeekStart.getDate() - maxWeeksBack * 7)

  // Check if we're at the boundaries
  const canGoBack = selectedWeekStart.getTime() > minWeekStart.getTime()
  const isCurrentWeek = isSameWeek(selectedWeekStart, today)

  const handlePrevWeek = () => {
    if (!canGoBack) return
    const newWeek = new Date(selectedWeekStart)
    newWeek.setDate(newWeek.getDate() - 7)
    onWeekChange(newWeek)
  }

  const handleNextWeek = () => {
    const newWeek = new Date(selectedWeekStart)
    newWeek.setDate(newWeek.getDate() + 7)
    onWeekChange(newWeek)
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Button
        variant="ghost"
        size="icon"
        onClick={handlePrevWeek}
        disabled={!canGoBack}
        aria-label="Previous week"
        className="h-8 w-8 shrink-0"
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>

      <div className="flex min-w-0 flex-1 flex-col items-center justify-center text-center">
        <span className="text-sm font-medium text-foreground">
          {formatWeekRange(selectedWeekStart)}
        </span>
        {isCurrentWeek && (
          <span className="text-xs text-primary">This Week</span>
        )}
        {!isCurrentWeek && selectedWeekStart > currentWeekStart && (
          <span className="text-xs text-muted-foreground">
            {Math.round((selectedWeekStart.getTime() - currentWeekStart.getTime()) / (7 * 24 * 60 * 60 * 1000))} week{Math.round((selectedWeekStart.getTime() - currentWeekStart.getTime()) / (7 * 24 * 60 * 60 * 1000)) !== 1 ? 's' : ''} ahead
          </span>
        )}
        {!isCurrentWeek && selectedWeekStart < currentWeekStart && (
          <span className="text-xs text-muted-foreground">
            {Math.round((currentWeekStart.getTime() - selectedWeekStart.getTime()) / (7 * 24 * 60 * 60 * 1000))} week{Math.round((currentWeekStart.getTime() - selectedWeekStart.getTime()) / (7 * 24 * 60 * 60 * 1000)) !== 1 ? 's' : ''} ago
          </span>
        )}
      </div>

      <Button
        variant="ghost"
        size="icon"
        onClick={handleNextWeek}
        aria-label="Next week"
        className="h-8 w-8 shrink-0"
      >
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  )
}

/**
 * Get the Monday of the current week.
 */
export function getCurrentWeekStart(): Date {
  return getWeekStart(new Date())
}

/**
 * Format a Date to YYYY-MM-DD string for API calls.
 */
export function formatDateForApi(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Parse a YYYY-MM-DD string to a Date.
 */
export function parseDateFromApi(dateStr: string): Date {
  const [year, month, day] = dateStr.split('-').map(Number)
  return new Date(year, month - 1, day)
}
