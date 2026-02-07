'use client'

import * as React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, RefreshCw, Clock } from 'lucide-react'

export interface OptionAwareSignal {
    signal: string
    action: string
    confidence: {
        score: number
        level: string
    }
    tier?: number
    setup_type?: string
    option?: {
        strike: number
        type: 'CE' | 'PE'
        symbol: string
        entry_price: number
        delta: number
        gamma?: number
        theta?: number
        iv?: number
        volume: number
        oi: number
    }
    targets?: {
        target_1_price: number
        target_1_points: number
        target_2_price: number
        target_2_points: number
        stop_loss_price: number
        stop_loss_points: number
    }
    risk_reward?: {
        risk_per_lot: number
        reward_1_per_lot: number
        reward_2_per_lot: number
        ratio_1: string
        ratio_2: string
    }
    index_context?: {
        spot_price: number
        expected_move: number
    }
    // NEW: AMD (Manipulation) Detection
    amd_detection?: {
        manipulation_found: boolean
        type: 'bear_trap' | 'bull_trap' | null
        level: number | null
        confidence: number
        override_signal: 'bullish' | 'bearish' | null
        description: string | null
        recovery_pts: number
        time: string | null
        is_active: boolean
        override_applied: boolean
    }
    lot_size?: number
    reasoning?: string[]
    timestamp?: string
}

interface OptionAwareSignalCardProps {
    index: string
    className?: string
    compact?: boolean
    onRefresh?: () => void
    isLoading?: boolean
}

export function OptionAwareSignalCard({
    index,
    className,
    compact = false,
    onRefresh,
    isLoading = false
}: OptionAwareSignalCardProps) {
    const [signal, setSignal] = React.useState<OptionAwareSignal | null>(null)
    const [loading, setLoading] = React.useState(true)
    const [lastUpdate, setLastUpdate] = React.useState<Date | null>(null)

    // Fetch signal from API
    const fetchSignal = React.useCallback(async () => {
        try {
            setLoading(true)
            const response = await fetch(`/api/signals/${index}/option-aware`, {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem('token')}`
                }
            })

            if (!response.ok) {
                throw new Error('Failed to fetch signal')
            }

            const data = await response.json()
            setSignal(data.signal)
            setLastUpdate(new Date())
        } catch (error) {
            console.error('Error fetching option-aware signal:', error)
        } finally {
            setLoading(false)
        }
    }, [index])

    // Initial fetch
    React.useEffect(() => {
        fetchSignal()
    }, [fetchSignal])

    // Auto-refresh every 2 minutes during market hours
    React.useEffect(() => {
        const interval = setInterval(fetchSignal, 120000) // 2 minutes
        return () => clearInterval(interval)
    }, [fetchSignal])

    // Handle manual refresh
    const handleRefresh = () => {
        if (onRefresh) {
            onRefresh()
        }
        fetchSignal()
    }

    // Show loading state
    if (loading && !signal) {
        return (
            <Card className={cn('border-purple-500/30', className)}>
                <CardHeader>
                    <CardTitle className="text-base md:text-lg flex items-center gap-2">
                        🎯 Option-Aware ICT Signal
                        <Badge variant="outline" className="bg-yellow-600/20">
                            LOADING...
                        </Badge>
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-center py-8 text-muted-foreground">
                        <RefreshCw className="w-8 h-8 mx-auto mb-2 animate-spin" />
                        <div>Analyzing {index}...</div>
                    </div>
                </CardContent>
            </Card>
        )
    }

    // Show WAIT state
    if (!signal || signal.signal === 'WAIT') {
        return (
            <Card className={cn('border-purple-500/30', className)}>
                <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                        <CardTitle className="text-base md:text-lg flex items-center gap-2">
                            🎯 Option-Aware ICT Signal
                            <Badge variant="outline" className="bg-yellow-600/20">
                                WAIT
                            </Badge>
                            <Badge variant="outline" className="bg-purple-600/20">
                                📊 DELTA TARGETS
                            </Badge>
                        </CardTitle>
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={handleRefresh}
                            disabled={isLoading}
                            className="h-8 w-8"
                        >
                            <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
                        </Button>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="text-center py-8">
                        <div className="text-4xl mb-2">⏸️</div>
                        <div className="text-lg font-semibold text-yellow-500">WAIT</div>
                        <div className="text-sm text-muted-foreground mt-2">
                            {signal?.reasoning?.[0] || 'No clear setup found'}
                        </div>
                        {lastUpdate && (
                            <div className="text-xs text-muted-foreground mt-4 flex items-center justify-center gap-1">
                                <Clock className="w-3 h-3" />
                                {lastUpdate.toLocaleTimeString('en-IN')}
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>
        )
    }

    // Show full signal
    const isBuy = signal.action.includes('BUY')
    const option = signal.option
    const targets = signal.targets
    const rr = signal.risk_reward
    const ctx = signal.index_context
    const amd = signal.amd_detection

    return (
        <Card className={cn('border-purple-500/30', className)}>
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-base md:text-lg flex items-center gap-2 flex-wrap">
                        🎯 Option-Aware ICT
                        <Badge variant={isBuy ? 'bullish' : 'bearish'}>
                            {isBuy ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                            {signal.action}
                        </Badge>
                        <Badge variant="outline" className="bg-purple-600/20">
                            📊 DELTA
                        </Badge>
                    </CardTitle>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleRefresh}
                        disabled={isLoading}
                        className="h-8 w-8"
                    >
                        <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Signal Summary */}
                <div className="grid grid-cols-3 gap-3">
                    <div className="bg-muted rounded-lg p-3">
                        <div className="text-xs text-muted-foreground mb-1">Confidence</div>
                        <div className={cn(
                            'text-xl font-bold',
                            signal.confidence.score >= 75 ? 'text-bullish' :
                                signal.confidence.score >= 60 ? 'text-neutral' : 'text-bearish'
                        )}>
                            {signal.confidence.score}%
                        </div>
                        <div className="text-xs text-muted-foreground">{signal.confidence.level}</div>
                    </div>
                    <div className="bg-muted rounded-lg p-3">
                        <div className="text-xs text-muted-foreground mb-1">Setup Quality</div>
                        <div className="text-xl font-bold text-blue-400">Tier {signal.tier || 2}</div>
                        <div className="text-xs text-muted-foreground truncate">{signal.setup_type}</div>
                    </div>
                    <div className="bg-muted rounded-lg p-3">
                        <div className="text-xs text-muted-foreground mb-1">Spot Price</div>
                        <div className="text-lg font-bold">₹{ctx?.spot_price.toLocaleString()}</div>
                        <div className="text-xs text-yellow-500">Move: {ctx?.expected_move}pts</div>
                    </div>
                </div>

                {/* AMD (Manipulation) Detection Alert */}
                {amd?.manipulation_found && (
                    <div className={cn(
                        "rounded-xl p-4 border space-y-2",
                        amd.type === 'bear_trap' 
                            ? "bg-green-900/30 border-green-500/50" 
                            : "bg-red-900/30 border-red-500/50"
                    )}>
                        <div className="flex items-center gap-2">
                            <span className="text-xl">{amd.type === 'bear_trap' ? '🐻' : '🐂'}</span>
                            <h4 className={cn(
                                "text-sm font-bold",
                                amd.type === 'bear_trap' ? "text-green-300" : "text-red-300"
                            )}>
                                {amd.type === 'bear_trap' ? 'BEAR TRAP DETECTED' : 'BULL TRAP DETECTED'}
                                {amd.override_applied && (
                                    <Badge variant="outline" className="ml-2 bg-yellow-600/30 text-yellow-300">
                                        OVERRIDE
                                    </Badge>
                                )}
                            </h4>
                            {amd.is_active && (
                                <Badge variant="outline" className="bg-blue-600/30 animate-pulse">
                                    ACTIVE
                                </Badge>
                            )}
                        </div>
                        
                        <div className="grid grid-cols-3 gap-2 text-center">
                            <div className="bg-muted/50 rounded p-2">
                                <div className="text-xs text-muted-foreground">Level</div>
                                <div className="text-sm font-bold">₹{amd.level?.toLocaleString()}</div>
                            </div>
                            <div className="bg-muted/50 rounded p-2">
                                <div className="text-xs text-muted-foreground">Recovery</div>
                                <div className="text-sm font-bold text-bullish">+{amd.recovery_pts}pts</div>
                            </div>
                            <div className="bg-muted/50 rounded p-2">
                                <div className="text-xs text-muted-foreground">Confidence</div>
                                <div className={cn(
                                    "text-sm font-bold",
                                    amd.confidence >= 80 ? "text-green-400" : "text-yellow-400"
                                )}>{amd.confidence}%</div>
                            </div>
                        </div>
                        
                        {amd.description && (
                            <div className="text-xs text-muted-foreground bg-muted/30 rounded p-2 mt-2">
                                💡 {amd.description}
                            </div>
                        )}
                    </div>
                )}

                {/* Option Details */}
                {option && (
                    <div className="bg-purple-900/20 rounded-xl p-4 border border-purple-500/30 space-y-3">
                        <h4 className="text-sm font-bold text-purple-300">📍 Specific Strike</h4>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <div className="text-xs text-muted-foreground">Strike & Type</div>
                                <div className="text-2xl font-bold">{option.strike} {option.type}</div>
                            </div>
                            <div>
                                <div className="text-xs text-muted-foreground">Entry Price (LTP)</div>
                                <div className="text-2xl font-bold text-bullish">₹{option.entry_price.toFixed(2)}</div>
                            </div>
                        </div>

                        <div className="text-xs text-muted-foreground">Symbol:</div>
                        <div className="text-xs font-mono bg-muted px-2 py-1 rounded truncate">{option.symbol}</div>

                        {/* Greeks */}
                        <div className="grid grid-cols-4 gap-2 text-center">
                            <div className="bg-muted rounded p-2">
                                <div className="text-xs text-muted-foreground">Delta</div>
                                <div className="text-sm font-bold text-blue-400">{option.delta.toFixed(3)}</div>
                            </div>
                            {option.gamma && (
                                <div className="bg-muted rounded p-2">
                                    <div className="text-xs text-muted-foreground">Gamma</div>
                                    <div className="text-sm font-bold text-purple-400">{option.gamma.toFixed(4)}</div>
                                </div>
                            )}
                            {option.theta && (
                                <div className="bg-muted rounded p-2">
                                    <div className="text-xs text-muted-foreground">Theta</div>
                                    <div className="text-sm font-bold text-red-400">{option.theta.toFixed(2)}</div>
                                </div>
                            )}
                            {option.iv && (
                                <div className="bg-muted rounded p-2">
                                    <div className="text-xs text-muted-foreground">IV</div>
                                    <div className="text-sm font-bold text-yellow-400">{option.iv.toFixed(1)}%</div>
                                </div>
                            )}
                        </div>

                        {/* Liquidity */}
                        <div className="grid grid-cols-2 gap-2">
                            <div className="bg-muted rounded p-2 text-center">
                                <div className="text-xs text-muted-foreground">Volume</div>
                                <div className="text-sm font-bold">{option.volume.toLocaleString()}</div>
                            </div>
                            <div className="bg-muted rounded p-2 text-center">
                                <div className="text-xs text-muted-foreground">Open Interest</div>
                                <div className="text-sm font-bold">{option.oi.toLocaleString()}</div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Targets */}
                {targets && (
                    <div className="bg-blue-900/20 rounded-xl p-4 border border-blue-500/30 space-y-2">
                        <h4 className="text-sm font-bold text-blue-300">🎯 Premium Targets</h4>

                        <div className="flex justify-between items-center bg-green-900/30 rounded p-2 border border-green-500/30">
                            <span className="text-xs text-muted-foreground">Target 1</span>
                            <span className="font-bold text-bullish">
                                ₹{targets.target_1_price.toFixed(2)} (+{targets.target_1_points.toFixed(1)} pts)
                            </span>
                        </div>
                        <div className="flex justify-between items-center bg-green-900/30 rounded p-2 border border-green-500/30">
                            <span className="text-xs text-muted-foreground">Target 2</span>
                            <span className="font-bold text-bullish">
                                ₹{targets.target_2_price.toFixed(2)} (+{targets.target_2_points.toFixed(1)} pts)
                            </span>
                        </div>
                        <div className="flex justify-between items-center bg-red-900/30 rounded p-2 border border-red-500/30">
                            <span className="text-xs text-muted-foreground">Stop Loss</span>
                            <span className="font-bold text-bearish">
                                ₹{targets.stop_loss_price.toFixed(2)} (-{targets.stop_loss_points.toFixed(1)} pts)
                            </span>
                        </div>
                    </div>
                )}

                {/* Risk/Reward */}
                {rr && (
                    <div className="bg-yellow-900/20 rounded-xl p-4 border border-yellow-500/30">
                        <h4 className="text-sm font-bold text-yellow-300 mb-3">💰 Risk/Reward Per Lot</h4>

                        <div className="grid grid-cols-3 gap-3">
                            <div className="text-center">
                                <div className="text-xs text-muted-foreground mb-1">Risk</div>
                                <div className="text-lg font-bold text-bearish">₹{rr.risk_per_lot.toLocaleString()}</div>
                            </div>
                            <div className="text-center">
                                <div className="text-xs text-muted-foreground mb-1">Reward (T1)</div>
                                <div className="text-lg font-bold text-bullish">
                                    ₹{rr.reward_1_per_lot.toLocaleString()}
                                </div>
                                <div className="text-xs text-muted-foreground">{rr.ratio_1}</div>
                            </div>
                            <div className="text-center">
                                <div className="text-xs text-muted-foreground mb-1">Reward (T2)</div>
                                <div className="text-lg font-bold text-bullish">
                                    ₹{rr.reward_2_per_lot.toLocaleString()}
                                </div>
                                <div className="text-xs text-muted-foreground">{rr.ratio_2}</div>
                            </div>
                        </div>

                        <div className="mt-3 pt-3 border-t border-yellow-500/30 text-center text-sm">
                            <span className="text-muted-foreground">Lot Size: </span>
                            <span className="font-bold">{signal.lot_size}</span>
                        </div>
                    </div>
                )}

                {/* Timestamp */}
                {lastUpdate && (
                    <div className="text-xs text-muted-foreground text-right flex items-center justify-end gap-1">
                        <Clock className="w-3 h-3" />
                        {lastUpdate.toLocaleTimeString('en-IN')}
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
