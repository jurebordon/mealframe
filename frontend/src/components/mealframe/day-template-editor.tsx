'use client'

import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ChevronUp, ChevronDown, X, Plus, Trash2 } from 'lucide-react'
import type {
  DayTemplateResponse,
  DayTemplateCreate,
  DayTemplateSlotCreate,
  MealTypeCompact,
} from '@/lib/types'

// Local editable slot with a temp ID for stable React keys
interface EditableSlot extends DayTemplateSlotCreate {
  tempId: string
}

interface DayTemplateEditorProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  template?: DayTemplateResponse | null
  mealTypes: MealTypeCompact[]
  onSave: (data: DayTemplateCreate) => void
  onDelete?: (id: string) => void
  isSaving?: boolean
}

function createEditableSlotsFromTemplate(template: DayTemplateResponse): EditableSlot[] {
  return template.slots
    .slice()
    .sort((a, b) => a.position - b.position)
    .map((slot) => ({
      tempId: slot.id,
      position: slot.position,
      meal_type_id: slot.meal_type.id,
    }))
}

let slotCounter = 0

export function DayTemplateEditor({
  open,
  onOpenChange,
  template,
  mealTypes,
  onSave,
  onDelete,
  isSaving,
}: DayTemplateEditorProps) {
  const [name, setName] = useState('')
  const [notes, setNotes] = useState('')
  const [slots, setSlots] = useState<EditableSlot[]>([])
  const [maxCalories, setMaxCalories] = useState('')
  const [maxProtein, setMaxProtein] = useState('')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  // Reset form when dialog opens or the template prop changes
  const resetForm = useCallback(() => {
    if (template) {
      setName(template.name)
      setNotes(template.notes ?? '')
      setSlots(createEditableSlotsFromTemplate(template))
      setMaxCalories(template.max_calories_kcal != null ? String(template.max_calories_kcal) : '')
      setMaxProtein(template.max_protein_g != null ? String(Number(template.max_protein_g)) : '')
    } else {
      setName('')
      setNotes('')
      setSlots([])
      setMaxCalories('')
      setMaxProtein('')
    }
    setShowDeleteConfirm(false)
  }, [template])

  useEffect(() => {
    if (open) {
      resetForm()
    }
  }, [open, resetForm])

  // Look up the meal type name by ID for display
  const getMealTypeName = (mealTypeId: string): string => {
    return mealTypes.find((mt) => mt.id === mealTypeId)?.name ?? 'Unknown'
  }

  const handleAddSlot = () => {
    if (mealTypes.length === 0) return
    slotCounter += 1
    const newSlot: EditableSlot = {
      tempId: `new-slot-${Date.now()}-${slotCounter}`,
      position: slots.length + 1, // 1-based position
      meal_type_id: mealTypes[0].id,
    }
    setSlots([...slots, newSlot])
  }

  const handleRemoveSlot = (tempId: string) => {
    setSlots(
      slots
        .filter((s) => s.tempId !== tempId)
        .map((s, idx) => ({ ...s, position: idx + 1 })) // 1-based position
    )
  }

  const handleMoveSlot = (tempId: string, direction: 'up' | 'down') => {
    const index = slots.findIndex((s) => s.tempId === tempId)
    if (
      (direction === 'up' && index === 0) ||
      (direction === 'down' && index === slots.length - 1)
    ) {
      return
    }

    const newSlots = [...slots]
    const swapIndex = direction === 'up' ? index - 1 : index + 1
    ;[newSlots[index], newSlots[swapIndex]] = [newSlots[swapIndex], newSlots[index]]

    setSlots(newSlots.map((s, idx) => ({ ...s, position: idx + 1 }))) // 1-based position
  }

  const handleUpdateSlotMealType = (tempId: string, mealTypeId: string) => {
    setSlots(
      slots.map((s) =>
        s.tempId === tempId ? { ...s, meal_type_id: mealTypeId } : s
      )
    )
  }

  const handleSave = () => {
    if (!name.trim() || slots.length === 0) return

    const parsedMaxCalories = maxCalories ? parseInt(maxCalories) : null
    const parsedMaxProtein = maxProtein ? parseFloat(maxProtein) : null

    const payload: DayTemplateCreate = {
      name: name.trim(),
      notes: notes.trim() || null,
      max_calories_kcal: parsedMaxCalories,
      max_protein_g: parsedMaxProtein,
      slots: slots.map(({ position, meal_type_id }) => ({
        position,
        meal_type_id,
      })),
    }
    onSave(payload)
  }

  const handleDelete = () => {
    if (template && onDelete) {
      onDelete(template.id)
    }
  }

  const isEditing = !!template
  const canSave = name.trim().length > 0 && slots.length > 0 && !isSaving

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Edit Day Template' : 'Add Day Template'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Name */}
          <div className="space-y-2">
            <Label htmlFor="template-name">Template Name</Label>
            <Input
              id="template-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Normal Workday, Morning Workout Day"
              disabled={isSaving}
            />
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="template-notes">Notes</Label>
            <Textarea
              id="template-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional notes about this template..."
              rows={2}
              disabled={isSaving}
            />
          </div>

          {/* Slots */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Meal Slots ({slots.length})</Label>
              <Button
                onClick={handleAddSlot}
                variant="outline"
                size="sm"
                disabled={mealTypes.length === 0 || isSaving}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Slot
              </Button>
            </div>

            {slots.length === 0 ? (
              <div className="rounded-lg border border-dashed border-border bg-muted/20 p-8 text-center">
                <p className="text-sm text-muted-foreground">
                  No slots yet. Add a slot to get started.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {slots.map((slot, index) => (
                  <div
                    key={slot.tempId}
                    className="flex items-center gap-3 rounded-lg border border-border bg-card p-3"
                  >
                    {/* Reorder Buttons */}
                    <div className="flex flex-col gap-1">
                      <button
                        onClick={() => handleMoveSlot(slot.tempId, 'up')}
                        disabled={index === 0 || isSaving}
                        className="rounded p-1 hover:bg-secondary disabled:opacity-30"
                        type="button"
                      >
                        <ChevronUp className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleMoveSlot(slot.tempId, 'down')}
                        disabled={index === slots.length - 1 || isSaving}
                        className="rounded p-1 hover:bg-secondary disabled:opacity-30"
                        type="button"
                      >
                        <ChevronDown className="h-4 w-4" />
                      </button>
                    </div>

                    {/* Position Number */}
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                      {index + 1}
                    </div>

                    {/* Meal Type Selector */}
                    <div className="flex-1">
                      <Select
                        value={slot.meal_type_id}
                        onValueChange={(value) =>
                          handleUpdateSlotMealType(slot.tempId, value)
                        }
                        disabled={isSaving}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {mealTypes.map((mealType) => (
                            <SelectItem key={mealType.id} value={mealType.id}>
                              {mealType.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Remove Button */}
                    <Button
                      onClick={() => handleRemoveSlot(slot.tempId)}
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      disabled={isSaving}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Slot Preview */}
          {slots.length > 0 && (
            <div className="space-y-2">
              <Label>Preview</Label>
              <div className="rounded-lg border border-border bg-muted/20 p-4">
                <p className="text-sm text-muted-foreground">
                  {slots.map((s) => getMealTypeName(s.meal_type_id)).join(' \u2192 ')}
                </p>
              </div>
            </div>
          )}

          {/* Soft Limits */}
          <div className="space-y-3 border-t border-border pt-6">
            <div>
              <Label className="text-base">Daily Limits (optional)</Label>
              <p className="mt-1 text-sm text-muted-foreground">
                Soft limits for tracking. Days exceeding these will appear in your stats.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="max-calories" className="text-sm font-normal">
                  Max Calories
                </Label>
                <div className="relative">
                  <Input
                    id="max-calories"
                    type="number"
                    value={maxCalories}
                    onChange={(e) => setMaxCalories(e.target.value)}
                    placeholder="e.g. 2200"
                    className="pr-12"
                    disabled={isSaving}
                  />
                  <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                    kcal
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="max-protein" className="text-sm font-normal">
                  Max Protein
                </Label>
                <div className="relative">
                  <Input
                    id="max-protein"
                    type="number"
                    step="0.1"
                    value={maxProtein}
                    onChange={(e) => setMaxProtein(e.target.value)}
                    placeholder="e.g. 180"
                    className="pr-8"
                    disabled={isSaving}
                  />
                  <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                    g
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter className="flex-col gap-2 sm:flex-row sm:gap-3">
          {isEditing && onDelete && showDeleteConfirm && (
            <div className="flex w-full flex-col gap-2 sm:flex-1">
              <p className="text-sm text-muted-foreground">
                Are you sure you want to delete this template?
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
