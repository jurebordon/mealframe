'use client'

import { useState, useEffect } from 'react'

type FormState = 'idle' | 'loading' | 'success' | 'error'

const LS_KEY = 'mf_waitlist_submitted'
const SYNC_EVENT = 'mf_waitlist_success'

interface WaitlistFormProps {
  size?: 'default' | 'large'
  id: string
}

export function WaitlistForm({ size = 'default', id }: WaitlistFormProps) {
  const [email, setEmail] = useState('')
  const [state, setState] = useState<FormState>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  const inputId = `${id}-email`
  const isLarge = size === 'large'

  // Hydrate success state from localStorage on mount,
  // and listen for success from other form instances on the same page
  useEffect(() => {
    try {
      if (localStorage.getItem(LS_KEY) === 'true') {
        setState('success')
      }
    } catch {
      // localStorage unavailable (SSR / private browsing) — ignore
    }

    const onSync = () => setState('success')
    window.addEventListener(SYNC_EVENT, onSync)
    return () => window.removeEventListener(SYNC_EVENT, onSync)
  }, [])

  const isValidEmail = (value: string) =>
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isValidEmail(email)) {
      setErrorMessage('Please enter a valid email address.')
      setState('error')
      return
    }

    setState('loading')
    setErrorMessage('')

    const scriptUrl = process.env.NEXT_PUBLIC_GOOGLE_SCRIPT_URL

    try {
      if (scriptUrl) {
        await fetch(scriptUrl, {
          method: 'POST',
          body: new URLSearchParams({ email }),
        })
      } else {
        await new Promise((r) => setTimeout(r, 900))
      }
      try { localStorage.setItem(LS_KEY, 'true') } catch { /* ignore */ }
      setState('success')
      setEmail('')
      window.dispatchEvent(new Event(SYNC_EVENT))
    } catch {
      setErrorMessage(
        'Submission failed. Try again or email hello@mealframe.app'
      )
      setState('error')
    }
  }

  // ── Success banner ────────────────────────────────────────────────────────
  if (state === 'success') {
    return (
      <div
        className="flex w-full items-center gap-3 rounded-md border px-5 py-4"
        style={{ borderColor: '#c47a30', background: 'rgba(196,122,48,0.10)' }}
        role="status"
        aria-live="polite"
      >
        <svg
          className="h-5 w-5 shrink-0"
          style={{ color: '#c47a30' }}
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        <p className={`font-medium ${isLarge ? 'text-base' : 'text-sm'}`} style={{ color: '#c47a30' }}>
          {"You're on the list. We'll email you when testing opens."}
        </p>
      </div>
    )
  }

  // ── Form ──────────────────────────────────────────────────────────────────
  return (
    <form onSubmit={handleSubmit} noValidate className="w-full">
      <label htmlFor={inputId} className="sr-only">
        Email address
      </label>

      <div className={`flex flex-col gap-3 sm:flex-row ${isLarge ? 'sm:gap-3' : 'sm:gap-2'}`}>
        <input
          id={inputId}
          type="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value)
            if (state === 'error') {
              setState('idle')
              setErrorMessage('')
            }
          }}
          placeholder="your@email.com"
          autoComplete="email"
          required
          disabled={state === 'loading'}
          className={`min-w-0 flex-1 rounded-md border outline-none transition-all disabled:cursor-not-allowed disabled:opacity-50 ${
            isLarge ? 'px-4 py-3 text-base' : 'px-4 py-2.5 text-sm'
          }`}
          style={{
            background: '#1a1a1a',
            color: '#f0ede8',
            borderColor:
              state === 'error'
                ? 'rgba(220,80,60,0.8)'
                : 'rgba(255,255,255,0.14)',
            boxShadow:
              state === 'error'
                ? '0 0 0 3px rgba(220,80,60,0.15)'
                : undefined,
          }}
          onFocus={(e) => {
            if (state !== 'error') {
              e.currentTarget.style.borderColor = '#c47a30'
              e.currentTarget.style.boxShadow = '0 0 0 3px rgba(196,122,48,0.18)'
            }
          }}
          onBlur={(e) => {
            if (state !== 'error') {
              e.currentTarget.style.borderColor = 'rgba(255,255,255,0.14)'
              e.currentTarget.style.boxShadow = ''
            }
          }}
        />

        <button
          type="submit"
          disabled={state === 'loading'}
          className={`shrink-0 rounded-md font-semibold transition-all disabled:cursor-not-allowed disabled:opacity-50 ${
            isLarge ? 'px-6 py-3 text-base' : 'px-5 py-2.5 text-sm'
          }`}
          style={{ background: '#c47a30', color: '#0d0c0b' }}
          onMouseEnter={(e) => {
            if (state !== 'loading') e.currentTarget.style.background = '#d48840'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#c47a30'
          }}
        >
          {state === 'loading' ? (
            <span className="flex items-center gap-2">
              <svg
                className="h-4 w-4 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle
                  className="opacity-25"
                  cx="12" cy="12" r="10"
                  stroke="currentColor" strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Joining...
            </span>
          ) : (
            'Join Waitlist'
          )}
        </button>
      </div>

      {state === 'error' && errorMessage && (
        <p
          className="mt-2.5 text-xs"
          style={{ color: '#e07060' }}
          role="alert"
          aria-live="assertive"
        >
          {errorMessage}
        </p>
      )}
    </form>
  )
}
