'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuthStore } from '@/lib/auth-store'
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react'

function VerifyEmailContent() {
  const searchParams = useSearchParams()
  const token = searchParams.get('token')
  const verifyEmail = useAuthStore((s) => s.verifyEmail)

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      setMessage('No verification token provided.')
      return
    }

    let cancelled = false
    verifyEmail(token)
      .then((msg) => {
        if (!cancelled) {
          setStatus('success')
          setMessage(msg)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setStatus('error')
          setMessage(err instanceof Error ? err.message : 'Verification failed')
        }
      })

    return () => {
      cancelled = true
    }
  }, [token, verifyEmail])

  return (
    <Card className="select-auto">
      <CardHeader className="text-center">
        {status === 'loading' && (
          <>
            <div className="mx-auto mb-2">
              <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" />
            </div>
            <CardTitle className="text-xl">Verifying your email...</CardTitle>
          </>
        )}
        {status === 'success' && (
          <>
            <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-green-500/10">
              <CheckCircle2 className="h-6 w-6 text-green-500" />
            </div>
            <CardTitle className="text-xl">Email verified</CardTitle>
            <CardDescription>{message}</CardDescription>
          </>
        )}
        {status === 'error' && (
          <>
            <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
              <XCircle className="h-6 w-6 text-destructive" />
            </div>
            <CardTitle className="text-xl">Verification failed</CardTitle>
            <CardDescription>{message}</CardDescription>
          </>
        )}
      </CardHeader>
      {status !== 'loading' && (
        <CardFooter className="justify-center">
          <Button asChild>
            <Link href="/login">Go to sign in</Link>
          </Button>
        </CardFooter>
      )}
    </Card>
  )
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <Card className="select-auto">
          <CardHeader className="text-center">
            <div className="mx-auto mb-2">
              <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" />
            </div>
            <CardTitle className="text-xl">Loading...</CardTitle>
          </CardHeader>
        </Card>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  )
}
