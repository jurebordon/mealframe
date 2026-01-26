'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Calendar, UtensilsCrossed, SlidersHorizontal, TrendingUp } from 'lucide-react'

const navItems = [
  { href: '/', label: 'Today', icon: Home },
  { href: '/week', label: 'Week', icon: Calendar },
  { href: '/meals', label: 'Meals', icon: UtensilsCrossed },
  { href: '/setup', label: 'Setup', icon: SlidersHorizontal },
  { href: '/stats', label: 'Stats', icon: TrendingUp },
]

export function BottomNav() {
  const pathname = usePathname()

  return (
    <nav 
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80 md:hidden"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="mx-auto flex max-w-screen-sm items-stretch justify-around px-2 pb-safe">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex min-h-[64px] min-w-0 flex-1 flex-col items-center justify-center gap-1 rounded-lg px-2 py-2 transition-colors active:scale-95 ${
                isActive
                  ? 'text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
              aria-label={`${item.label}${isActive ? ', current tab' : ''}`}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon className={`h-6 w-6 ${isActive ? 'fill-primary/20' : ''}`} strokeWidth={isActive ? 2.5 : 2} />
              <span className="text-xs font-medium leading-tight">{item.label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
