import { Providers } from '@/components/providers'
import { AuthGuard } from '@/components/auth-guard'
import { AppShell } from '@/components/navigation/app-shell'
import { OfflineBanner } from '@/components/mealframe/offline-banner'

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <Providers>
      <AuthGuard>
        <OfflineBanner />
        <AppShell>
          {children}
        </AppShell>
      </AuthGuard>
    </Providers>
  )
}
