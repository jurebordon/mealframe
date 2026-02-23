'use client'

import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import type React from 'react'

export type MealCardStatus = 'default' | 'next' | 'completed' | 'skipped'

interface MealCardProps {
  mealName: string
  portionDescription: string
  mealType: string
  calories?: number
  protein?: number
  carbs?: number
  sugar?: number
  fat?: number
  saturatedFat?: number
  fiber?: number
  status?: MealCardStatus
  completionStatus?: 'followed' | 'equivalent' | 'skipped' | 'deviated' | 'social'
  className?: string
  onClick?: () => void
}

export function MealCard({
  mealName,
  portionDescription,
  mealType,
  calories,
  protein,
  carbs,
  sugar,
  fat,
  saturatedFat,
  fiber,
  status = 'default',
  completionStatus,
  className,
  onClick,
}: MealCardProps) {
  const statusStyles = {
    default: 'bg-card border-border',
    next: 'bg-card border-primary shadow-lg ring-2 ring-primary/20',
    completed: 'bg-card border-border opacity-60',
    skipped: 'bg-card border-border opacity-40',
  }

  return (
    <div
      className={cn(
        'rounded-lg border p-6 transition-all duration-200',
        statusStyles[status],
        onClick && 'cursor-pointer hover:shadow-md',
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-3">
          {/* Meal Type Badge */}
          <Badge variant="outline" className="text-xs font-normal text-muted-foreground">
            {mealType}
          </Badge>

          {/* Meal Name */}
          <h3 className="text-balance text-xl font-semibold leading-tight text-card-foreground">
            {mealName}
          </h3>

          {/* Portion Description - The Key Info */}
          <p className="text-pretty text-base leading-relaxed text-foreground/90">
            {portionDescription}
          </p>

          {/* Macros Row - Subtle, Secondary */}
          {(calories || protein || carbs || fat) && (
            <div className="flex flex-wrap gap-x-4 gap-y-1 pt-2 text-sm text-muted-foreground">
              {calories != null && <span>{calories} kcal</span>}
              {protein != null && <span>{protein}g protein</span>}
              {carbs != null && <span>{carbs}g carbs</span>}
              {sugar != null && <span>{sugar}g sugar</span>}
              {fat != null && <span>{fat}g fat</span>}
              {saturatedFat != null && <span>{saturatedFat}g sat. fat</span>}
              {fiber != null && <span>{fiber}g fiber</span>}
            </div>
          )}
        </div>

        {/* Completion Status Indicator */}
        {completionStatus && (
          <div className="flex-shrink-0">
            {completionStatus === 'followed' && (
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-success text-success-foreground">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  className="h-4 w-4"
                >
                  <path
                    fillRule="evenodd"
                    d="M12.416 3.376a.75.75 0 0 1 .208 1.04l-5 7.5a.75.75 0 0 1-1.154.114l-3-3a.75.75 0 0 1 1.06-1.06l2.353 2.353 4.493-6.74a.75.75 0 0 1 1.04-.207Z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            )}
            {completionStatus === 'equivalent' && (
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-warning text-warning-foreground">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  className="h-4 w-4"
                >
                  <path d="M8.75 3.75a.75.75 0 0 0-1.5 0v3.5h-3.5a.75.75 0 0 0 0 1.5h3.5v3.5a.75.75 0 0 0 1.5 0v-3.5h3.5a.75.75 0 0 0 0-1.5h-3.5v-3.5Z" />
                </svg>
              </div>
            )}
            {(completionStatus === 'skipped' || completionStatus === 'deviated') && (
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-muted text-muted-foreground">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  className="h-4 w-4"
                >
                  <path d="M5.28 4.22a.75.75 0 0 0-1.06 1.06L6.94 8l-2.72 2.72a.75.75 0 1 0 1.06 1.06L8 9.06l2.72 2.72a.75.75 0 1 0 1.06-1.06L9.06 8l2.72-2.72a.75.75 0 0 0-1.06-1.06L8 6.94 5.28 4.22Z" />
                </svg>
              </div>
            )}
            {completionStatus === 'social' && (
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  className="h-3.5 w-3.5"
                >
                  <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM12.5 16h.5a2 2 0 0 0 2-2v-.5a2.5 2.5 0 0 0-2.5-2.5h-3v5ZM3.5 11A2.5 2.5 0 0 0 1 13.5v.5a2 2 0 0 0 2 2h.5v-5h-3Z" />
                </svg>
              </div>
            )}
          </div>
        )}
      </div>

      {status === 'next' && (
        <div className="mt-4 flex items-center gap-2 text-sm font-medium text-primary">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 16 16"
            fill="currentColor"
            className="h-4 w-4"
          >
            <path
              fillRule="evenodd"
              d="M8 14A6 6 0 1 0 8 2a6 6 0 0 0 0 12Zm.75-8.25a.75.75 0 0 0-1.5 0V8c0 .414.336.75.75.75h2a.75.75 0 0 0 0-1.5h-1.25V5.75Z"
              clipRule="evenodd"
            />
          </svg>
          <span>Next meal</span>
        </div>
      )}
    </div>
  )
}
