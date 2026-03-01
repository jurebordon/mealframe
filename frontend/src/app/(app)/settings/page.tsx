'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/auth-store'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LogOut, User, Shield } from 'lucide-react'

export default function SettingsPage() {
  const router = useRouter()
  const { user, logout } = useAuthStore()
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  const handleLogout = async () => {
    setIsLoggingOut(true)
    await logout()
    router.push('/login')
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-6">
      <h1 className="text-2xl font-semibold">Settings</h1>

      {/* Profile */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <User className="h-4 w-4" />
            Profile
          </CardTitle>
          <CardDescription>Your account information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="text-sm text-muted-foreground">Email</p>
            <p className="text-sm font-medium">{user?.email}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Auth provider</p>
            <p className="text-sm font-medium capitalize">{user?.auth_provider || 'email'}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Member since</p>
            <p className="text-sm font-medium">
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })
                : '—'}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Security */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Shield className="h-4 w-4" />
            Security
          </CardTitle>
          <CardDescription>Manage your session</CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="destructive"
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="gap-2"
          >
            <LogOut className="h-4 w-4" />
            {isLoggingOut ? 'Signing out...' : 'Sign out'}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
