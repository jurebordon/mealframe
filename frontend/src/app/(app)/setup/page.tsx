'use client'

/**
 * Setup page — manage Meal Types, Day Templates, and Week Plans.
 *
 * Desktop-oriented setup workflow (per PRD) with three tabs:
 * 1. Meal Types - functional eating slots
 * 2. Day Templates - ordered sequences of meal types
 * 3. Week Plans - weekday-to-template mappings
 */

import { useState } from 'react'
import { Plus, Star } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'

import { MealTypeEditor } from '@/components/mealframe/meal-type-editor'
import { DayTemplateEditor } from '@/components/mealframe/day-template-editor'
import { WeekPlanEditor } from '@/components/mealframe/week-plan-editor'

import {
  useMealTypes,
  useCreateMealType,
  useUpdateMealType,
  useDeleteMealType,
} from '@/hooks/use-meal-types'
import {
  useDayTemplates,
  useDayTemplate,
  useCreateDayTemplate,
  useUpdateDayTemplate,
  useDeleteDayTemplate,
} from '@/hooks/use-day-templates'
import {
  useWeekPlans,
  useWeekPlan,
  useCreateWeekPlan,
  useUpdateWeekPlan,
  useDeleteWeekPlan,
  useSetDefaultWeekPlan,
} from '@/hooks/use-week-plans'

import type {
  MealTypeWithCount,
  MealTypeCreate,
  MealTypeCompact,
  DayTemplateListItem,
  DayTemplateResponse,
  DayTemplateCreate,
  WeekPlanListItem,
  WeekPlanResponse,
  WeekPlanCreate,
} from '@/lib/types'

export default function SetupPage() {
  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto max-w-4xl px-4 pb-24 pt-safe">
        <header className="mb-6 pt-6">
          <h1 className="text-2xl font-semibold text-foreground">Setup</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Configure the building blocks for your meal plans
          </p>
        </header>

        <Tabs defaultValue="meal-types">
          <TabsList className="w-full">
            <TabsTrigger value="meal-types" className="flex-1">Meal Types</TabsTrigger>
            <TabsTrigger value="day-templates" className="flex-1">Day Templates</TabsTrigger>
            <TabsTrigger value="week-plans" className="flex-1">Week Plans</TabsTrigger>
          </TabsList>

          <TabsContent value="meal-types">
            <MealTypesTab />
          </TabsContent>
          <TabsContent value="day-templates">
            <DayTemplatesTab />
          </TabsContent>
          <TabsContent value="week-plans">
            <WeekPlansTab />
          </TabsContent>
        </Tabs>
      </div>
    </main>
  )
}

// =============================================================================
// Meal Types Tab
// =============================================================================

function MealTypesTab() {
  const { data: mealTypes, isLoading } = useMealTypes()
  const createMutation = useCreateMealType()
  const updateMutation = useUpdateMealType()
  const deleteMutation = useDeleteMealType()

  const [editorOpen, setEditorOpen] = useState(false)
  const [editingType, setEditingType] = useState<MealTypeWithCount | null>(null)

  const handleAdd = () => {
    setEditingType(null)
    setEditorOpen(true)
  }

  const handleEdit = (mt: MealTypeWithCount) => {
    setEditingType(mt)
    setEditorOpen(true)
  }

  const handleSave = (data: MealTypeCreate) => {
    if (editingType) {
      updateMutation.mutate(
        { id: editingType.id, data },
        { onSuccess: () => setEditorOpen(false) }
      )
    } else {
      createMutation.mutate(data, {
        onSuccess: () => setEditorOpen(false),
      })
    }
  }

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id, {
      onSuccess: () => setEditorOpen(false),
    })
  }

  if (isLoading) {
    return <TabSkeleton />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Meal types define functional eating slots (e.g., Breakfast, Pre-Workout Snack).
        </p>
        <Button onClick={handleAdd} size="sm">
          <Plus className="mr-2 h-4 w-4" />
          Add Type
        </Button>
      </div>

      {mealTypes && mealTypes.length === 0 && (
        <EmptyCard message="No meal types yet. Add one to get started." />
      )}

      {mealTypes && mealTypes.length > 0 && (
        <div className="space-y-2">
          {mealTypes.map((mt) => (
            <button
              key={mt.id}
              onClick={() => handleEdit(mt)}
              className="flex w-full items-center justify-between rounded-lg border border-border bg-card p-4 text-left transition-colors hover:bg-accent"
            >
              <div>
                <div className="font-medium">{mt.name}</div>
                {mt.description && (
                  <div className="mt-0.5 text-sm text-muted-foreground">{mt.description}</div>
                )}
                {mt.tags.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {mt.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <span className="ml-4 shrink-0 text-sm text-muted-foreground">
                {mt.meal_count} {mt.meal_count === 1 ? 'meal' : 'meals'}
              </span>
            </button>
          ))}
        </div>
      )}

      <MealTypeEditor
        open={editorOpen}
        onOpenChange={setEditorOpen}
        mealType={editingType}
        onSave={handleSave}
        onDelete={handleDelete}
        isSaving={createMutation.isPending || updateMutation.isPending}
      />
    </div>
  )
}

// =============================================================================
// Day Templates Tab
// =============================================================================

function DayTemplatesTab() {
  const { data: templates, isLoading: templatesLoading } = useDayTemplates()
  const { data: mealTypes } = useMealTypes()
  const createMutation = useCreateDayTemplate()
  const updateMutation = useUpdateDayTemplate()
  const deleteMutation = useDeleteDayTemplate()

  const [editorOpen, setEditorOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)

  // Fetch full template detail when editing (need slots with meal_type info)
  const { data: editingTemplate } = useDayTemplate(editingId)

  const mealTypeCompacts: MealTypeCompact[] = (mealTypes || []).map((mt) => ({
    id: mt.id,
    name: mt.name,
  }))

  const handleAdd = () => {
    setEditingId(null)
    setEditorOpen(true)
  }

  const handleEdit = (t: DayTemplateListItem) => {
    setEditingId(t.id)
    setEditorOpen(true)
  }

  const handleSave = (data: DayTemplateCreate) => {
    if (editingId) {
      updateMutation.mutate(
        { id: editingId, data },
        { onSuccess: () => { setEditorOpen(false); setEditingId(null) } }
      )
    } else {
      createMutation.mutate(data, {
        onSuccess: () => setEditorOpen(false),
      })
    }
  }

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id, {
      onSuccess: () => { setEditorOpen(false); setEditingId(null) },
    })
  }

  if (templatesLoading) {
    return <TabSkeleton />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Day templates are ordered sequences of meal types for a day pattern.
        </p>
        <Button onClick={handleAdd} size="sm">
          <Plus className="mr-2 h-4 w-4" />
          Add Template
        </Button>
      </div>

      {templates && templates.length === 0 && (
        <EmptyCard message="No day templates yet. Add one to define your daily structure." />
      )}

      {templates && templates.length > 0 && (
        <div className="space-y-2">
          {templates.map((t) => (
            <button
              key={t.id}
              onClick={() => handleEdit(t)}
              className="flex w-full items-center justify-between rounded-lg border border-border bg-card p-4 text-left transition-colors hover:bg-accent"
            >
              <div>
                <div className="font-medium">{t.name}</div>
                {t.slot_preview && (
                  <div className="mt-0.5 text-sm text-muted-foreground">{t.slot_preview}</div>
                )}
                {t.notes && (
                  <div className="mt-0.5 text-xs text-muted-foreground italic">{t.notes}</div>
                )}
                {(t.max_calories_kcal != null || t.max_protein_g != null) && (
                  <div className="mt-1 text-xs text-muted-foreground">
                    Max:{' '}
                    {[
                      t.max_calories_kcal != null && `${t.max_calories_kcal.toLocaleString()} kcal`,
                      t.max_protein_g != null && `${Number(t.max_protein_g)}g protein`,
                    ].filter(Boolean).join(' / ')}
                  </div>
                )}
              </div>
              <span className="ml-4 shrink-0 text-sm text-muted-foreground">
                {t.slot_count} {t.slot_count === 1 ? 'slot' : 'slots'}
              </span>
            </button>
          ))}
        </div>
      )}

      <DayTemplateEditor
        open={editorOpen}
        onOpenChange={(open) => {
          setEditorOpen(open)
          if (!open) setEditingId(null)
        }}
        template={editingId ? editingTemplate ?? null : null}
        mealTypes={mealTypeCompacts}
        onSave={handleSave}
        onDelete={handleDelete}
        isSaving={createMutation.isPending || updateMutation.isPending}
      />
    </div>
  )
}

// =============================================================================
// Week Plans Tab
// =============================================================================

function WeekPlansTab() {
  const { data: weekPlans, isLoading: plansLoading } = useWeekPlans()
  const { data: dayTemplates } = useDayTemplates()
  const createMutation = useCreateWeekPlan()
  const updateMutation = useUpdateWeekPlan()
  const deleteMutation = useDeleteWeekPlan()
  const setDefaultMutation = useSetDefaultWeekPlan()

  const [editorOpen, setEditorOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)

  // Fetch full week plan detail when editing (need days with template info)
  const { data: editingPlan } = useWeekPlan(editingId)

  const handleAdd = () => {
    setEditingId(null)
    setEditorOpen(true)
  }

  const handleEdit = (p: WeekPlanListItem) => {
    setEditingId(p.id)
    setEditorOpen(true)
  }

  const handleSave = (data: WeekPlanCreate) => {
    if (editingId) {
      updateMutation.mutate(
        { id: editingId, data },
        { onSuccess: () => { setEditorOpen(false); setEditingId(null) } }
      )
    } else {
      createMutation.mutate(data, {
        onSuccess: () => setEditorOpen(false),
      })
    }
  }

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id, {
      onSuccess: () => { setEditorOpen(false); setEditingId(null) },
    })
  }

  const handleSetDefault = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setDefaultMutation.mutate(id)
  }

  if (plansLoading) {
    return <TabSkeleton />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Week plans map day templates to weekdays. The default plan is used for generating new weeks.
        </p>
        <Button onClick={handleAdd} size="sm">
          <Plus className="mr-2 h-4 w-4" />
          Add Plan
        </Button>
      </div>

      {weekPlans && weekPlans.length === 0 && (
        <EmptyCard message="No week plans yet. Add one to define your weekly structure." />
      )}

      {weekPlans && weekPlans.length > 0 && (
        <div className="space-y-2">
          {weekPlans.map((p) => (
            <button
              key={p.id}
              onClick={() => handleEdit(p)}
              className="flex w-full items-center justify-between rounded-lg border border-border bg-card p-4 text-left transition-colors hover:bg-accent"
            >
              <div className="flex items-center gap-2">
                <div className="font-medium">{p.name}</div>
                {p.is_default && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                    <Star className="h-3 w-3" />
                    Default
                  </span>
                )}
              </div>
              <div className="ml-4 flex shrink-0 items-center gap-3">
                <span className="text-sm text-muted-foreground">
                  {p.day_count}/7 days
                </span>
                {!p.is_default && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => handleSetDefault(p.id, e)}
                    className="text-xs"
                    disabled={setDefaultMutation.isPending}
                  >
                    Set Default
                  </Button>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      <WeekPlanEditor
        open={editorOpen}
        onOpenChange={(open) => {
          setEditorOpen(open)
          if (!open) setEditingId(null)
        }}
        weekPlan={editingId ? editingPlan ?? null : null}
        dayTemplates={dayTemplates || []}
        onSave={handleSave}
        onDelete={handleDelete}
        isSaving={createMutation.isPending || updateMutation.isPending}
      />
    </div>
  )
}

// =============================================================================
// Shared Components
// =============================================================================

function TabSkeleton() {
  return (
    <div className="space-y-4 pt-2">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-64" />
        <Skeleton className="h-9 w-24" />
      </div>
      {[1, 2, 3].map((i) => (
        <Skeleton key={i} className="h-16 w-full rounded-lg" />
      ))}
    </div>
  )
}

function EmptyCard({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-muted/20 p-8 text-center">
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  )
}
