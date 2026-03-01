'use client'

import React from "react"
import Link from "next/link"
import { Settings } from "lucide-react"

import { BottomNav } from './bottom-nav'
import { Sidebar } from './sidebar'

interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-background pt-safe">
      {/* Desktop Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="flex flex-1 flex-col overflow-y-auto pb-16 md:pb-0" role="main">
        {/* Mobile top bar — settings link (hidden on desktop where sidebar has it) */}
        <div className="flex items-center justify-end px-4 py-2 md:hidden">
          <Link
            href="/settings"
            className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label="Settings"
          >
            <Settings className="h-5 w-5" />
          </Link>
        </div>
        {children}
      </main>

      {/* Mobile Bottom Nav */}
      <BottomNav />
    </div>
  )
}
