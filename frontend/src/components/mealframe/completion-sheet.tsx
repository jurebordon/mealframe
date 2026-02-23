'use client'

import React from "react"

import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { cn } from '@/lib/utils'
import type { CompletionStatus } from './status-badge'

interface CompletionSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  mealName: string
  onSelect: (status: CompletionStatus) => void
}

const statusOptions: Array<{
  status: Exclude<CompletionStatus, 'pending'>
  label: string
  description: string
  icon: React.ReactNode
  color: string
}> = [
  {
    status: 'followed',
    label: 'Followed',
    description: 'Ate as planned',
    color: 'bg-success/10 text-success border-success/20 hover:bg-success/20',
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
    status: 'equivalent',
    label: 'Equivalent',
    description: 'Similar but different portion',
    color: 'bg-warning/10 text-warning border-warning/20 hover:bg-warning/20',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        className="h-5 w-5"
      >
        <path d="M8.75 3.75a.75.75 0 0 0-1.5 0v3.5h-3.5a.75.75 0 0 0 0 1.5h3.5v3.5a.75.75 0 0 0 1.5 0v-3.5h3.5a.75.75 0 0 0 0-1.5h-3.5v-3.5Z" />
      </svg>
    ),
  },
  {
    status: 'skipped',
    label: 'Skipped',
    description: 'Did not eat this meal',
    color: 'bg-muted text-muted-foreground border-border hover:bg-muted/80',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        className="h-5 w-5"
      >
        <path d="M6.22 4.22a.75.75 0 0 1 1.06 0L10.06 7l-2.78 2.78a.75.75 0 0 1-1.06-1.06L7.44 7.5H3.75a.75.75 0 0 1 0-1.5h3.69L6.22 4.78a.75.75 0 0 1 0-1.06Z" />
      </svg>
    ),
  },
  {
    status: 'deviated',
    label: 'Deviated',
    description: 'Ate something completely different',
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
          d="M13.836 2.477a.75.75 0 0 1 .75.75v4.796a.75.75 0 0 1-.75.75h-4.796a.75.75 0 0 0 0 1.5h2.966l-5.469 5.47a.75.75 0 1 1-1.061-1.061l5.469-5.47v2.967a.75.75 0 0 0 1.5 0V3.227a.75.75 0 0 1 .75-.75Z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    status: 'social',
    label: 'Social',
    description: 'External context prevented following',
    color: 'bg-primary/10 text-primary border-primary/20 hover:bg-primary/20',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        className="h-5 w-5"
      >
        <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM12.5 16h.5a2 2 0 0 0 2-2v-.5a2.5 2.5 0 0 0-2.5-2.5h-3v5ZM3.5 11A2.5 2.5 0 0 0 1 13.5v.5a2 2 0 0 0 2 2h.5v-5h-3Z" />
      </svg>
    ),
  },
]

export function CompletionSheet({ open, onOpenChange, mealName, onSelect }: CompletionSheetProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="bottom" className="rounded-t-xl">
        <SheetHeader className="text-left">
          <SheetTitle className="text-balance">Mark completion status</SheetTitle>
          <SheetDescription className="text-pretty">{mealName}</SheetDescription>
        </SheetHeader>
        <div className="mt-6 space-y-2">
          {statusOptions.map((option) => (
            <button
              key={option.status}
              onClick={() => {
                onSelect(option.status)
                onOpenChange(false)
              }}
              className={cn(
                'flex w-full items-center gap-4 rounded-lg border p-4 text-left transition-all',
                option.color
              )}
              type="button"
            >
              <div className="flex-shrink-0">{option.icon}</div>
              <div className="flex-1 space-y-0.5">
                <div className="font-medium">{option.label}</div>
                <div className="text-sm opacity-80">{option.description}</div>
              </div>
            </button>
          ))}
        </div>
      </SheetContent>
    </Sheet>
  )
}
