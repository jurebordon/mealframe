'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { X, BookOpen, Camera, SkipForward } from 'lucide-react'

interface DeviatedMealSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSelectFromLibrary: () => void
  onCaptureWithPhoto: () => void
  onSkip: () => void
}

export function DeviatedMealSheet({
  open,
  onOpenChange,
  onSelectFromLibrary,
  onCaptureWithPhoto,
  onSkip,
}: DeviatedMealSheetProps) {
  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-[60] bg-black/40 backdrop-blur-sm"
            onClick={() => onOpenChange(false)}
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
            aria-labelledby="deviated-meal-sheet-title"
          >
            {/* Drag Handle */}
            <div className="flex justify-center pt-3 pb-2">
              <div className="h-1 w-12 rounded-full bg-muted" aria-hidden="true" />
            </div>

            {/* Header */}
            <div className="flex items-center justify-between px-6 pb-2">
              <h2 id="deviated-meal-sheet-title" className="text-lg font-semibold text-foreground">
                What did you eat instead?
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

            {/* Options */}
            <div className="space-y-2 px-6 pb-6">
              <button
                onClick={() => {
                  onOpenChange(false)
                  onSelectFromLibrary()
                }}
                className="flex w-full items-center gap-4 rounded-2xl border border-border bg-background p-4 text-left transition-colors hover:bg-muted active:scale-[0.98]"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <BookOpen className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-medium text-foreground">Pick from Library</p>
                  <p className="text-sm text-muted-foreground">Choose what you actually ate</p>
                </div>
              </button>

              <button
                onClick={() => {
                  onOpenChange(false)
                  onCaptureWithPhoto()
                }}
                className="flex w-full items-center gap-4 rounded-2xl border border-border bg-background p-4 text-left transition-colors hover:bg-muted active:scale-[0.98]"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Camera className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-medium text-foreground">Capture with Photo</p>
                  <p className="text-sm text-muted-foreground">Take a photo to auto-fill macros</p>
                </div>
              </button>

              <button
                onClick={() => {
                  onOpenChange(false)
                  onSkip()
                }}
                className="flex w-full items-center gap-4 rounded-2xl border border-dashed border-border bg-background p-4 text-left transition-colors hover:bg-muted active:scale-[0.98]"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-muted text-muted-foreground">
                  <SkipForward className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-medium text-muted-foreground">Skip</p>
                  <p className="text-sm text-muted-foreground">Just mark as deviated</p>
                </div>
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
