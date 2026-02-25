import { Providers } from '@/components/providers'
import { AppShell } from '@/components/navigation/app-shell'
import { OfflineBanner } from '@/components/mealframe/offline-banner'

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <Providers>
      <OfflineBanner />
      <AppShell>
        {children}
      </AppShell>
    </Providers>
  )
}
