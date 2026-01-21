'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

interface ProbabilityBarProps {
  label: string
  value: number
  max?: number
  color?: 'bullish' | 'bearish' | 'neutral' | 'primary'
  showValue?: boolean
  className?: string
}

export function ProbabilityBar({
  label,
  value,
  max = 100,
  color = 'primary',
  showValue = true,
  className,
}: ProbabilityBarProps) {
  const percentage = (value / max) * 100

  return (
    <div className={cn('space-y-1', className)}>
      <div className="flex justify-between text-xs md:text-sm">
        <span className={cn({
          'text-bullish': color === 'bullish',
          'text-bearish': color === 'bearish',
          'text-neutral': color === 'neutral',
        })}>
          {label}
        </span>
        {showValue && (
          <span className="font-semibold">{value.toFixed(1)}%</span>
        )}
      </div>
      <div className="w-full bg-muted rounded-full h-2 md:h-3">
        <div
          className={cn('h-full rounded-full transition-all duration-500', {
            'bg-bullish': color === 'bullish',
            'bg-bearish': color === 'bearish',
            'bg-neutral': color === 'neutral',
            'bg-primary': color === 'primary',
          })}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  )
}

interface SentimentGaugeProps {
  bullish: number
  bearish: number
  className?: string
}

export function SentimentGauge({ bullish, bearish, className }: SentimentGaugeProps) {
  const total = bullish + bearish
  const bullishPercent = total > 0 ? (bullish / total) * 100 : 50
  const bearishPercent = total > 0 ? (bearish / total) * 100 : 50

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex justify-between items-center">
        <div className="text-center">
          <div className="text-xl md:text-2xl font-bold text-bullish">{bullish}</div>
          <div className="text-xs text-muted-foreground">Bullish</div>
        </div>
        <div className="text-center">
          <div className="text-xl md:text-2xl font-bold text-bearish">{bearish}</div>
          <div className="text-xs text-muted-foreground">Bearish</div>
        </div>
      </div>
      <div className="flex h-3 rounded-full overflow-hidden">
        <div
          className="bg-bullish transition-all duration-500"
          style={{ width: `${bullishPercent}%` }}
        />
        <div
          className="bg-bearish transition-all duration-500"
          style={{ width: `${bearishPercent}%` }}
        />
      </div>
    </div>
  )
}
