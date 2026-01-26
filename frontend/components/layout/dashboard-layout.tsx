'use client'

import * as React from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Menu, TrendingUp, X, ArrowLeft, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Sidebar, MobileNavigation } from './sidebar'
import { cn } from '@/lib/utils'

const indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX', 'BANKEX']

const navigation = [
  { name: 'Dashboard', href: '/', icon: '📊' },
  { name: 'Stock Screener', href: '/screener', icon: '🔍' },
  { name: 'Index Analyzer', href: '/analyzer', icon: '📈' },
  { name: 'Options Scanner', href: '/options', icon: '🎯' },
  { name: 'AI Integration', href: '/mcp', icon: '🤖' },
  { name: 'Subscription', href: '/subscription', icon: '⭐' },
  { name: 'Billing & Credits', href: '/billing', icon: '💳' },
]

interface DashboardLayoutProps {
  children: React.ReactNode
  user?: { email: string } | null
  selectedIndex?: string
  onIndexChange?: (index: string) => void
  onLogout?: () => void
  showBackButton?: boolean
  pageTitle?: string
  showIndexSelector?: boolean
}

export function DashboardLayout({ 
  children, 
  user, 
  selectedIndex = 'NIFTY', 
  onIndexChange, 
  onLogout,
  showBackButton = true,
  pageTitle,
  showIndexSelector = true
}: DashboardLayoutProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false)
  const pathname = usePathname()
  const router = useRouter()

  // Persist sidebar collapsed state
  React.useEffect(() => {
    const saved = localStorage.getItem('sidebar_collapsed')
    if (saved !== null) {
      setSidebarCollapsed(JSON.parse(saved))
    }
  }, [])

  const toggleSidebarCollapse = () => {
    const newState = !sidebarCollapsed
    setSidebarCollapsed(newState)
    localStorage.setItem('sidebar_collapsed', JSON.stringify(newState))
  }

  const isHomePage = pathname === '/'

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <Sidebar 
        user={user}
        onLogout={onLogout}
        collapsed={sidebarCollapsed}
        onToggleCollapse={toggleSidebarCollapse}
      />

      {/* Mobile Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 md:hidden">
        <div className="px-4">
          <div className="flex h-14 items-center justify-between">
            {/* Left: Menu + Back or Logo */}
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setMobileMenuOpen(true)}
              >
                <Menu className="h-5 w-5" />
              </Button>
              
              {showBackButton && !isHomePage ? (
                <Button
                  variant="ghost"
                  size="sm"
                  className="gap-1"
                  onClick={() => router.back()}
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </Button>
              ) : (
                <Link href="/" className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-primary-foreground" />
                  </div>
                  <span className="text-lg font-bold">TradeWise</span>
                </Link>
              )}
            </div>

            {/* Right: Index + Live indicator */}
            <div className="flex items-center gap-2">
              {showIndexSelector && (
                <span className="text-sm font-semibold text-primary">{selectedIndex}</span>
              )}
              <span className="w-2 h-2 bg-bullish rounded-full animate-pulse" />
            </div>
          </div>

          {/* Mobile Index Tabs (scrollable) */}
          {showIndexSelector && (
            <div className="overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
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
          )}
        </div>
      </header>

      {/* Desktop Top Bar */}
      <header className={cn(
        "hidden md:flex sticky top-0 z-30 h-16 items-center justify-between border-b border-border bg-background/95 backdrop-blur px-6 transition-all duration-300",
        sidebarCollapsed ? "ml-[70px]" : "ml-[260px]"
      )}>
        <div className="flex items-center gap-4">
          {/* Back Button */}
          {showBackButton && !isHomePage && (
            <Button
              variant="ghost"
              size="sm"
              className="gap-1"
              onClick={() => router.back()}
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
          )}
          
          {/* Page Title */}
          {pageTitle && (
            <h1 className="text-lg font-semibold">{pageTitle}</h1>
          )}
          
          {/* Index Selector */}
          {showIndexSelector && (
            <div className="flex gap-1 ml-2">
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
          )}
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="w-2 h-2 bg-bullish rounded-full animate-pulse" />
            <span>Live</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className={cn(
        "transition-all duration-300 pb-20 md:pb-0",
        sidebarCollapsed ? "md:ml-[70px]" : "md:ml-[260px]"
      )}>
        {children}
      </main>

      {/* Mobile Bottom Navigation */}
      <MobileNavigation />

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
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

            {showIndexSelector && (
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
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// Export a simple back button component for use in page headers
export function BackButton({ className }: { className?: string }) {
  const router = useRouter()
  
  return (
    <Button
      variant="ghost"
      size="sm"
      className={cn("gap-1", className)}
      onClick={() => router.back()}
    >
      <ArrowLeft className="h-4 w-4" />
      Back
    </Button>
  )
}
