'use client'

import { Suspense, useEffect, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuthStore } from '@/lib/auth-store'
import { Loader2 } from 'lucide-react'

function OAuthCallbackHandler() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const handleOAuthCallback = useAuthStore((s) => s.handleOAuthCallback)
  const processed = useRef(false)

  useEffect(() => {
    if (processed.current) return
    processed.current = true

    const token = searchParams.get('token')
    const error = searchParams.get('error')

    if (error) {
      const messages: Record<string, string> = {
        exchange_failed: 'Google sign-in failed. Please try again.',
        account_disabled: 'Your account has been disabled.',
      }
      router.replace(`/login?error=${encodeURIComponent(messages[error] || 'Sign-in failed')}`)
      return
    }

    if (!token) {
      router.replace('/login?error=Missing+authentication+token')
      return
    }

    handleOAuthCallback(token)
      .then(() => router.replace('/'))
      .catch(() => router.replace('/login?error=Sign-in+failed'))
  }, [searchParams, router, handleOAuthCallback])

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
    </div>
  )
}

export default function OAuthCallbackPage() {
  return (
    <Suspense>
      <OAuthCallbackHandler />
    </Suspense>
  )
}
