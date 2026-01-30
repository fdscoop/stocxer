'use client'

import * as React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Menu, TrendingUp, X, LogOut, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: '📊' },
  { name: 'Stock Screener', href: '/screener', icon: '🔍' },
  { name: 'Index Analyzer', href: '/analyzer', icon: '📈' },
  { name: 'Options Scanner', href: '/options', icon: '🎯' },
  { name: 'Paper Trading', href: '/paper-trading', icon: '🤖' },
  { name: 'AI Integration', href: '/mcp', icon: '🧠' },
  { name: 'Subscription', href: '/subscription', icon: '⭐' },
  { name: 'Billing & Credits', href: '/billing', icon: '💳' },
]

const indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX', 'BANKEX']

interface HeaderProps {
  user?: { email: string } | null
  selectedIndex?: string
  onIndexChange?: (index: string) => void
  onLogout?: () => void
}

export function Header({ user, selectedIndex = 'NIFTY', onIndexChange, onLogout }: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false)
  const pathname = usePathname()

  return (
    <>
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4">
          <div className="flex h-14 md:h-16 items-center justify-between">
            {/* Left: Mobile menu + Logo */}
            <div className="flex items-center gap-2 md:gap-4">
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden"
                onClick={() => setMobileMenuOpen(true)}
              >
                <Menu className="h-5 w-5" />
              </Button>
              
              <Link href="/" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-primary-foreground" />
                </div>
                <span className="text-lg md:text-xl font-bold">TradeWise</span>
              </Link>

              {/* Desktop Index Tabs */}
              <div className="hidden lg:flex gap-1 ml-6">
                {indices.map((index) => (
                  <button
                    key={index}
                    onClick={() => onIndexChange?.(index)}
                    className={cn(
                      'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                      selectedIndex === index
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                    )}
                  >
                    {index}
                  </button>
                ))}
              </div>
            </div>

            {/* Center: Mobile Index Display */}
            <div className="flex md:hidden items-center gap-2">
              <span className="text-sm font-semibold text-primary">{selectedIndex}</span>
              <span className="w-2 h-2 bg-bullish rounded-full animate-pulse" />
            </div>

            {/* Right: Desktop Nav + User */}
            <div className="hidden md:flex items-center gap-4">
              <nav className="flex items-center gap-2">
                {navigation.slice(1).map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'px-3 py-2 text-sm font-medium rounded-md transition-colors',
                      pathname === item.href
                        ? 'bg-muted text-foreground'
                        : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                    )}
                  >
                    <span className="mr-1">{item.icon}</span>
                    {item.name}
                  </Link>
                ))}
              </nav>

              {user ? (
                <div className="flex items-center gap-3 border-l pl-4">
                  <div className="text-right">
                    <div className="text-xs text-muted-foreground">Logged in as</div>
                    <div className="text-sm font-medium">{user.email}</div>
                  </div>
                  <Button variant="destructive" size="sm" onClick={onLogout}>
                    <LogOut className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <Link href="/login">
                  <Button size="sm">Login</Button>
                </Link>
              )}

              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span className="w-2 h-2 bg-bullish rounded-full animate-pulse" />
                <span>Live</span>
              </div>
            </div>
          </div>

          {/* Mobile Index Tabs (scrollable) */}
          <div className="md:hidden overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
            <div className="flex gap-1 min-w-max">
              {indices.map((index) => (
                <button
                  key={index}
                  onClick={() => onIndexChange?.(index)}
                  className={cn(
                    'px-3 py-1.5 text-xs font-medium rounded-md whitespace-nowrap transition-colors',
                    selectedIndex === index
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground bg-muted'
                  )}
                >
                  {index}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div 
            className="fixed inset-0 bg-black/80" 
            onClick={() => setMobileMenuOpen(false)} 
          />
          <div className="fixed left-0 top-0 bottom-0 w-[85%] max-w-[320px] bg-background p-6 shadow-xl">
            <div className="flex items-center justify-between mb-8">
              <Link href="/" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-primary-foreground" />
                </div>
                <span className="text-xl font-bold">TradeWise</span>
              </Link>
              <Button variant="ghost" size="icon" onClick={() => setMobileMenuOpen(false)}>
                <X className="h-5 w-5" />
              </Button>
            </div>

            <nav className="space-y-2">
              {navigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors',
                    pathname === item.href
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                  )}
                >
                  <span className="text-lg">{item.icon}</span>
                  {item.name}
                </Link>
              ))}
            </nav>

            <div className="mt-6 pt-6 border-t">
              <div className="text-xs text-muted-foreground uppercase mb-3">Select Index</div>
              <div className="grid grid-cols-2 gap-2">
                {indices.map((index) => (
                  <button
                    key={index}
                    onClick={() => {
                      onIndexChange?.(index)
                      setMobileMenuOpen(false)
                    }}
                    className={cn(
                      'px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                      selectedIndex === index
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground hover:text-foreground'
                    )}
                  >
                    {index}
                  </button>
                ))}
              </div>
            </div>

            {user ? (
              <div className="mt-6 pt-6 border-t">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-muted rounded-full flex items-center justify-center">
                    <User className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-sm font-medium">{user.email}</div>
                    <div className="text-xs text-muted-foreground">Logged in</div>
                  </div>
                </div>
                <Button variant="destructive" className="w-full" onClick={onLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </Button>
              </div>
            ) : (
              <div className="mt-6 pt-6 border-t">
                <Link href="/login" onClick={() => setMobileMenuOpen(false)}>
                  <Button className="w-full">Login</Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
