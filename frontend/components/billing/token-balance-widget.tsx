'use client'

import * as React from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { RefreshCw, Wallet, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TokenBalanceWidgetProps {
    balance: number | null
    loading?: boolean
    onRefresh?: () => void
    className?: string
}

export function TokenBalanceWidget({
    balance,
    loading = false,
    onRefresh,
    className
}: TokenBalanceWidgetProps) {
    const [isRefreshing, setIsRefreshing] = React.useState(false)

    const handleRefresh = async () => {
        if (onRefresh && !isRefreshing && !loading) {
            setIsRefreshing(true)
            await onRefresh()
            setTimeout(() => setIsRefreshing(false), 500)
        }
    }

    const isLowBalance = balance !== null && balance < 10
    const displayBalance = balance !== null ? balance.toFixed(2) : '---'

    return (
        <Card className={cn("px-4 py-3 shadow-sm", className)}>
            <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                    <div className={cn(
                        "w-10 h-10 rounded-full flex items-center justify-center",
                        isLowBalance ? "bg-orange-500/10" : "bg-primary/10"
                    )}>
                        <Wallet className={cn(
                            "h-5 w-5",
                            isLowBalance ? "text-orange-500" : "text-primary"
                        )} />
                    </div>
                    <div>
                        <div className="text-xs text-muted-foreground">Token Balance</div>
                        <div className="flex items-baseline gap-1">
                            <span className={cn(
                                "text-2xl font-bold",
                                isLowBalance && "text-orange-500"
                            )}>
                                {loading ? '...' : `₹${displayBalance}`}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex flex-col items-end gap-1">
                    {isLowBalance && balance !== null && (
                        <div className="flex items-center gap-1 text-xs text-orange-500">
                            <AlertTriangle className="h-3 w-3" />
                            <span>Low Balance</span>
                        </div>
                    )}
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleRefresh}
                        disabled={loading || isRefreshing}
                        className="h-7 px-2"
                    >
                        <RefreshCw className={cn(
                            "h-3 w-3",
                            (loading || isRefreshing) && "animate-spin"
                        )} />
                    </Button>
                </div>
            </div>
        </Card>
    )
}
