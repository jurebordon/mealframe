import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'MealFrame',
  description: 'Meal planning that eliminates decision fatigue',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
