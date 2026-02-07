'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { X, Trash2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useMealTypes } from '@/hooks/use-meal-types'

export interface MealFormData {
  id?: string
  name: string
  portion_description: string
  calories_kcal: number | null
  protein_g: number | null
  carbs_g: number | null
  sugar_g: number | null
  fat_g: number | null
  saturated_fat_g: number | null
  fiber_g: number | null
  meal_type_ids: string[]
  notes: string
}

const EMPTY_FORM: MealFormData = {
  name: '',
  portion_description: '',
  calories_kcal: null,
  protein_g: null,
  carbs_g: null,
  sugar_g: null,
  fat_g: null,
  saturated_fat_g: null,
  fiber_g: null,
  meal_type_ids: [],
  notes: '',
}

interface MealEditorProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave: (meal: MealFormData) => void
  onDelete?: () => void
  initialData?: MealFormData
  mode: 'add' | 'edit'
}

export function MealEditor({
  open,
  onOpenChange,
  onSave,
  onDelete,
  initialData,
  mode,
}: MealEditorProps) {
  const [formData, setFormData] = useState<MealFormData>(EMPTY_FORM)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const { data: mealTypes } = useMealTypes()

  useEffect(() => {
    if (initialData) {
      setFormData(initialData)
    } else {
      setFormData(EMPTY_FORM)
    }
    setShowDeleteConfirm(false)
  }, [initialData, open])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave(formData)
    onOpenChange(false)
  }

  const toggleMealType = (id: string) => {
    setFormData((prev) => ({
      ...prev,
      meal_type_ids: prev.meal_type_ids.includes(id)
        ? prev.meal_type_ids.filter((t) => t !== id)
        : [...prev.meal_type_ids, id],
    }))
  }

  const handleDelete = () => {
    if (onDelete) {
      onDelete()
      onOpenChange(false)
    }
  }

  const setNumericField = (field: 'calories_kcal' | 'protein_g' | 'carbs_g' | 'sugar_g' | 'fat_g' | 'saturated_fat_g' | 'fiber_g', raw: string) => {
    if (raw === '') {
      setFormData({ ...formData, [field]: null })
      return
    }
    const val = Number(raw)
    if (!isNaN(val) && val >= 0) {
      setFormData({ ...formData, [field]: val })
    }
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
            className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
            onClick={() => onOpenChange(false)}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed inset-x-4 top-4 bottom-4 z-50 mx-auto flex max-w-2xl flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-2xl sm:inset-y-8"
          >
            {/* Header - Fixed */}
            <div className="shrink-0 border-b border-border p-6 pb-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <h2 className="text-balance text-xl font-bold text-foreground sm:text-2xl">
                    {mode === 'add' ? 'Add Meal' : 'Edit Meal'}
                  </h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {mode === 'add'
                      ? 'Create a new meal for your library'
                      : 'Update meal details'}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onOpenChange(false)}
                  className="h-8 w-8 shrink-0 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Form - Scrollable */}
            <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
              <div className="flex-1 space-y-6 overflow-y-auto p-6">
                {/* Name */}
                <div>
                  <label className="mb-2 block text-sm font-semibold text-foreground">
                    Meal Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="h-11 w-full rounded-lg border border-input bg-background px-4 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="e.g., Greek Yogurt Bowl"
                    required
                  />
                </div>

                {/* Portion */}
                <div>
                  <label className="mb-2 block text-sm font-semibold text-foreground">
                    Portion Description *
                  </label>
                  <textarea
                    value={formData.portion_description}
                    onChange={(e) => setFormData({ ...formData, portion_description: e.target.value })}
                    className="min-h-[80px] w-full rounded-lg border border-input bg-background px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="e.g., 200g Greek yogurt + 30g granola + 100g mixed berries"
                    required
                  />
                  <p className="mt-1 text-xs text-muted-foreground">
                    Be specific with weights and measurements for accuracy
                  </p>
                </div>

                {/* Macros Grid */}
                <div>
                  <label className="mb-3 block text-sm font-semibold text-foreground">
                    Macros
                  </label>
                  <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                    <div>
                      <label className="mb-1 block text-xs text-muted-foreground">
                        Calories
                      </label>
                      <input
                        type="number"
                        value={formData.calories_kcal ?? ''}
                        onChange={(e) => setNumericField('calories_kcal', e.target.value)}
                        className="h-11 w-full rounded-lg border border-input bg-background px-3 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                        placeholder="—"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-muted-foreground">
                        Protein (g)
                      </label>
                      <input
                        type="number"
                        value={formData.protein_g ?? ''}
                        onChange={(e) => setNumericField('protein_g', e.target.value)}
                        className="h-11 w-full rounded-lg border border-input bg-background px-3 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                        placeholder="—"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-muted-foreground">
                        Carbs (g)
                      </label>
                      <input
                        type="number"
                        value={formData.carbs_g ?? ''}
                        onChange={(e) => setNumericField('carbs_g', e.target.value)}
                        className="h-11 w-full rounded-lg border border-input bg-background px-3 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                        placeholder="—"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-muted-foreground">
                        Sugar (g)
                      </label>
                      <input
                        type="number"
                        value={formData.sugar_g ?? ''}
                        onChange={(e) => setNumericField('sugar_g', e.target.value)}
                        className="h-11 w-full rounded-lg border border-input bg-background px-3 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                        placeholder="—"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-muted-foreground">Fat (g)</label>
                      <input
                        type="number"
                        value={formData.fat_g ?? ''}
                        onChange={(e) => setNumericField('fat_g', e.target.value)}
                        className="h-11 w-full rounded-lg border border-input bg-background px-3 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                        placeholder="—"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-muted-foreground">
                        Sat. Fat (g)
                      </label>
                      <input
                        type="number"
                        value={formData.saturated_fat_g ?? ''}
                        onChange={(e) => setNumericField('saturated_fat_g', e.target.value)}
                        className="h-11 w-full rounded-lg border border-input bg-background px-3 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                        placeholder="—"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-muted-foreground">
                        Fiber (g)
                      </label>
                      <input
                        type="number"
                        value={formData.fiber_g ?? ''}
                        onChange={(e) => setNumericField('fiber_g', e.target.value)}
                        className="h-11 w-full rounded-lg border border-input bg-background px-3 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                        placeholder="—"
                        min="0"
                      />
                    </div>
                  </div>
                </div>

                {/* Meal Types */}
                <div>
                  <label className="mb-3 block text-sm font-semibold text-foreground">
                    Meal Types
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {mealTypes?.map((mt) => (
                      <button
                        key={mt.id}
                        type="button"
                        onClick={() => toggleMealType(mt.id)}
                        className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
                          formData.meal_type_ids.includes(mt.id)
                            ? 'border-primary bg-primary text-primary-foreground'
                            : 'border-border bg-background text-foreground hover:border-primary/50'
                        }`}
                      >
                        {mt.name}
                      </button>
                    ))}
                    {!mealTypes?.length && (
                      <p className="text-sm text-muted-foreground">Loading meal types...</p>
                    )}
                  </div>
                </div>

                {/* Notes */}
                <div>
                  <label className="mb-2 block text-sm font-semibold text-foreground">
                    Notes (optional)
                  </label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="min-h-[60px] w-full rounded-lg border border-input bg-background px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="Additional notes, preferences, or substitutions"
                  />
                </div>
              </div>

              {/* Footer - Fixed */}
              <div className="shrink-0 border-t border-border p-6 pt-4">
                {showDeleteConfirm ? (
                  <div className="flex flex-col gap-3">
                    <p className="text-sm text-muted-foreground">
                      Are you sure you want to delete this meal?
                    </p>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant="destructive"
                        size="sm"
                        onClick={handleDelete}
                        className="flex-1"
                      >
                        Yes, Delete
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setShowDeleteConfirm(false)}
                        className="flex-1"
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    {mode === 'edit' && onDelete && (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setShowDeleteConfirm(true)}
                        className="shrink-0 border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground"
                        aria-label="Delete meal"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                    <div className="flex flex-1 gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => onOpenChange(false)}
                        size="sm"
                        className="flex-1"
                      >
                        Cancel
                      </Button>
                      <Button type="submit" size="sm" className="flex-1">
                        {mode === 'add' ? 'Add Meal' : 'Save'}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
