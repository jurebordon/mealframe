'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { CompletionSheetAnimated } from './completion-sheet-animated'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, X, MoreHorizontal, Sparkles } from 'lucide-react'

interface UnmarkedMeal {
  id: string
  name: string
  portion: string
  time: string
  type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
}

interface YesterdayReviewProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  unmarkedMeals: UnmarkedMeal[]
  onMealComplete: (mealId: string, status: 'followed' | 'skipped' | 'equivalent' | 'deviated' | 'social') => void
  onDismiss: () => void
}

export function YesterdayReview({
  open,
  onOpenChange,
  unmarkedMeals: initialMeals,
  onMealComplete,
  onDismiss,
}: YesterdayReviewProps) {
  const [unmarkedMeals, setUnmarkedMeals] = useState(initialMeals)
  const [completingMealId, setCompletingMealId] = useState<string | null>(null)
  const [showCompletionSheet, setShowCompletionSheet] = useState(false)
  const [selectedMealId, setSelectedMealId] = useState<string | null>(null)
  const [showCelebration, setShowCelebration] = useState(false)

  useEffect(() => {
    setUnmarkedMeals(initialMeals)
  }, [initialMeals])

  const totalMeals = initialMeals.length
  const remainingCount = unmarkedMeals.length

  const handleQuickComplete = (mealId: string, status: 'followed' | 'skipped') => {
    setCompletingMealId(mealId)

    // Micro-animation delay
    setTimeout(() => {
      setUnmarkedMeals((prev) => prev.filter((m) => m.id !== mealId))
      onMealComplete(mealId, status)
      setCompletingMealId(null)

      // Check if all done
      if (unmarkedMeals.length === 1) {
        // Last meal - show celebration
        setShowCelebration(true)
        setTimeout(() => {
          setShowCelebration(false)
          onOpenChange(false)
        }, 1500)
      }
    }, 300)
  }

  const handleMoreOptions = (mealId: string) => {
    setSelectedMealId(mealId)
    setShowCompletionSheet(true)
  }

  const handleCompletionSelect = (status: 'followed' | 'equivalent' | 'skipped' | 'deviated' | 'social') => {
    if (selectedMealId) {
      setCompletingMealId(selectedMealId)
      setShowCompletionSheet(false)

      setTimeout(() => {
        setUnmarkedMeals((prev) => prev.filter((m) => m.id !== selectedMealId))
        onMealComplete(selectedMealId, status)
        setCompletingMealId(null)

        // Check if all done
        if (unmarkedMeals.length === 1) {
          setShowCelebration(true)
          setTimeout(() => {
            setShowCelebration(false)
            onOpenChange(false)
          }, 1500)
        }
      }, 300)
    }
  }

  const handleMarkAllFollowed = () => {
    const mealIds = unmarkedMeals.map((m) => m.id)
    
    // Animate all meals out
    mealIds.forEach((id, index) => {
      setTimeout(() => {
        setCompletingMealId(id)
        setTimeout(() => {
          setUnmarkedMeals((prev) => prev.filter((m) => m.id !== id))
          onMealComplete(id, 'followed')
          setCompletingMealId(null)

          // Show celebration after last meal
          if (index === mealIds.length - 1) {
            setShowCelebration(true)
            setTimeout(() => {
              setShowCelebration(false)
              onOpenChange(false)
            }, 1500)
          }
        }, 300)
      }, index * 150)
    })
  }

  const handleDismissClick = () => {
    onDismiss()
    onOpenChange(false)
  }

  const selectedMeal = unmarkedMeals.find((m) => m.id === selectedMealId)

  return (
    <>
      <AnimatePresence>
        {open && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={handleDismissClick}
              className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
            />

            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.95 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed inset-x-4 top-1/2 z-50 mx-auto max-w-md -translate-y-1/2 rounded-2xl border border-border bg-card p-6 shadow-2xl"
            >
              {/* Header */}
              <div className="mb-6">
                <h2 className="mb-2 text-2xl font-bold text-foreground">
                  {remainingCount === 1 ? 'Quick check-in' : "Yesterday's meals"}
                </h2>
                <p className="text-sm text-muted-foreground">
                  You have {remainingCount} unmarked {remainingCount === 1 ? 'meal' : 'meals'} from
                  yesterday
                </p>
              </div>

              {/* Progress Indicator */}
              {totalMeals > 1 && (
                <div className="mb-4">
                  <div className="mb-2 flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">
                      {totalMeals - remainingCount} of {totalMeals} completed
                    </span>
                    <span className="font-medium text-primary">
                      {remainingCount} remaining
                    </span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{
                        width: `${((totalMeals - remainingCount) / totalMeals) * 100}%`,
                      }}
                      transition={{ type: 'spring', damping: 20, stiffness: 100 }}
                      className="h-full bg-primary"
                    />
                  </div>
                </div>
              )}

              {/* Meal List */}
              <div className="mb-6 max-h-[400px] space-y-3 overflow-y-auto">
                <AnimatePresence mode="popLayout">
                  {unmarkedMeals.map((meal) => (
                    <motion.div
                      key={meal.id}
                      layout
                      initial={{ opacity: 0, x: -20 }}
                      animate={{
                        opacity: completingMealId === meal.id ? 0.5 : 1,
                        x: 0,
                        scale: completingMealId === meal.id ? 0.95 : 1,
                      }}
                      exit={{ opacity: 0, x: 20, height: 0, marginBottom: 0 }}
                      transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                      className="rounded-xl border border-border bg-background p-4"
                    >
                      <div className="mb-3 flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <h3 className="mb-1 text-base font-semibold text-foreground">
                            {meal.name}
                          </h3>
                          <p className="mb-1 text-sm text-muted-foreground">{meal.time}</p>
                          <p className="text-sm leading-relaxed text-foreground/80">
                            {meal.portion}
                          </p>
                        </div>
                      </div>

                      {/* Quick Actions */}
                      <div className="flex gap-2">
                        <Button
                          variant="default"
                          size="sm"
                          className="flex-1"
                          onClick={() => handleQuickComplete(meal.id, 'followed')}
                          disabled={completingMealId === meal.id}
                        >
                          <Check className="mr-1.5 h-4 w-4" />
                          Followed
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1 bg-transparent"
                          onClick={() => handleQuickComplete(meal.id, 'skipped')}
                          disabled={completingMealId === meal.id}
                        >
                          <X className="mr-1.5 h-4 w-4" />
                          Skipped
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleMoreOptions(meal.id)}
                          disabled={completingMealId === meal.id}
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>

              {/* Actions */}
              <div className="space-y-2">
                {remainingCount > 1 && (
                  <Button
                    variant="default"
                    size="lg"
                    className="w-full"
                    onClick={handleMarkAllFollowed}
                  >
                    Mark all as Followed
                  </Button>
                )}
                <Button
                  variant="outline"
                  size="lg"
                  className="w-full bg-transparent"
                  onClick={handleDismissClick}
                >
                  Skip for now
                </Button>
              </div>
            </motion.div>

            {/* Celebration Overlay */}
            <AnimatePresence>
              {showCelebration && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="fixed inset-0 z-[60] flex items-center justify-center bg-background/80 backdrop-blur-sm"
                >
                  <motion.div
                    initial={{ scale: 0, rotate: -180 }}
                    animate={{ scale: 1, rotate: 0 }}
                    exit={{ scale: 0, rotate: 180 }}
                    transition={{ type: 'spring', damping: 15, stiffness: 200 }}
                    className="flex flex-col items-center gap-4"
                  >
                    <div className="flex h-20 w-20 items-center justify-center rounded-full bg-success/20">
                      <Check className="h-10 w-10 text-success" strokeWidth={3} />
                    </div>
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.2 }}
                      className="text-center"
                    >
                      <h3 className="text-2xl font-bold text-foreground">All caught up!</h3>
                      <p className="text-sm text-muted-foreground">Great job staying consistent</p>
                    </motion.div>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
      </AnimatePresence>

      {/* Completion Sheet for "More Options" */}
      <CompletionSheetAnimated
        open={showCompletionSheet}
        onOpenChange={setShowCompletionSheet}
        onSelect={handleCompletionSelect}
        mealName={selectedMeal?.name || ''}
      />
    </>
  )
}
