'use client'

import * as React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, Target, AlertTriangle } from 'lucide-react'

export interface Signal {
  id?: string
  symbol: string
  action: 'BUY' | 'SELL'
  price: number
  target?: number
  stopLoss?: number
  confidence: number
  timestamp?: string
  reasons?: string[]
}

interface SignalCardProps {
  signal: Signal
  className?: string
  compact?: boolean
}

export function SignalCard({ signal, className, compact = false }: SignalCardProps) {
  const isBuy = signal.action === 'BUY'
  const potentialGain = signal.target
    ? (((signal.target - signal.price) / signal.price) * 100).toFixed(1)
    : null
  const potentialLoss = signal.stopLoss
    ? (((signal.price - signal.stopLoss) / signal.price) * 100).toFixed(1)
    : null

  return (
    <Card
      className={cn(
        'transition-all hover:shadow-lg',
        isBuy ? 'border-bullish/30' : 'border-bearish/30',
        className
      )}
    >
      <CardHeader className={cn('pb-2', compact && 'p-3')}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className={cn('text-base md:text-lg', compact && 'text-sm')}>
              {signal.symbol}
            </CardTitle>
            <Badge variant={isBuy ? 'bullish' : 'bearish'}>
              {isBuy ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
              {signal.action}
            </Badge>
          </div>
          <div
            className={cn(
              'text-xs md:text-sm font-semibold px-2 py-1 rounded',
              signal.confidence >= 80
                ? 'bg-bullish/20 text-bullish'
                : signal.confidence >= 60
                ? 'bg-neutral/20 text-neutral'
                : 'bg-bearish/20 text-bearish'
            )}
          >
            {signal.confidence}%
          </div>
        </div>
      </CardHeader>
      <CardContent className={cn(compact && 'p-3 pt-0')}>
        <div className={cn('grid gap-2', compact ? 'grid-cols-3' : 'grid-cols-3')}>
          <div className="text-center p-2 rounded-lg bg-muted">
            <div className="text-xs text-muted-foreground">Entry</div>
            <div className="text-sm md:text-base font-semibold">₹{signal.price.toFixed(2)}</div>
          </div>
          {signal.target && (
            <div className="text-center p-2 rounded-lg bg-bullish/10">
              <div className="text-xs text-muted-foreground flex items-center justify-center gap-1">
                <Target className="w-3 h-3" />
                Target
              </div>
              <div className="text-sm md:text-base font-semibold text-bullish">
                ₹{signal.target.toFixed(2)}
              </div>
              {potentialGain && (
                <div className="text-xs text-bullish">+{potentialGain}%</div>
              )}
            </div>
          )}
          {signal.stopLoss && (
            <div className="text-center p-2 rounded-lg bg-bearish/10">
              <div className="text-xs text-muted-foreground flex items-center justify-center gap-1">
                <AlertTriangle className="w-3 h-3" />
                SL
              </div>
              <div className="text-sm md:text-base font-semibold text-bearish">
                ₹{signal.stopLoss.toFixed(2)}
              </div>
              {potentialLoss && (
                <div className="text-xs text-bearish">-{potentialLoss}%</div>
              )}
            </div>
          )}
        </div>

        {!compact && signal.reasons && signal.reasons.length > 0 && (
          <div className="mt-3 pt-3 border-t">
            <div className="text-xs text-muted-foreground mb-1">Reasons:</div>
            <div className="flex flex-wrap gap-1">
              {signal.reasons.slice(0, 3).map((reason, i) => (
                <span
                  key={i}
                  className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground"
                >
                  {reason}
                </span>
              ))}
            </div>
          </div>
        )}

        {signal.timestamp && (
          <div className="mt-2 text-xs text-muted-foreground text-right" suppressHydrationWarning>
            {new Date(signal.timestamp).toLocaleString('en-IN', {
              day: '2-digit',
              month: 'short',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

interface SignalGridProps {
  signals: Signal[]
  compact?: boolean
  className?: string
}

export function SignalGrid({ signals, compact = false, className }: SignalGridProps) {
  if (signals.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No signals found. Run a scan to find trading opportunities.
      </div>
    )
  }

  return (
    <div
      className={cn(
        'grid gap-3 md:gap-4',
        compact ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1 md:grid-cols-2',
        className
      )}
    >
      {signals.map((signal, i) => (
        <SignalCard key={signal.id || i} signal={signal} compact={compact} />
      ))}
    </div>
  )
}
