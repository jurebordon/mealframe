'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Calendar, UtensilsCrossed, SlidersHorizontal, TrendingUp, Moon, Sun } from 'lucide-react'
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'

const navItems = [
  { href: '/', label: 'Today', icon: Home },
  { href: '/week', label: 'Week', icon: Calendar },
  { href: '/meals', label: 'Meals', icon: UtensilsCrossed },
  { href: '/setup', label: 'Setup', icon: SlidersHorizontal },
  { href: '/stats', label: 'Stats', icon: TrendingUp },
]

export function Sidebar() {
  const pathname = usePathname()
  const [isDark, setIsDark] = useState(true)

  useEffect(() => {
    const html = document.documentElement
    setIsDark(html.classList.contains('dark'))
  }, [])

  const toggleTheme = () => {
    const html = document.documentElement
    if (html.classList.contains('dark')) {
      html.classList.remove('dark')
      setIsDark(false)
    } else {
      html.classList.add('dark')
      setIsDark(true)
    }
  }

  return (
    <aside className="hidden h-screen w-64 flex-col border-r border-border bg-card md:flex">
      {/* Logo/Brand */}
      <div className="flex h-16 items-center border-b border-border px-6">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
            <UtensilsCrossed className="h-5 w-5 text-primary" />
          </div>
          <span className="text-lg font-semibold text-foreground">MealFrame</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              }`}
            >
              <Icon className="h-5 w-5" />
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>

      {/* Theme Toggle */}
      <div className="border-t border-border p-4">
        <Button
          variant="outline"
          size="sm"
          onClick={toggleTheme}
          className="w-full justify-start gap-2 bg-transparent"
        >
          {isDark ? (
            <>
              <Sun className="h-4 w-4" />
              Light Mode
            </>
          ) : (
            <>
              <Moon className="h-4 w-4" />
              Dark Mode
            </>
          )}
        </Button>
      </div>
    </aside>
  )
}
