'use client'

import * as React from 'react'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Zap, TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ScanConfirmationDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    scanMode: 'quick' | 'full'
    index: string
    costInTokens: number
    costInRupees: number
    currentBalance: number
    balanceAfter: number
    sufficientBalance: boolean
    scanDescription?: string
    willUseSubscription?: boolean
    paymentMethod?: string
    onConfirm: () => void
}

export function ScanConfirmationDialog({
    open,
    onOpenChange,
    scanMode,
    index,
    costInTokens,
    costInRupees,
    currentBalance,
    balanceAfter,
    sufficientBalance,
    scanDescription,
    willUseSubscription = false,
    paymentMethod = 'wallet',
    onConfirm,
}: ScanConfirmationDialogProps) {
    const isLowBalanceAfter = balanceAfter < 10 && !willUseSubscription

    const handleConfirm = () => {
        onConfirm()
        onOpenChange(false)
    }

    const modeLabel = scanMode === 'quick' ? 'Quick Scan' : 'Full Analysis'
    const modeIcon = scanMode === 'quick' ? Zap : TrendingUp
    const ModeIcon = modeIcon

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <ModeIcon className="h-5 w-5 text-primary" />
                        Confirm {modeLabel}
                    </DialogTitle>
                    <DialogDescription>
                        Review the scan details and cost before proceeding
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    {/* Scan Details */}
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">Index</span>
                            <Badge variant="outline" className="font-semibold">
                                {index}
                            </Badge>
                        </div>

                        <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">Scan Mode</span>
                            <Badge
                                variant={scanMode === 'quick' ? 'default' : 'secondary'}
                                className="font-medium"
                            >
                                {modeLabel}
                            </Badge>
                        </div>

                        {scanDescription && (
                            <div className="text-xs text-muted-foreground pt-1 border-t">
                                {scanDescription}
                            </div>
                        )}
                    </div>

                    {/* Cost Breakdown */}
                    <div className="rounded-lg border bg-muted/50 p-4 space-y-2">
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Scan Cost</span>
                            <div className="text-right">
                                <div className="font-bold text-lg">₹{costInRupees.toFixed(2)}</div>
                                <div className="text-xs text-muted-foreground">
                                    {costInTokens.toFixed(2)} tokens
                                </div>
                            </div>
                        </div>

                        {!willUseSubscription && (
                            <>
                                <div className="h-px bg-border" />
                                <div className="flex items-center justify-between text-sm">
                                    <span className="text-muted-foreground">Current Balance</span>
                                    <span>₹{currentBalance.toFixed(2)}</span>
                                </div>

                                <div className="flex items-center justify-between text-sm font-semibold">
                                    <span>Balance After Scan</span>
                                    <span className={cn(
                                        isLowBalanceAfter && "text-orange-500"
                                    )}>
                                        ₹{balanceAfter.toFixed(2)}
                                    </span>
                                </div>
                            </>
                        )}

                        {willUseSubscription && (
                            <div className="flex items-center gap-2 text-sm text-green-600 pt-2">
                                <Badge variant="outline" className="border-green-600">
                                    Using Subscription
                                </Badge>
                                <span>No tokens will be deducted</span>
                            </div>
                        )}
                    </div>

                    {/* Low Balance Warning */}
                    {isLowBalanceAfter && !willUseSubscription && (
                        <div className="flex items-start gap-2 p-3 rounded-lg bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-900">
                            <AlertTriangle className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                            <div className="text-sm text-orange-800 dark:text-orange-200">
                                <div className="font-medium">Low Balance Warning</div>
                                <div className="text-xs mt-1">
                                    Your balance will be low after this scan. Consider topping up your tokens.
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Insufficient Balance */}
                    {!sufficientBalance && (
                        <div className="flex items-start gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900">
                            <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                            <div className="text-sm text-red-800 dark:text-red-200">
                                <div className="font-medium">Insufficient Balance</div>
                                <div className="text-xs mt-1">
                                    You need ₹{(costInRupees - currentBalance).toFixed(2)} more tokens to complete this scan.
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <DialogFooter className="gap-2 sm:gap-0">
                    <Button
                        type="button"
                        variant="outline"
                        onClick={() => onOpenChange(false)}
                    >
                        Cancel
                    </Button>
                    <Button
                        type="button"
                        onClick={handleConfirm}
                        disabled={!sufficientBalance}
                    >
                        {sufficientBalance ? 'Confirm Scan' : 'Add Tokens First'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
