'use client'

import * as React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'
import { Clock, TrendingUp, TrendingDown, Target, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface OptionScannerResult {
    index: string
    trading_symbol: string
    action: string
    strike: number
    option_type: string
    entry_price: number
    target_1?: number
    target_2?: number
    stop_loss?: number
    confidence: number
    timestamp: string
    spot_price?: number
}

interface OptionScannerResultsWidgetProps {
    index: string
    onIndexChange?: (index: string) => void
    className?: string
}

const INDICES = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX', 'BANKEX']

export function OptionScannerResultsWidget({
    index,
    onIndexChange,
    className
}: OptionScannerResultsWidgetProps) {
    const [result, setResult] = React.useState<OptionScannerResult | null>(null)
    const [loading, setLoading] = React.useState(false)
    const [error, setError] = React.useState<string | null>(null)

    const fetchLatestResult = React.useCallback(async () => {
        setLoading(true)
        setError(null)

        try {
            const apiUrl = typeof window !== 'undefined'
                ? (localStorage.getItem('apiUrl') || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
                : 'http://localhost:8000'

            const token = typeof window !== 'undefined'
                ? (localStorage.getItem('auth_token') || localStorage.getItem('token') || localStorage.getItem('jwt_token'))
                : null

            if (!token) {
                setError('Please login to view scan results')
                return
            }

            const response = await fetch(
                `${apiUrl}/options/scanner-results/latest?index=${index}`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }
            )

            if (response.ok) {
                const data = await response.json()

                if (data.status === 'success') {
                    setResult(data)
                    setError(null)
                } else if (data.status === 'no_data') {
                    setResult(null)
                    setError(null) // No error, just no data
                }
            } else if (response.status === 404) {
                setResult(null)
                setError(null)
            } else {
                setError('Failed to fetch scan results')
            }
        } catch (err) {
            console.error('Error fetching option scanner results:', err)
            setError('Network error')
        } finally {
            setLoading(false)
        }
    }, [index])

    React.useEffect(() => {
        fetchLatestResult()
    }, [index, fetchLatestResult])

    const getActionColor = (action: string) => {
        if (action.includes('BUY') && action.includes('CALL')) return 'text-green-600 dark:text-green-400'
        if (action.includes('BUY') && action.includes('PUT')) return 'text-red-600 dark:text-red-400'
        if (action.includes('SELL')) return 'text-orange-600 dark:text-orange-400'
        if (action.includes('WAIT')) return 'text-yellow-600 dark:text-yellow-400'
        if (action.includes('AVOID')) return 'text-gray-600 dark:text-gray-400'
        return 'text-primary'
    }

    const getActionIcon = (action: string) => {
        if (action.includes('BUY') && action.includes('CALL')) return TrendingUp
        if (action.includes('BUY') && action.includes('PUT')) return TrendingDown
        return Target
    }

    const formatTimestamp = (timestamp: string) => {
        const date = new Date(timestamp)
        const now = new Date()
        const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))

        if (diffMinutes < 1) return 'Just now'
        if (diffMinutes < 60) return `${diffMinutes}m ago`
        if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`
        return date.toLocaleDateString()
    }

    return (
        <Card className={className}>
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">Latest Scan Results</CardTitle>
                    <Select value={index} onValueChange={onIndexChange}>
                        <SelectTrigger className="w-[140px] h-8">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            {INDICES.map((idx) => (
                                <SelectItem key={idx} value={idx}>
                                    {idx}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            </CardHeader>

            <CardContent>
                {loading ? (
                    <div className="flex items-center justify-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                ) : error ? (
                    <div className="flex items-center gap-2 p-4 rounded-lg bg-muted text-muted-foreground">
                        <AlertCircle className="h-4 w-4" />
                        <span className="text-sm">{error}</span>
                    </div>
                ) : result ? (
                    <div className="space-y-4">
                        {/* Action and Symbol */}
                        <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    {React.createElement(getActionIcon(result.action), {
                                        className: cn("h-5 w-5", getActionColor(result.action))
                                    })}
                                    <span className={cn("font-bold text-lg", getActionColor(result.action))}>
                                        {result.action}
                                    </span>
                                </div>
                                <div className="text-sm font-medium text-muted-foreground">
                                    {result.trading_symbol}
                                </div>
                            </div>
                            <Badge variant="outline" className="shrink-0">
                                {result.confidence.toFixed(0)}% Confidence
                            </Badge>
                        </div>

                        {/* Price Details */}
                        <div className="grid grid-cols-2 gap-3">
                            <div className="p-3 rounded-lg bg-muted/50">
                                <div className="text-xs text-muted-foreground mb-1">Entry Price</div>
                                <div className="font-bold text-lg">₹{result.entry_price.toFixed(2)}</div>
                            </div>
                            {result.spot_price && (
                                <div className="p-3 rounded-lg bg-muted/50">
                                    <div className="text-xs text-muted-foreground mb-1">Spot Price</div>
                                    <div className="font-bold text-lg">₹{result.spot_price.toFixed(2)}</div>
                                </div>
                            )}
                        </div>

                        {/* Targets and Stop Loss */}
                        {(result.target_1 || result.target_2 || result.stop_loss) && (
                            <div className="space-y-2">
                                {result.target_1 && (
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-muted-foreground">Target 1</span>
                                        <span className="font-semibold text-green-600">₹{result.target_1.toFixed(2)}</span>
                                    </div>
                                )}
                                {result.target_2 && (
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-muted-foreground">Target 2</span>
                                        <span className="font-semibold text-green-600">₹{result.target_2.toFixed(2)}</span>
                                    </div>
                                )}
                                {result.stop_loss && (
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-muted-foreground">Stop Loss</span>
                                        <span className="font-semibold text-red-600">₹{result.stop_loss.toFixed(2)}</span>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Timestamp */}
                        <div className="flex items-center gap-1 text-xs text-muted-foreground pt-2 border-t">
                            <Clock className="h-3 w-3" />
                            <span>Scanned {formatTimestamp(result.timestamp)}</span>
                        </div>
                    </div>
                ) : (
                    <div className="text-center py-8">
                        <div className="text-muted-foreground mb-3">
                            <Target className="h-12 w-12 mx-auto mb-2 opacity-20" />
                            <p className="text-sm">No scans yet for {index}</p>
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => window.location.reload()}
                        >
                            Run a Scan
                        </Button>
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
