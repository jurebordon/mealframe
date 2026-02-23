'use client'

import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface CompletionAnimationProps {
  show: boolean
  type: 'followed' | 'equivalent' | 'skipped' | 'deviated' | 'social'
}

export function CompletionAnimation({ show, type }: CompletionAnimationProps) {
  const isCelebration = type === 'followed'

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="pointer-events-none fixed inset-0 z-[100] flex items-center justify-center"
        >
          {/* Glow effect */}
          {isCelebration && (
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 2, opacity: [0, 0.3, 0] }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
              className="absolute h-64 w-64 rounded-full bg-success blur-3xl"
            />
          )}

          {/* Main icon animation */}
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{
              type: 'spring',
              damping: 12,
              stiffness: 200,
            }}
            className={`flex h-24 w-24 items-center justify-center rounded-full ${
              isCelebration
                ? 'bg-success/20 text-success'
                : type === 'equivalent'
                  ? 'bg-warning/20 text-warning'
                  : 'bg-muted text-muted-foreground'
            }`}
          >
            {type === 'followed' && (
              <motion.svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 16 16"
                fill="currentColor"
                className="h-12 w-12"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.5, ease: 'easeInOut' }}
              >
                <motion.path
                  fillRule="evenodd"
                  d="M12.416 3.376a.75.75 0 0 1 .208 1.04l-5 7.5a.75.75 0 0 1-1.154.114l-3-3a.75.75 0 0 1 1.06-1.06l2.353 2.353 4.493-6.74a.75.75 0 0 1 1.04-.207Z"
                  clipRule="evenodd"
                />
              </motion.svg>
            )}

            {type === 'equivalent' && (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 16 16"
                fill="currentColor"
                className="h-12 w-12"
              >
                <path
                  fillRule="evenodd"
                  d="M8 15A7 7 0 1 0 8 1a7 7 0 0 0 0 14Zm.75-10.25a.75.75 0 0 0-1.5 0v4.69L6.03 8.22a.75.75 0 0 0-1.06 1.06l2.5 2.5a.75.75 0 0 0 1.06 0l2.5-2.5a.75.75 0 1 0-1.06-1.06l-1.22 1.22V4.75Z"
                  clipRule="evenodd"
                />
              </svg>
            )}

            {type === 'skipped' && (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 16 16"
                fill="currentColor"
                className="h-12 w-12"
              >
                <path
                  fillRule="evenodd"
                  d="M5.28 4.22a.75.75 0 0 0-1.06 1.06L6.94 8l-2.72 2.72a.75.75 0 1 0 1.06 1.06L8 9.06l2.72 2.72a.75.75 0 1 0 1.06-1.06L9.06 8l2.72-2.72a.75.75 0 0 0-1.06-1.06L8 6.94 5.28 4.22Z"
                  clipRule="evenodd"
                />
              </svg>
            )}

            {type === 'deviated' && (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 16 16"
                fill="currentColor"
                className="h-12 w-12"
              >
                <path
                  fillRule="evenodd"
                  d="M13.836 2.477a.75.75 0 0 1 .75.75v3.182a.75.75 0 0 1-.75.75h-3.182a.75.75 0 0 1 0-1.5h1.37L9.74 3.378a.75.75 0 0 1 1.06-1.06l2.281 2.28V3.227a.75.75 0 0 1 .75-.75Zm-2.551 7.5a.75.75 0 0 1 0 1.06l-2.28 2.28v-1.37a.75.75 0 0 0-1.5 0v3.182c0 .414.336.75.75.75h3.182a.75.75 0 0 0 0-1.5h-1.37l2.28-2.28a.75.75 0 0 0-1.06-1.06Z"
                  clipRule="evenodd"
                />
              </svg>
            )}

            {type === 'social' && (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 16 16"
                fill="currentColor"
                className="h-12 w-12"
              >
                <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM12.735 14c.618 0 1.093-.561.872-1.139a6.002 6.002 0 0 0-11.215 0c-.22.578.254 1.139.872 1.139h9.47Z" />
              </svg>
            )}
          </motion.div>

          {/* Particle burst for celebration */}
          {isCelebration && (
            <>
              {[...Array(8)].map((_, i) => (
                <motion.div
                  key={i}
                  initial={{
                    x: 0,
                    y: 0,
                    scale: 0,
                    opacity: 1,
                  }}
                  animate={{
                    x: Math.cos((i * Math.PI * 2) / 8) * 120,
                    y: Math.sin((i * Math.PI * 2) / 8) * 120,
                    scale: [0, 1, 0],
                    opacity: [1, 1, 0],
                  }}
                  transition={{
                    duration: 0.8,
                    ease: 'easeOut',
                  }}
                  className="absolute h-2 w-2 rounded-full bg-success"
                />
              ))}
            </>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}
