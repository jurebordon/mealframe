'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown, Edit2 } from 'lucide-react'
import { StatusBadge } from './status-badge'
import { motion, AnimatePresence } from 'framer-motion'

export interface Meal {
  id: string
  name: string
  time: string
  portion: string
  status: 'pending' | 'completed'
  completionType?: 'followed' | 'equivalent' | 'skipped' | 'deviated' | 'social'
  macros: {
    calories: number
    protein: number
    carbs: number
    sugar: number
    fat: number
    saturatedFat: number
    fiber: number
  }
}

interface DayCardExpandableProps {
  date: string
  weekday: string
  fullDate: string // e.g., "Monday, Jan 6"
  templateName: string
  meals: Meal[]
  isOverride?: boolean
  overrideReason?: string
  isToday?: boolean
  isPast?: boolean
  className?: string
  onEdit?: () => void
}

export function DayCardExpandable({
  date,
  weekday,
  fullDate,
  templateName,
  meals,
  isOverride = false,
  overrideReason,
  isToday = false,
  isPast = false,
  className,
  onEdit,
}: DayCardExpandableProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const completedCount = meals.filter((m) => m.status === 'completed').length
  const totalCount = meals.length
  const completionPercentage = totalCount > 0 ? (completedCount / totalCount) * 100 : 0

  return (
    <div
      className={cn(
        'rounded-xl border bg-card transition-all duration-200',
        isToday && 'border-primary/40 bg-primary/5 ring-2 ring-primary/20',
        isPast && !isToday && 'opacity-75',
        isOverride && 'opacity-60',
        className
      )}
    >
      {/* Main Card Content */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          {/* Left: Date & Status */}
          <button
            onClick={() => !isOverride && setIsExpanded(!isExpanded)}
            className="flex-1 text-left"
            type="button"
          >
            <div className="mb-3 flex items-center gap-2">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold text-foreground">{fullDate}</h3>
                  {isToday && (
                    <span className="rounded-full bg-primary px-2 py-0.5 text-xs font-medium text-primary-foreground">
                      Today
                    </span>
                  )}
                </div>
              </div>
            </div>

            {isOverride ? (
              <div className="space-y-1">
                <div className="text-sm font-medium text-muted-foreground">No Plan</div>
                {overrideReason && (
                  <div className="text-sm text-muted-foreground/80">{overrideReason}</div>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {/* Template Badge */}
                <div className="inline-flex items-center rounded-md bg-secondary px-2.5 py-1 text-sm font-medium text-secondary-foreground">
                  {templateName}
                </div>

                {/* Progress */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">
                      {completedCount}/{totalCount} completed
                    </span>
                    {!isOverride && (
                      <ChevronDown
                        className={cn(
                          'h-4 w-4 text-muted-foreground transition-transform duration-200',
                          isExpanded && 'rotate-180'
                        )}
                      />
                    )}
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${completionPercentage}%` }}
                      transition={{ duration: 0.5, ease: 'easeOut' }}
                      className="h-full rounded-full bg-primary"
                    />
                  </div>
                </div>

                {/* Daily Totals */}
                {meals.length > 0 && (
                  <div className="flex flex-wrap gap-x-2 gap-y-0.5 text-xs text-muted-foreground">
                    <span>{Math.round(meals.reduce((s, m) => s + m.macros.calories, 0))} cal</span>
                    <span>&middot;</span>
                    <span>{Math.round(meals.reduce((s, m) => s + m.macros.protein, 0))}g P</span>
                    <span>&middot;</span>
                    <span>{Math.round(meals.reduce((s, m) => s + m.macros.carbs, 0))}g C</span>
                    <span>&middot;</span>
                    <span>{Math.round(meals.reduce((s, m) => s + m.macros.fat, 0))}g F</span>
                  </div>
                )}
              </div>
            )}
          </button>

          {/* Right: Edit Button */}
          {onEdit && (
            <button
              onClick={onEdit}
              className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              type="button"
            >
              <Edit2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Expanded Meals List */}
      <AnimatePresence>
        {isExpanded && !isOverride && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="border-t border-border px-4 pb-4 pt-3">
              <div className="space-y-2">
                {meals.map((meal) => (
                  <div
                    key={meal.id}
                    className={cn(
                      'rounded-lg border border-border bg-background/50 p-3',
                      meal.status === 'completed' && 'opacity-70'
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="mb-1 flex items-center gap-2">
                          <h4
                            className={cn(
                              'text-sm font-semibold',
                              meal.status === 'completed'
                                ? 'text-muted-foreground line-through'
                                : 'text-foreground'
                            )}
                          >
                            {meal.name}
                          </h4>
                          {meal.status === 'completed' && meal.completionType && (
                            <StatusBadge status={meal.completionType} />
                          )}
                        </div>
                        <p className="mb-1 text-xs text-muted-foreground">{meal.time}</p>
                        <p className="mb-2 text-xs text-foreground/80 leading-relaxed">
                          {meal.portion}
                        </p>
                        <div className="flex flex-wrap gap-x-2 gap-y-0.5 text-xs text-muted-foreground">
                          <span>{meal.macros.calories} cal</span>
                          <span>&middot;</span>
                          <span>{meal.macros.protein}g P</span>
                          <span>&middot;</span>
                          <span>{meal.macros.carbs}g C</span>
                          {meal.macros.sugar > 0 && <><span>&middot;</span><span>{meal.macros.sugar}g sugar</span></>}
                          <span>&middot;</span>
                          <span>{meal.macros.fat}g F</span>
                          {meal.macros.saturatedFat > 0 && <><span>&middot;</span><span>{meal.macros.saturatedFat}g sat.F</span></>}
                          {meal.macros.fiber > 0 && <><span>&middot;</span><span>{meal.macros.fiber}g fiber</span></>}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
