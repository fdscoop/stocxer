'use client'

import * as React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  TrendingUp, 
  LayoutDashboard, 
  Search, 
  BarChart3, 
  Target, 
  Bot, 
  CreditCard, 
  Star,
  ChevronLeft,
  ChevronRight,
  LogOut,
  User,
  Activity
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, description: 'Overview & latest scans' },
  { name: 'Stock Screener', href: '/screener', icon: Search, description: 'Scan stocks for signals' },
  { name: 'Index Analyzer', href: '/analyzer', icon: BarChart3, description: 'Deep option chain analysis' },
  { name: 'Options Scanner', href: '/options', icon: Target, description: 'Find optimal options' },
  { name: 'Paper Trading', href: '/paper-trading', icon: Activity, description: 'Automated paper trading', beta: true },
  { name: 'AI Integration', href: '/mcp', icon: Bot, description: 'Connect with AI assistants (Beta)', beta: true },
  { name: 'Subscription', href: '/subscription', icon: Star, description: 'Manage your plan' },
  { name: 'Billing & Credits', href: '/billing', icon: CreditCard, description: 'View usage & credits' },
]

interface SidebarProps {
  user?: { email: string } | null
  onLogout?: () => void
  collapsed?: boolean
  onToggleCollapse?: () => void
}

export function Sidebar({ user, onLogout, collapsed = false, onToggleCollapse }: SidebarProps) {
  const pathname = usePathname()

  return (
    <TooltipProvider delayDuration={0}>
      <aside 
        className={cn(
          "fixed left-0 top-0 z-40 h-screen border-r border-border bg-background/95 backdrop-blur transition-all duration-300 ease-in-out",
          "hidden md:flex md:flex-col",
          collapsed ? "w-[70px]" : "w-[260px]"
        )}
      >
        {/* Logo Section */}
        <div className={cn(
          "flex h-16 items-center border-b border-border px-4",
          collapsed ? "justify-center" : "justify-between"
        )}>
          <Link href="/" className="flex items-center gap-2">
            <div className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
              <TrendingUp className="w-5 h-5 text-primary-foreground" />
            </div>
            {!collapsed && (
              <span className="text-xl font-bold tracking-tight">TradeWise</span>
            )}
          </Link>
          
          {!collapsed && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={onToggleCollapse}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Navigation */}
        <ScrollArea className="flex-1 py-4">
          <nav className="space-y-1 px-2">
            {navigation.map((item) => {
              const isActive = pathname === item.href
              const Icon = item.icon
              
              if (collapsed) {
                return (
                  <Tooltip key={item.href}>
                    <TooltipTrigger asChild>
                      <Link
                        href={item.href}
                        className={cn(
                          'flex items-center justify-center h-10 w-full rounded-lg transition-colors',
                          isActive
                            ? 'bg-primary text-primary-foreground'
                            : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                        )}
                      >
                        <Icon className="h-5 w-5" />
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent side="right" className="flex flex-col">
                      <span className="font-medium">{item.name}</span>
                      <span className="text-xs text-muted-foreground">{item.description}</span>
                    </TooltipContent>
                  </Tooltip>
                )
              }
              
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                  )}
                >
                  <Icon className="h-5 w-5 flex-shrink-0" />
                  <div className="flex flex-col flex-1">
                    <div className="flex items-center gap-2">
                      <span>{item.name}</span>
                      {(item as any).beta && (
                        <span className={cn(
                          "text-xs px-1.5 py-0.5 rounded text-orange-600 bg-orange-100 border border-orange-200",
                          isActive && "text-orange-800 bg-orange-200"
                        )}>
                          Beta
                        </span>
                      )}
                    </div>
                    <span className={cn(
                      "text-xs",
                      isActive ? "text-primary-foreground/70" : "text-muted-foreground"
                    )}>
                      {item.description}
                    </span>
                  </div>
                </Link>
              )
            })}
          </nav>
        </ScrollArea>

        {/* Collapse Button (when collapsed) */}
        {collapsed && (
          <div className="px-2 py-2 border-t border-border">
            <Button
              variant="ghost"
              size="icon"
              className="w-full h-10"
              onClick={onToggleCollapse}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* User Section */}
        <div className={cn(
          "border-t border-border p-3",
          collapsed && "px-2"
        )}>
          {user ? (
            <div className={cn(
              "flex items-center gap-3",
              collapsed && "flex-col"
            )}>
              <div className={cn(
                "flex items-center justify-center rounded-full bg-muted flex-shrink-0",
                collapsed ? "w-10 h-10" : "w-9 h-9"
              )}>
                <User className="w-4 h-4 text-muted-foreground" />
              </div>
              
              {!collapsed && (
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{user.email}</div>
                  <div className="text-xs text-muted-foreground">Logged in</div>
                </div>
              )}
              
              {collapsed ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-9 w-9 text-destructive hover:text-destructive hover:bg-destructive/10"
                      onClick={onLogout}
                    >
                      <LogOut className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">Logout</TooltipContent>
                </Tooltip>
              ) : (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                  onClick={onLogout}
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              )}
            </div>
          ) : (
            <Link href="/login">
              <Button className={cn("w-full", collapsed && "px-2")}>
                {collapsed ? <User className="h-4 w-4" /> : "Login"}
              </Button>
            </Link>
          )}
        </div>
      </aside>
    </TooltipProvider>
  )
}

// Mobile Bottom Navigation
export function MobileNavigation() {
  const pathname = usePathname()
  
  const mobileNav = [
    { name: 'Home', href: '/', icon: LayoutDashboard },
    { name: 'Screener', href: '/screener', icon: Search },
    { name: 'Options', href: '/options', icon: Target },
    { name: 'Billing', href: '/billing', icon: CreditCard },
  ]

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 md:hidden border-t border-border bg-background/95 backdrop-blur safe-area-inset-bottom">
      <div className="flex items-center justify-around h-16 px-2">
        {mobileNav.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center justify-center flex-1 py-2 text-xs font-medium transition-colors",
                isActive
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className={cn("h-5 w-5 mb-1", isActive && "text-primary")} />
              {item.name}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
