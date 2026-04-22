'use client'

import { useState, useEffect, useCallback } from 'react'
import { Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type {
  WeekPlanResponse,
  WeekPlanCreate,
  WeekPlanDayCreate,
  DayTemplateListItem,
  Weekday,
} from '@/lib/types'
import { WEEKDAY_NAMES } from '@/lib/types'

const UNASSIGNED_VALUE = '__none__'

const WEEKDAY_NAMES_SHORT: Record<Weekday, string> = {
  0: 'Mon',
  1: 'Tue',
  2: 'Wed',
  3: 'Thu',
  4: 'Fri',
  5: 'Sat',
  6: 'Sun',
}

const ALL_WEEKDAYS: Weekday[] = [0, 1, 2, 3, 4, 5, 6]

interface WeekPlanEditorProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  weekPlan?: WeekPlanResponse | null
  dayTemplates: DayTemplateListItem[]
  onSave: (data: WeekPlanCreate) => void
  onDelete?: (id: string) => void
  isSaving?: boolean
}

function buildDayMappingsFromWeekPlan(
  weekPlan: WeekPlanResponse
): Record<number, string | null> {
  const mappings: Record<number, string | null> = {}
  for (const day of ALL_WEEKDAYS) {
    mappings[day] = null
  }
  for (const day of weekPlan.days) {
    mappings[day.weekday] = day.day_template.id
  }
  return mappings
}

function emptyDayMappings(): Record<number, string | null> {
  const mappings: Record<number, string | null> = {}
  for (const day of ALL_WEEKDAYS) {
    mappings[day] = null
  }
  return mappings
}

export function WeekPlanEditor({
  open,
  onOpenChange,
  weekPlan,
  dayTemplates,
  onSave,
  onDelete,
  isSaving,
}: WeekPlanEditorProps) {
  const [name, setName] = useState('')
  const [dayMappings, setDayMappings] = useState<Record<number, string | null>>(
    emptyDayMappings
  )
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  // Reset form when dialog opens or the weekPlan prop changes
  const resetForm = useCallback(() => {
    if (weekPlan) {
      setName(weekPlan.name)
      setDayMappings(buildDayMappingsFromWeekPlan(weekPlan))
    } else {
      setName('')
      setDayMappings(emptyDayMappings())
    }
    setShowDeleteConfirm(false)
  }, [weekPlan])

  useEffect(() => {
    if (open) {
      resetForm()
    }
  }, [open, resetForm])

  const handleDayMappingChange = (weekday: Weekday, value: string) => {
    setDayMappings((prev) => ({
      ...prev,
      [weekday]: value === UNASSIGNED_VALUE ? null : value,
    }))
  }

  const getTemplatePreview = (templateId: string | null): string | null => {
    if (!templateId) return null
    const template = dayTemplates.find((t) => t.id === templateId)
    return template?.slot_preview ?? null
  }

  const handleSave = () => {
    const trimmedName = name.trim()
    if (!trimmedName) return

    const days: WeekPlanDayCreate[] = ALL_WEEKDAYS.filter(
      (weekday) => dayMappings[weekday] != null
    ).map((weekday) => ({
      weekday,
      day_template_id: dayMappings[weekday]!,
    }))

    const payload: WeekPlanCreate = {
      name: trimmedName,
      days,
    }

    onSave(payload)
  }

  const handleDelete = () => {
    if (weekPlan && onDelete) {
      onDelete(weekPlan.id)
    }
  }

  const isEditing = !!weekPlan
  const canSave = name.trim().length > 0 && !isSaving

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto overflow-x-hidden">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Edit Week Plan' : 'Add Week Plan'}
          </DialogTitle>
        </DialogHeader>

        <div className="min-w-0 space-y-6 py-4">
          {/* Name */}
          <div className="space-y-2">
            <Label htmlFor="week-plan-name">Name</Label>
            <Input
              id="week-plan-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Standard Week, Training Week"
              disabled={isSaving}
            />
          </div>

          {/* Day Mappings */}
          <div className="space-y-2">
            <Label>Day Templates</Label>
            <div className="space-y-2">
              {ALL_WEEKDAYS.map((weekday) => {
                const templateId = dayMappings[weekday]
                const preview = getTemplatePreview(templateId)

                return (
                  <div
                    key={weekday}
                    className="overflow-hidden rounded-lg border border-border bg-card p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 sm:w-24 shrink-0 text-sm font-medium">
                        <span className="sm:hidden">{WEEKDAY_NAMES_SHORT[weekday]}</span>
                        <span className="hidden sm:inline">{WEEKDAY_NAMES[weekday]}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <Select
                          value={templateId ?? UNASSIGNED_VALUE}
                          onValueChange={(value) =>
                            handleDayMappingChange(weekday, value)
                          }
                          disabled={isSaving}
                        >
                          <SelectTrigger className="w-full overflow-hidden">
                            <SelectValue placeholder="No template" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value={UNASSIGNED_VALUE}>
                              None
                            </SelectItem>
                            {dayTemplates.map((template) => (
                              <SelectItem key={template.id} value={template.id}>
                                {template.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    {templateId && preview && (
                      <p className="mt-1 ml-13 sm:ml-27 max-w-full text-xs text-muted-foreground break-words">
                        {preview}
                      </p>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        <DialogFooter className="flex-col gap-2 sm:flex-row sm:gap-3">
          {isEditing && onDelete && showDeleteConfirm && (
            <div className="flex w-full flex-col gap-2 sm:flex-1">
              <p className="text-sm text-muted-foreground">
                Are you sure you want to delete this week plan?
              </p>
              <div className="flex gap-2">
                <Button
                  variant="destructive"
                  onClick={handleDelete}
                  size="sm"
                  className="flex-1"
                  disabled={isSaving}
                >
                  Confirm Delete
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowDeleteConfirm(false)}
                  size="sm"
                  className="flex-1"
                  disabled={isSaving}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {(!isEditing || !onDelete || !showDeleteConfirm) && (
            <>
              {isEditing && onDelete && (
                <Button
                  variant="outline"
                  onClick={() => setShowDeleteConfirm(true)}
                  size="sm"
                  className="border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground"
                  disabled={isSaving}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
              <div className="flex flex-1 gap-2">
                <Button
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                  size="sm"
                  className="flex-1"
                  disabled={isSaving}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={!canSave}
                  size="sm"
                  className="flex-1"
                >
                  {isSaving ? 'Saving...' : 'Save'}
                </Button>
              </div>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
