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
  scalp_feasibility?: {
    feasible: boolean
    risk_level: string
    risk_score: number
    recommendation: string
    time_window: string
    targets: {
      entry: number
      target_5: number
      target_10: number
      target_15: number
      stop_loss: number
    }
    index_moves_needed: {
      for_5_pts: number
      for_10_pts: number
      for_15_pts: number
    }
    per_lot_pnl: {
      profit_5: number
      profit_10: number
      profit_15: number
      max_loss: number
      lot_size: number
    }
    theta_impact?: {
      per_hour: number
      per_30_min: number
      warning: string
    }
    risk_factors: string[]
    momentum_boost: boolean
  }
  greeks?: {
    delta: number
    gamma?: number
    theta?: number
    vega?: number
  }
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

        {/* ⚡ Quick Scalp Targets - 5/10/15 Point Zones */}
        {signal.scalp_feasibility && signal.greeks?.delta && (
          <div className="mt-3 pt-3 border-t">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-cyan-400">⚡ Quick Scalp Targets</span>
                <span className="text-xs bg-cyan-600/50 px-1.5 py-0.5 rounded">INTRADAY</span>
              </div>
              <div className="text-xs text-gray-500">
                Delta: <span className="text-cyan-300 font-mono">{signal.greeks.delta.toFixed(3)}</span>
              </div>
            </div>
            
            {/* Risk Level Badge */}
            <div className="mb-2">
              <Badge
                variant={
                  !signal.scalp_feasibility.feasible || signal.scalp_feasibility.risk_level === 'EXTREME'
                    ? 'destructive'
                    : signal.scalp_feasibility.risk_level === 'HIGH'
                    ? 'secondary'
                    : 'default'
                }
                className={cn(
                  'text-xs',
                  !signal.scalp_feasibility.feasible || signal.scalp_feasibility.risk_level === 'EXTREME'
                    ? 'bg-red-600/80'
                    : signal.scalp_feasibility.risk_level === 'HIGH'
                    ? 'bg-yellow-600/80'
                    : 'bg-green-600/80'
                )}
              >
                {!signal.scalp_feasibility.feasible || signal.scalp_feasibility.risk_level === 'EXTREME'
                  ? '⛔ HIGH RISK'
                  : signal.scalp_feasibility.risk_level === 'HIGH'
                  ? '⚠️ RISKY'
                  : '✅ VIABLE'
                }
              </Badge>
            </div>

            {/* Scalp Target Grid */}
            <div className="grid grid-cols-3 gap-2 mb-2">
              {/* 5 Points Target */}
              <div className="bg-green-900/40 rounded-lg p-2 border border-green-500/30 text-center">
                <div className="text-xs text-green-400/70">+5 Points</div>
                <div className="text-sm font-bold text-green-400">
                  ₹{signal.scalp_feasibility.targets.target_5.toFixed(1)}
                </div>
                <div className="text-xs text-gray-400">
                  ~{signal.scalp_feasibility.index_moves_needed.for_5_pts} idx pts
                </div>
              </div>

              {/* 10 Points Target */}
              <div className="bg-green-900/50 rounded-lg p-2 border border-green-500/40 text-center">
                <div className="text-xs text-green-400/70">+10 Points</div>
                <div className="text-sm font-bold text-green-400">
                  ₹{signal.scalp_feasibility.targets.target_10.toFixed(1)}
                </div>
                <div className="text-xs text-gray-400">
                  ~{signal.scalp_feasibility.index_moves_needed.for_10_pts} idx pts
                </div>
              </div>

              {/* 15 Points Target */}
              <div className="bg-green-900/60 rounded-lg p-2 border border-green-500/50 text-center">
                <div className="text-xs text-green-400/70">+15 Points</div>
                <div className="text-sm font-bold text-green-400">
                  ₹{signal.scalp_feasibility.targets.target_15.toFixed(1)}
                </div>
                <div className="text-xs text-gray-400">
                  ~{signal.scalp_feasibility.index_moves_needed.for_15_pts} idx pts
                </div>
              </div>
            </div>

            {/* Stop Loss and Per Lot Info */}
            <div className="flex justify-between items-center text-xs">
              <span>
                SL: <span className="text-red-400">₹{signal.scalp_feasibility.targets.stop_loss.toFixed(1)}</span>
              </span>
              <span>
                Per Lot: <span className="text-cyan-300">
                  ₹{signal.scalp_feasibility.per_lot_pnl.profit_5} to ₹{signal.scalp_feasibility.per_lot_pnl.profit_15}
                </span>
                {signal.scalp_feasibility.theta_impact && signal.scalp_feasibility.theta_impact.per_hour > 1.5 && (
                  <span className="text-red-400 ml-2">
                    ⏱️ θ: -₹{signal.scalp_feasibility.theta_impact.per_hour.toFixed(1)}/hr
                  </span>
                )}
              </span>
            </div>

            {/* Recommendation */}
            {signal.scalp_feasibility.recommendation && (
              <div className="mt-1 text-xs text-gray-400">
                {signal.scalp_feasibility.recommendation}
              </div>
            )}
          </div>
        )}

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
