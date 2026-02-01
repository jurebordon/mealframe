'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { CompletionStatus } from './status-badge'

/** Completion statuses that can be selected (excludes 'pending') */
export type SelectableCompletionStatus = Exclude<CompletionStatus, 'pending'>

interface CompletionSheetAnimatedProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  mealName: string
  onSelect: (status: SelectableCompletionStatus) => void
  /** Current status when editing an already-completed meal */
  currentStatus?: SelectableCompletionStatus | null
}

const statusOptions: Array<{
  status: Exclude<CompletionStatus, 'pending'>
  label: string
  description: string
  icon: React.ReactNode
  color: string
  isPrimary?: boolean
}> = [
  {
    status: 'followed',
    label: 'Followed',
    description: 'Ate as planned',
    color: 'bg-success/10 text-success border-success/30 hover:bg-success/20',
    isPrimary: true,
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        className="h-5 w-5"
      >
        <path
          fillRule="evenodd"
          d="M12.416 3.376a.75.75 0 0 1 .208 1.04l-5 7.5a.75.75 0 0 1-1.154.114l-3-3a.75.75 0 0 1 1.06-1.06l2.353 2.353 4.493-6.74a.75.75 0 0 1 1.04-.207Z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    status: 'adjusted',
    label: 'Adjusted',
    description: 'Similar but different portion',
    color: 'bg-warning/10 text-warning border-warning/30 hover:bg-warning/20',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        className="h-5 w-5"
      >
        <path
          fillRule="evenodd"
          d="M8 15A7 7 0 1 0 8 1a7 7 0 0 0 0 14Zm.75-10.25a.75.75 0 0 0-1.5 0v4.69L6.03 8.22a.75.75 0 0 0-1.06 1.06l2.5 2.5a.75.75 0 0 0 1.06 0l2.5-2.5a.75.75 0 1 0-1.06-1.06l-1.22 1.22V4.75Z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    status: 'skipped',
    label: 'Skipped',
    description: "Didn't eat this meal",
    color: 'bg-muted text-muted-foreground border-border hover:bg-muted/80',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        className="h-5 w-5"
      >
        <path
          fillRule="evenodd"
          d="M5.28 4.22a.75.75 0 0 0-1.06 1.06L6.94 8l-2.72 2.72a.75.75 0 1 0 1.06 1.06L8 9.06l2.72 2.72a.75.75 0 1 0 1.06-1.06L9.06 8l2.72-2.72a.75.75 0 0 0-1.06-1.06L8 6.94 5.28 4.22Z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    status: 'replaced',
    label: 'Replaced',
    description: 'Ate something else',
    color: 'bg-muted text-muted-foreground border-border hover:bg-muted/80',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        className="h-5 w-5"
      >
        <path
          fillRule="evenodd"
          d="M13.836 2.477a.75.75 0 0 1 .75.75v3.182a.75.75 0 0 1-.75.75h-3.182a.75.75 0 0 1 0-1.5h1.37L9.74 3.378a.75.75 0 0 1 1.06-1.06l2.281 2.28V3.227a.75.75 0 0 1 .75-.75Zm-2.551 7.5a.75.75 0 0 1 0 1.06l-2.28 2.28v-1.37a.75.75 0 0 0-1.5 0v3.182c0 .414.336.75.75.75h3.182a.75.75 0 0 0 0-1.5h-1.37l2.28-2.28a.75.75 0 0 0-1.06-1.06Z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    status: 'social',
    label: 'Social',
    description: 'Eating out / social event',
    color: 'bg-primary/10 text-primary border-primary/30 hover:bg-primary/20',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        className="h-5 w-5"
      >
        <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM12.735 14c.618 0 1.093-.561.872-1.139a6.002 6.002 0 0 0-11.215 0c-.22.578.254 1.139.872 1.139h9.47Z" />
      </svg>
    ),
  },
]

export function CompletionSheetAnimated({
  open,
  onOpenChange,
  mealName,
  onSelect,
  currentStatus,
}: CompletionSheetAnimatedProps) {
  const [selectedStatus, setSelectedStatus] = useState<SelectableCompletionStatus | null>(null)
  const isEditing = currentStatus != null

  const handleSelect = (status: SelectableCompletionStatus) => {
    setSelectedStatus(status)
    
    // Delay the callback to allow animation to play
    setTimeout(() => {
      onSelect(status)
      setSelectedStatus(null)
    }, 400)
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
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
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
            aria-labelledby="completion-sheet-title"
          >
            {/* Drag Handle */}
            <div className="flex justify-center pt-3 pb-2">
              <div className="h-1 w-12 rounded-full bg-muted" aria-hidden="true" />
            </div>

            {/* Header */}
            <div className="border-b border-border px-6 py-4">
              <div className="mb-1 flex items-start justify-between gap-3">
                <h2 id="completion-sheet-title" className="text-balance text-lg font-semibold text-foreground">
                  {isEditing ? 'Change status' : 'Mark completion status'}
                </h2>
                <button
                  onClick={() => onOpenChange(false)}
                  className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground active:scale-95"
                  type="button"
                  aria-label="Close completion status selector"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <p className="text-balance text-sm text-muted-foreground">{mealName}</p>
            </div>

            {/* Options */}
            <div className="max-h-[60vh] overflow-y-auto px-6 py-4">
              <div className="space-y-3">
                {statusOptions.map((option, index) => {
                  const isSelected = selectedStatus === option.status
                  const isCurrent = currentStatus === option.status

                  return (
                    <motion.button
                      key={option.status}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      onClick={() => handleSelect(option.status)}
                      disabled={selectedStatus !== null}
                      aria-label={`Mark as ${option.label.toLowerCase()}: ${option.description}${isCurrent ? ' (current)' : ''}`}
                      className={cn(
                        'relative flex min-h-[64px] w-full items-center gap-4 rounded-xl border-2 p-4 text-left transition-all active:scale-95',
                        option.color,
                        option.isPrimary && 'min-h-[72px]',
                        isSelected && 'scale-[0.98]',
                        selectedStatus && !isSelected && 'opacity-40',
                        isCurrent && 'ring-2 ring-foreground/20'
                      )}
                      type="button"
                    >
                      {/* Icon */}
                      <motion.div
                        className="flex-shrink-0"
                        animate={
                          isSelected
                            ? {
                                scale: [1, 1.3, 1],
                                rotate: option.status === 'followed' ? [0, 360] : 0,
                              }
                            : {}
                        }
                        transition={{ duration: 0.4 }}
                      >
                        {option.icon}
                      </motion.div>

                      {/* Content */}
                      <div className="flex-1 space-y-1">
                        <div className={cn('flex items-center gap-2 font-semibold', option.isPrimary && 'text-base')}>
                          {option.label}
                          {isCurrent && (
                            <span className="rounded-full bg-foreground/10 px-2 py-0.5 text-xs font-normal">
                              Current
                            </span>
                          )}
                        </div>
                        <div className={cn('text-sm opacity-80', option.isPrimary && 'text-base')}>
                          {option.description}
                        </div>
                      </div>

                      {/* Checkmark on selection */}
                      <AnimatePresence>
                        {isSelected && (
                          <motion.div
                            initial={{ scale: 0, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="flex-shrink-0"
                          >
                            <svg
                              className="h-6 w-6"
                              fill="currentColor"
                              viewBox="0 0 16 16"
                            >
                              <path
                                fillRule="evenodd"
                                d="M12.416 3.376a.75.75 0 0 1 .208 1.04l-5 7.5a.75.75 0 0 1-1.154.114l-3-3a.75.75 0 0 1 1.06-1.06l2.353 2.353 4.493-6.74a.75.75 0 0 1 1.04-.207Z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.button>
                  )
                })}
              </div>
            </div>

            {/* Safe area padding for mobile */}
            <div className="h-8" />
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
