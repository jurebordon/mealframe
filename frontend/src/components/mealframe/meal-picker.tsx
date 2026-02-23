'use client'

import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Search, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useMeals } from '@/hooks/use-meals'
import type { MealListItem } from '@/lib/types'

interface MealPickerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSelectMeal: (meal: MealListItem) => void
  /** "add-adhoc" (default) for adding meals, "reassign" for swapping a slot's meal */
  mode?: 'add-adhoc' | 'reassign'
  /** When in reassign mode, filter meals to this meal type */
  mealTypeId?: string | null
}

export function MealPicker({ open, onOpenChange, onSelectMeal, mode = 'add-adhoc', mealTypeId }: MealPickerProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const { data, isLoading } = useMeals({ pageSize: 200, mealTypeId: mealTypeId ?? undefined })

  const meals = data?.items ?? []

  const filteredMeals = useMemo(() => {
    if (!searchQuery.trim()) return meals

    const query = searchQuery.toLowerCase()
    return meals.filter(
      (meal) =>
        meal.name.toLowerCase().includes(query) ||
        meal.portion_description.toLowerCase().includes(query) ||
        meal.meal_types.some((type) => type.name.toLowerCase().includes(query))
    )
  }, [meals, searchQuery])

  const handleSelectMeal = (meal: MealListItem) => {
    onSelectMeal(meal)
    setSearchQuery('')
    onOpenChange(false)
  }

  const title = mode === 'reassign' ? 'Change meal' : 'Add a meal'

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm"
            onClick={() => onOpenChange(false)}
          />

          {/* Sheet */}
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed inset-x-0 bottom-0 z-50 mx-auto max-w-[480px] rounded-t-3xl border-t border-border bg-card pb-safe shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-labelledby="meal-picker-title"
          >
            {/* Drag Handle */}
            <div className="flex justify-center pt-3 pb-2">
              <div className="h-1 w-12 rounded-full bg-muted" aria-hidden="true" />
            </div>

            {/* Header */}
            <div className="border-b border-border px-6 py-4">
              <div className="mb-3 flex items-start justify-between gap-3">
                <h2 id="meal-picker-title" className="text-balance text-lg font-semibold text-foreground">
                  {title}
                </h2>
                <button
                  onClick={() => onOpenChange(false)}
                  className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground active:scale-95"
                  type="button"
                  aria-label="Close meal picker"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Search Input */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search meals..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-lg border border-border bg-background py-3 pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  autoFocus
                />
              </div>
            </div>

            {/* Meal List */}
            <div className="max-h-[60vh] overflow-y-auto px-6 py-4">
              {isLoading ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  <p className="mt-3 text-sm text-muted-foreground">Loading meals...</p>
                </div>
              ) : filteredMeals.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                    <Search className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {searchQuery ? 'No meals match your search' : 'No meals available'}
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredMeals.map((meal) => (
                    <motion.button
                      key={meal.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      onClick={() => handleSelectMeal(meal)}
                      className={cn(
                        'flex min-h-[72px] w-full items-start gap-4 rounded-xl border border-border bg-background p-4 text-left transition-all hover:border-primary/50 hover:bg-muted/50 active:scale-[0.98]'
                      )}
                    >
                      <div className="flex-1 space-y-1">
                        <h3 className="text-balance text-base font-semibold leading-tight text-foreground">
                          {meal.name}
                        </h3>
                        <p className="line-clamp-1 text-sm text-muted-foreground">{meal.portion_description}</p>
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-1 text-right">
                        {meal.calories_kcal != null && (
                          <span className="text-sm font-semibold text-foreground">
                            {Number(meal.calories_kcal)} kcal
                          </span>
                        )}
                        {meal.protein_g != null && (
                          <span className="text-xs text-muted-foreground">
                            {Math.round(Number(meal.protein_g))}g protein
                          </span>
                        )}
                      </div>
                    </motion.button>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
