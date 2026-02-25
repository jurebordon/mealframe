'use client'

import { useState, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Search, Plus, Upload, ChevronDown } from 'lucide-react'
import { MealEditor, type MealFormData } from '@/components/mealframe/meal-editor'
import { CSVImporter } from '@/components/mealframe/csv-importer'
import { useMeals, useCreateMeal, useUpdateMeal, useDeleteMeal } from '@/hooks/use-meals'
import { useMealTypes } from '@/hooks/use-meal-types'
import type { MealListItem } from '@/lib/types'

export default function MealsPage() {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [selectedTypeId, setSelectedTypeId] = useState<string | null>(null)
  const [showEditor, setShowEditor] = useState(false)
  const [showImporter, setShowImporter] = useState(false)
  const [editingMeal, setEditingMeal] = useState<MealFormData | undefined>()
  const [showTypeFilter, setShowTypeFilter] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setDebouncedSearch(value)
    }, 300)
  }, [])

  const { data: mealsData, isLoading, error } = useMeals({
    pageSize: 100,
    search: debouncedSearch || undefined,
    mealTypeId: selectedTypeId || undefined,
  })
  const { data: mealTypes } = useMealTypes()

  const createMealMutation = useCreateMeal()
  const updateMealMutation = useUpdateMeal()
  const deleteMealMutation = useDeleteMeal()

  const meals = mealsData?.items ?? []
  const totalCount = mealsData?.total ?? 0

  const handleAddMeal = () => {
    setEditingMeal(undefined)
    setShowEditor(true)
  }

  const handleEditMeal = (meal: MealListItem) => {
    setEditingMeal({
      id: meal.id,
      name: meal.name,
      portion_description: meal.portion_description,
      calories_kcal: meal.calories_kcal,
      protein_g: meal.protein_g ? Number(meal.protein_g) : null,
      carbs_g: meal.carbs_g ? Number(meal.carbs_g) : null,
      sugar_g: meal.sugar_g ? Number(meal.sugar_g) : null,
      fat_g: meal.fat_g ? Number(meal.fat_g) : null,
      saturated_fat_g: meal.saturated_fat_g ? Number(meal.saturated_fat_g) : null,
      fiber_g: meal.fiber_g ? Number(meal.fiber_g) : null,
      meal_type_ids: meal.meal_types.map((mt) => mt.id),
      notes: '',
    })
    setShowEditor(true)
  }

  const handleSaveMeal = (formData: MealFormData) => {
    const payload = {
      name: formData.name,
      portion_description: formData.portion_description,
      calories_kcal: formData.calories_kcal,
      protein_g: formData.protein_g,
      carbs_g: formData.carbs_g,
      sugar_g: formData.sugar_g,
      fat_g: formData.fat_g,
      saturated_fat_g: formData.saturated_fat_g,
      fiber_g: formData.fiber_g,
      notes: formData.notes || undefined,
      meal_type_ids: formData.meal_type_ids,
    }

    if (formData.id) {
      updateMealMutation.mutate({ id: formData.id, data: payload })
    } else {
      createMealMutation.mutate(payload)
    }
  }

  const handleDeleteMeal = () => {
    if (editingMeal?.id) {
      deleteMealMutation.mutate(editingMeal.id)
    }
  }

  const toggleTypeFilter = (typeId: string) => {
    setSelectedTypeId((prev) => (prev === typeId ? null : typeId))
    setShowTypeFilter(false)
  }

  const selectedTypeName = mealTypes?.find((mt) => mt.id === selectedTypeId)?.name

  return (
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto max-w-4xl px-4 py-4">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0 flex-1">
              <h1 className="text-balance text-lg font-bold text-foreground sm:text-xl md:text-2xl">
                Meals Library
              </h1>
              <p className="hidden text-sm text-muted-foreground sm:block">
                Manage your collection of meals
              </p>
            </div>
            <div className="flex shrink-0 gap-2">
              <Button variant="outline" size="sm" onClick={() => setShowImporter(true)}>
                <Upload className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">Import CSV</span>
              </Button>
              <Button size="sm" onClick={handleAddMeal}>
                <Plus className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">Add Meal</span>
              </Button>
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search meals..."
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="h-11 w-full rounded-lg border border-input bg-background pl-10 pr-4 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Filter Bar */}
          <div className="flex items-center gap-2">
            {/* Type Filter */}
            <div className="relative">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowTypeFilter(!showTypeFilter)}
                className="gap-2"
              >
                {selectedTypeName || 'Meal Type'}
                {selectedTypeId && (
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                    1
                  </span>
                )}
                <ChevronDown className="h-4 w-4" />
              </Button>
              {showTypeFilter && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowTypeFilter(false)}
                  />
                  <div className="absolute left-0 top-full z-20 mt-2 w-56 rounded-lg border border-border bg-card p-2 shadow-lg">
                    {selectedTypeId && (
                      <button
                        onClick={() => {
                          setSelectedTypeId(null)
                          setShowTypeFilter(false)
                        }}
                        className="mb-1 w-full rounded-md px-3 py-2 text-left text-sm font-medium text-muted-foreground hover:bg-muted"
                        type="button"
                      >
                        Clear filter
                      </button>
                    )}
                    {mealTypes?.map((mt) => (
                      <button
                        key={mt.id}
                        onClick={() => toggleTypeFilter(mt.id)}
                        className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm hover:bg-muted ${
                          selectedTypeId === mt.id
                            ? 'bg-muted font-semibold text-foreground'
                            : 'text-foreground'
                        }`}
                        type="button"
                      >
                        <span>{mt.name}</span>
                        <span className="text-xs text-muted-foreground">{mt.meal_count}</span>
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* Count indicator */}
            {!isLoading && (
              <span className="text-sm text-muted-foreground">
                {totalCount} {totalCount === 1 ? 'meal' : 'meals'}
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="mx-auto max-w-4xl px-4 py-6 pb-24">
        {/* Loading State */}
        {isLoading && (
          <div className="flex min-h-[300px] items-center justify-center">
            <div className="text-sm text-muted-foreground">Loading meals...</div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="flex min-h-[300px] flex-col items-center justify-center text-center">
            <p className="mb-4 text-sm text-destructive">Failed to load meals</p>
            <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
              Retry
            </Button>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && meals.length === 0 && !debouncedSearch && !selectedTypeId && (
          <div className="flex min-h-[400px] flex-col items-center justify-center text-center">
            <div className="mb-4 rounded-full bg-muted p-6">
              <Plus className="h-12 w-12 text-muted-foreground" />
            </div>
            <h2 className="mb-2 text-xl font-bold text-foreground">No meals yet</h2>
            <p className="mb-6 text-sm text-muted-foreground">
              Add your first meal or import from CSV to get started
            </p>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowImporter(true)}>
                <Upload className="mr-2 h-4 w-4" />
                Import CSV
              </Button>
              <Button onClick={handleAddMeal}>
                <Plus className="mr-2 h-4 w-4" />
                Add Meal
              </Button>
            </div>
          </div>
        )}

        {/* No Results (with active filter/search) */}
        {!isLoading && !error && meals.length === 0 && (debouncedSearch || selectedTypeId) && (
          <div className="flex min-h-[300px] flex-col items-center justify-center text-center">
            <div className="mb-4 rounded-full bg-muted p-6">
              <Search className="h-12 w-12 text-muted-foreground" />
            </div>
            <h2 className="mb-2 text-lg font-bold text-foreground">No meals found</h2>
            <p className="mb-6 text-sm text-muted-foreground">
              Try adjusting your search or filter
            </p>
            <Button
              variant="outline"
              onClick={() => {
                setSearchQuery('')
                setDebouncedSearch('')
                setSelectedTypeId(null)
              }}
            >
              Clear Filters
            </Button>
          </div>
        )}

        {/* Meal List */}
        {!isLoading && meals.length > 0 && (
          <div className="space-y-3">
            {meals.map((meal) => (
              <button
                key={meal.id}
                onClick={() => handleEditMeal(meal)}
                className="w-full text-left transition-opacity hover:opacity-80"
                type="button"
              >
                <div className="rounded-xl border border-border bg-card p-4">
                  {/* Meal Type Badges */}
                  {meal.meal_types.length > 0 && (
                    <div className="mb-2 flex flex-wrap gap-2">
                      {meal.meal_types.map((mt) => (
                        <span
                          key={mt.id}
                          className="rounded-full border border-border bg-muted px-3 py-1 text-xs font-medium text-foreground"
                        >
                          {mt.name}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Name */}
                  <h3 className="mb-2 text-balance text-base font-semibold leading-tight text-foreground sm:text-lg">
                    {meal.name}
                  </h3>

                  {/* Portion */}
                  <p className="mb-3 text-balance text-sm leading-relaxed text-muted-foreground">
                    {meal.portion_description}
                  </p>

                  {/* Macros */}
                  {(meal.calories_kcal || meal.protein_g) && (
                    <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-muted-foreground">
                      {meal.calories_kcal != null && (
                        <span className="font-semibold">{meal.calories_kcal} kcal</span>
                      )}
                      {meal.protein_g != null && <span>{Number(meal.protein_g)}g protein</span>}
                      {meal.carbs_g != null && <span>{Number(meal.carbs_g)}g carbs</span>}
                      {meal.sugar_g != null && <span>{Number(meal.sugar_g)}g sugar</span>}
                      {meal.fat_g != null && <span>{Number(meal.fat_g)}g fat</span>}
                      {meal.saturated_fat_g != null && <span>{Number(meal.saturated_fat_g)}g sat. fat</span>}
                      {meal.fiber_g != null && <span>{Number(meal.fiber_g)}g fiber</span>}
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Modals */}
      <MealEditor
        open={showEditor}
        onOpenChange={setShowEditor}
        onSave={handleSaveMeal}
        onDelete={editingMeal?.id ? handleDeleteMeal : undefined}
        initialData={editingMeal}
        mode={editingMeal?.id ? 'edit' : 'add'}
      />

      <CSVImporter
        open={showImporter}
        onOpenChange={setShowImporter}
        onImportComplete={() => {
          queryClient.invalidateQueries({ queryKey: ['meals'] })
        }}
      />
    </main>
  )
}
