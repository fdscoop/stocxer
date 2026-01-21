'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  icon?: React.ReactNode
  className?: string
  variant?: 'default' | 'bullish' | 'bearish' | 'neutral'
}

export function StatCard({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  icon,
  className,
  variant = 'default',
}: StatCardProps) {
  return (
    <div
      className={cn(
        'rounded-xl border p-3 md:p-4 transition-all',
        {
          'bg-card border-border': variant === 'default',
          'bg-bullish-muted border-bullish/30': variant === 'bullish',
          'bg-bearish-muted border-bearish/30': variant === 'bearish',
          'bg-neutral-muted border-neutral/30': variant === 'neutral',
        },
        className
      )}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs md:text-sm text-muted-foreground">{title}</span>
        {icon && <span className="text-muted-foreground">{icon}</span>}
      </div>
      <div className="flex items-baseline gap-2">
        <span
          className={cn('text-xl md:text-2xl font-bold', {
            'text-bullish': variant === 'bullish',
            'text-bearish': variant === 'bearish',
            'text-neutral': variant === 'neutral',
          })}
        >
          {value}
        </span>
        {trend && trendValue && (
          <span
            className={cn('flex items-center text-xs', {
              'text-bullish': trend === 'up',
              'text-bearish': trend === 'down',
              'text-muted-foreground': trend === 'neutral',
            })}
          >
            {trend === 'up' && <TrendingUp className="w-3 h-3 mr-0.5" />}
            {trend === 'down' && <TrendingDown className="w-3 h-3 mr-0.5" />}
            {trend === 'neutral' && <Minus className="w-3 h-3 mr-0.5" />}
            {trendValue}
          </span>
        )}
      </div>
      {subtitle && (
        <span className="text-xs text-muted-foreground">{subtitle}</span>
      )}
    </div>
  )
}

interface StatsGridProps {
  children: React.ReactNode
  columns?: 2 | 3 | 4
  className?: string
}

export function StatsGrid({ children, columns = 4, className }: StatsGridProps) {
  return (
    <div
      className={cn(
        'grid gap-2 md:gap-3',
        {
          'grid-cols-2': columns === 2,
          'grid-cols-2 md:grid-cols-3': columns === 3,
          'grid-cols-2 md:grid-cols-4': columns === 4,
        },
        className
      )}
    >
      {children}
    </div>
  )
}
