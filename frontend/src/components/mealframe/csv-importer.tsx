'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { X, Upload, CheckCircle, AlertCircle, AlertTriangle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { importMeals } from '@/lib/api'
import type { MealImportResult } from '@/lib/types'

interface CSVImporterProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onImportComplete?: () => void
}

export function CSVImporter({ open, onOpenChange, onImportComplete }: CSVImporterProps) {
  const [file, setFile] = useState<File | null>(null)
  const [step, setStep] = useState<'upload' | 'importing' | 'complete'>('upload')
  const [result, setResult] = useState<MealImportResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
    }
  }

  const handleImport = async () => {
    if (!file) return

    setStep('importing')
    setError(null)

    try {
      const importResult = await importMeals(file)
      setResult(importResult)
      setStep('complete')
      if (importResult.success && importResult.summary.created > 0) {
        onImportComplete?.()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed')
      setStep('upload')
    }
  }

  const handleClose = () => {
    setFile(null)
    setResult(null)
    setError(null)
    setStep('upload')
    onOpenChange(false)
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
            onClick={handleClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed inset-0 z-50 m-auto h-fit max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-border bg-card p-6 shadow-2xl"
          >
            {/* Header */}
            <div className="mb-6 flex items-start justify-between">
              <div>
                <h2 className="text-2xl font-bold text-foreground">Import CSV</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Upload a CSV file to bulk import meals
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleClose}
                className="h-8 w-8 p-0 bg-transparent"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Upload Step */}
            {step === 'upload' && (
              <div className="space-y-6">
                {error && (
                  <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                      <p className="text-sm text-destructive">{error}</p>
                    </div>
                  </div>
                )}

                <div className="rounded-xl border-2 border-dashed border-border bg-muted/20 p-12 text-center">
                  <Upload className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                  <p className="mb-2 text-sm font-semibold text-foreground">
                    {file ? file.name : 'Choose a CSV file'}
                  </p>
                  <p className="mb-4 text-xs text-muted-foreground">
                    Required columns: name, portion_description. Optional: calories_kcal, protein_g, carbs_g, fat_g, meal_types, notes
                  </p>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="hidden"
                    id="csv-upload"
                  />
                  <label htmlFor="csv-upload">
                    <Button asChild variant={file ? 'outline' : 'default'}>
                      <span>{file ? 'Change File' : 'Select File'}</span>
                    </Button>
                  </label>
                </div>

                <div className="rounded-lg border border-border bg-muted/20 p-4">
                  <p className="mb-2 text-xs font-semibold text-foreground">CSV Format Example:</p>
                  <pre className="overflow-x-auto text-xs text-muted-foreground">
                    {`name,portion_description,calories_kcal,protein_g,carbs_g,fat_g,meal_types,notes
"Scrambled Eggs","2 eggs + 1 slice toast",320,18,15,22,"Breakfast","Use whole wheat"
"Chicken Bowl","150g chicken + rice",520,42,50,12,"Lunch,Dinner","Meal prep friendly"`}
                  </pre>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 border-t border-border pt-6">
                  <Button variant="outline" onClick={handleClose}>
                    Cancel
                  </Button>
                  <Button onClick={handleImport} disabled={!file}>
                    Import
                  </Button>
                </div>
              </div>
            )}

            {/* Importing Step */}
            {step === 'importing' && (
              <div className="space-y-6 text-center py-12">
                <div className="h-8 w-8 mx-auto animate-spin rounded-full border-2 border-primary border-t-transparent" />
                <p className="text-sm text-muted-foreground">
                  Importing meals from {file?.name}...
                </p>
              </div>
            )}

            {/* Complete Step */}
            {step === 'complete' && result && (
              <div className="space-y-6">
                {/* Summary */}
                <div className="text-center">
                  <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-success/20">
                    <CheckCircle className="h-8 w-8 text-success" />
                  </div>
                  <h3 className="mb-2 text-xl font-bold text-foreground">
                    Import {result.success ? 'Complete' : 'Failed'}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {result.summary.created} meals created
                    {result.summary.skipped > 0 && `, ${result.summary.skipped} rows skipped`}
                    {result.summary.warnings > 0 && `, ${result.summary.warnings} warnings`}
                  </p>
                </div>

                {/* Warnings */}
                {result.warnings.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-foreground flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-yellow-500" />
                      Warnings
                    </p>
                    <div className="max-h-40 space-y-1 overflow-y-auto rounded-lg border border-yellow-500/30 bg-yellow-500/5 p-3">
                      {result.warnings.map((w, i) => (
                        <p key={i} className="text-xs text-muted-foreground">
                          <span className="font-medium">Row {w.row}:</span> {w.message}
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                {/* Errors */}
                {result.errors.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-foreground flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-destructive" />
                      Errors (rows skipped)
                    </p>
                    <div className="max-h-40 space-y-1 overflow-y-auto rounded-lg border border-destructive/30 bg-destructive/5 p-3">
                      {result.errors.map((e, i) => (
                        <p key={i} className="text-xs text-muted-foreground">
                          <span className="font-medium">Row {e.row}:</span> {e.message}
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                <Button onClick={handleClose} className="w-full">
                  Done
                </Button>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
