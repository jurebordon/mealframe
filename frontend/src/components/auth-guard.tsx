'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/auth-store'
import { Spinner } from '@/components/ui/spinner'

interface AuthGuardProps {
  children: React.ReactNode
}

/**
 * Wraps protected routes. On mount, tries to restore the session
 * from the refresh token cookie. Redirects to /login if no valid session.
 */
export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter()
  const { user, isLoading, isInitialized, initialize } = useAuthStore()

  useEffect(() => {
    initialize()
  }, [initialize])

  useEffect(() => {
    if (isInitialized && !user) {
      router.replace('/login')
    }
  }, [isInitialized, user, router])

  // Show loading spinner while checking auth
  if (!isInitialized || isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <Spinner className="size-8 text-muted-foreground" />
      </div>
    )
  }

  // Not authenticated — will redirect, show nothing
  if (!user) {
    return null
  }

  return <>{children}</>
}
