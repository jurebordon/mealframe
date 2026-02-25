import type { Metadata } from 'next'
import { GeistSans } from 'geist/font/sans'

const FALLBACK_URL = 'https://mealframe.app'
const siteUrl =
  process.env.NEXT_PUBLIC_SITE_URL?.startsWith('http')
    ? process.env.NEXT_PUBLIC_SITE_URL
    : FALLBACK_URL

export const metadata: Metadata = {
  title: 'MealFrame — Plan when calm, follow when stressed',
  description:
    'MealFrame eliminates food decisions with exact meal portions and structured weekly plans. Beat evening overeating without willpower. Join the early access waitlist.',
  metadataBase: new URL(siteUrl),
  alternates: { canonical: siteUrl },
  openGraph: {
    type: 'website',
    url: siteUrl,
    title: 'MealFrame — Plan when calm, follow when stressed',
    description:
      'MealFrame eliminates food decisions with exact meal portions and structured weekly plans. Beat evening overeating without willpower. Join the early access waitlist.',
    images: [{ url: '/og-image.jpg', width: 1200, height: 630 }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'MealFrame — Plan when calm, follow when stressed',
    description:
      'MealFrame eliminates food decisions with exact meal portions and structured weekly plans. Beat evening overeating without willpower. Join the early access waitlist.',
  },
}

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className={GeistSans.className}>
      {children}
    </div>
  )
}
