'use client'

import { useState, useRef, useEffect, useCallback, useImperativeHandle, forwardRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Loader2, AlertCircle, Camera, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { captureAiMeal, createMeal, addAdhocSlot } from '@/lib/api'
import { ApiError } from '@/lib/api'
import { useMealTypes } from '@/hooks/use-meal-types'
import type { AICaptureResponse, MealCreate } from '@/lib/types'

type Phase = 'idle' | 'analyzing' | 'confirming' | 'error'

export interface AiCaptureSheetHandle {
  triggerFilePicker: () => void
}

interface AiCaptureSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onMealSaved: (mealId: string) => void
}

function mapCaptureError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 504) return 'Analysis timed out. Please try again.'
    if (error.status === 400) return 'Could not identify food in this photo. Try a clearer image.'
    if (error.status === 502) return 'Analysis service unavailable. Please try again.'
    if (error.status === 413) return 'Photo is too large. Please use a smaller image.'
    if (error.status === 503) return `Service not configured (${error.message})`
    return `Error ${error.status}: ${error.message}`
  }
  if (error instanceof Error) return `${error.name}: ${error.message}`
  return 'Something went wrong. Please try again.'
}

export const AiCaptureSheet = forwardRef<AiCaptureSheetHandle, AiCaptureSheetProps>(function AiCaptureSheet({
  open,
  onOpenChange,
  onMealSaved,
}, ref) {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  useImperativeHandle(ref, () => ({
    triggerFilePicker: () => fileInputRef.current?.click(),
  }))

  const [phase, setPhase] = useState<Phase>('idle')
  const [captureResult, setCaptureResult] = useState<AICaptureResponse | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [selectedMealTypeId, setSelectedMealTypeId] = useState<string>('')
  const [isSaving, setIsSaving] = useState(false)

  const { data: mealTypes } = useMealTypes()

  // Pre-fill meal type when capture result arrives
  useEffect(() => {
    if (captureResult && mealTypes) {
      const match = mealTypes.find(
        (mt) => mt.name.toLowerCase() === captureResult.suggested_meal_type?.toLowerCase()
      )
      setSelectedMealTypeId(match?.id ?? mealTypes[0]?.id ?? '')
    }
  }, [captureResult, mealTypes])

  // Reset state when sheet closes
  useEffect(() => {
    if (!open) {
      const timer = setTimeout(() => {
        setPhase('idle')
        setCaptureResult(null)
        setErrorMessage(null)
        setSelectedMealTypeId('')
        setIsSaving(false)
      }, 350)
      return () => clearTimeout(timer)
    }
  }, [open])

  const captureMutation = useMutation({
    mutationFn: (file: File) => captureAiMeal(file),
    onSuccess: (data) => {
      setCaptureResult(data)
      setPhase('confirming')
    },
    onError: (error) => {
      setErrorMessage(mapCaptureError(error))
      setPhase('error')
    },
  })

  const handleFileSelected = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) {
      // User cancelled file picker
      onOpenChange(false)
      return
    }
    setPhase('analyzing')
    captureMutation.mutate(file)
    // Reset input so the same file can be selected again on retry
    e.target.value = ''
  }, [captureMutation, onOpenChange])

  const handleRetry = useCallback(() => {
    setPhase('idle')
    setCaptureResult(null)
    setErrorMessage(null)
    // Trigger file picker again
    setTimeout(() => {
      fileInputRef.current?.click()
    }, 100)
  }, [])

  const handleSave = useCallback(async () => {
    if (!captureResult) return
    setIsSaving(true)

    try {
      const mealData: MealCreate = {
        name: captureResult.meal_name,
        portion_description: captureResult.portion_description,
        calories_kcal: captureResult.calories_kcal,
        protein_g: captureResult.protein_g,
        carbs_g: captureResult.carbs_g,
        sugar_g: captureResult.sugar_g,
        fat_g: captureResult.fat_g,
        saturated_fat_g: captureResult.saturated_fat_g,
        fiber_g: captureResult.fiber_g,
        meal_type_ids: selectedMealTypeId ? [selectedMealTypeId] : [],
        source: 'ai_capture',
        confidence_score: captureResult.confidence_score,
        ai_model_version: captureResult.ai_model_version,
      }

      const meal = await createMeal(mealData)
      await addAdhocSlot({ meal_id: meal.id })
      queryClient.invalidateQueries({ queryKey: ['today'] })
      onMealSaved(meal.id)
      onOpenChange(false)
    } catch {
      setErrorMessage('Failed to save meal. Please try again.')
      setIsSaving(false)
    }
  }, [captureResult, selectedMealTypeId, queryClient, onMealSaved, onOpenChange])

  const showSheet = phase !== 'idle'

  return (
    <>
      {/* Hidden file input — always mounted */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="sr-only"
        onChange={handleFileSelected}
      />

      <AnimatePresence>
        {open && showSheet && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 z-[60] bg-black/40 backdrop-blur-sm"
              onClick={phase === 'analyzing' ? undefined : () => onOpenChange(false)}
            />

            {/* Sheet */}
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
              className="fixed inset-x-0 bottom-0 z-[60] mx-auto max-w-[480px] rounded-t-3xl border-t border-border bg-card pb-safe shadow-2xl"
              role="dialog"
              aria-modal="true"
              aria-labelledby="ai-capture-sheet-title"
            >
              {/* Drag Handle */}
              <div className="flex justify-center pt-3 pb-2">
                <div className="h-1 w-12 rounded-full bg-muted" aria-hidden="true" />
              </div>

              {/* Analyzing State */}
              {phase === 'analyzing' && (
                <div className="flex flex-col items-center justify-center px-6 pb-8 pt-4">
                  <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  </div>
                  <h2 id="ai-capture-sheet-title" className="text-lg font-semibold text-foreground">
                    Analyzing your meal...
                  </h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    This usually takes a few seconds
                  </p>
                </div>
              )}

              {/* Confirming State */}
              {phase === 'confirming' && captureResult && (
                <div className="max-h-[80dvh] overflow-y-auto px-6 pb-6">
                  {/* Header */}
                  <div className="flex items-center justify-between pb-4">
                    <h2 id="ai-capture-sheet-title" className="text-lg font-semibold text-foreground">
                      Confirm meal
                    </h2>
                    <button
                      onClick={() => onOpenChange(false)}
                      className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground active:scale-95"
                      type="button"
                      aria-label="Close"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  {/* Meal Info */}
                  <div className="mb-4">
                    <h3 className="text-xl font-semibold text-foreground">
                      {captureResult.meal_name}
                    </h3>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {captureResult.portion_description}
                    </p>
                  </div>

                  {/* Macro Grid */}
                  <div className="mb-4 grid grid-cols-4 gap-2">
                    <MacroCard label="kcal" value={captureResult.calories_kcal} />
                    <MacroCard label="protein" value={captureResult.protein_g} unit="g" />
                    <MacroCard label="carbs" value={captureResult.carbs_g} unit="g" />
                    <MacroCard label="fat" value={captureResult.fat_g} unit="g" />
                  </div>

                  {/* Confidence */}
                  <div className="mb-4 flex items-center gap-2">
                    <div className="h-1.5 flex-1 rounded-full bg-muted">
                      <div
                        className="h-1.5 rounded-full bg-primary transition-all"
                        style={{ width: `${Math.round(captureResult.confidence_score * 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {Math.round(captureResult.confidence_score * 100)}% confidence
                    </span>
                  </div>

                  {/* Meal Type Selector */}
                  <div className="mb-6">
                    <label
                      htmlFor="meal-type-select"
                      className="mb-1.5 block text-sm font-medium text-foreground"
                    >
                      Meal type
                    </label>
                    <select
                      id="meal-type-select"
                      value={selectedMealTypeId}
                      onChange={(e) => setSelectedMealTypeId(e.target.value)}
                      className="w-full rounded-xl border border-border bg-background px-3 py-2.5 text-sm text-foreground outline-none focus:ring-2 focus:ring-primary/20"
                    >
                      {mealTypes?.map((mt) => (
                        <option key={mt.id} value={mt.id}>
                          {mt.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Actions */}
                  <div className="space-y-2">
                    <Button
                      onClick={handleSave}
                      disabled={isSaving}
                      className="w-full"
                      size="lg"
                    >
                      {isSaving ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        'Save'
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={handleRetry}
                      disabled={isSaving}
                      className="w-full gap-2"
                    >
                      <RotateCcw className="h-4 w-4" />
                      Retry
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => onOpenChange(false)}
                      disabled={isSaving}
                      className="w-full text-muted-foreground"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}

              {/* Error State */}
              {phase === 'error' && (
                <div className="flex flex-col items-center px-6 pb-6 pt-4">
                  <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
                    <AlertCircle className="h-8 w-8 text-destructive" />
                  </div>
                  <p className="mb-6 text-center text-sm text-muted-foreground">
                    {errorMessage}
                  </p>
                  <div className="w-full space-y-2">
                    <Button onClick={handleRetry} className="w-full gap-2">
                      <Camera className="h-4 w-4" />
                      Try again
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => onOpenChange(false)}
                      className="w-full text-muted-foreground"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
})

function MacroCard({
  label,
  value,
  unit,
}: {
  label: string
  value: number | null
  unit?: string
}) {
  return (
    <div className="rounded-xl bg-muted/50 p-3 text-center">
      <p className="text-lg font-semibold text-foreground">
        {value != null ? Math.round(value) : '—'}
        {unit && value != null && <span className="text-xs font-normal text-muted-foreground">{unit}</span>}
      </p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  )
}
