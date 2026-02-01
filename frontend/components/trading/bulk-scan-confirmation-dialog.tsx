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
import { AlertTriangle, Wallet, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface BulkScanConfirmationDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    stockCount: number
    totalCost: number
    perStockCost: number
    walletBalance: number
    sufficientBalance: boolean
    willUseSubscription?: boolean
    subscriptionInfo?: {
        plan_type: string
        scans_remaining: number
        daily_limit: number
    }
    onConfirm: () => void
}

export function BulkScanConfirmationDialog({
    open,
    onOpenChange,
    stockCount,
    totalCost,
    perStockCost,
    walletBalance,
    sufficientBalance,
    willUseSubscription = false,
    subscriptionInfo,
    onConfirm,
}: BulkScanConfirmationDialogProps) {
    const balanceAfter = walletBalance - totalCost
    const isLowBalanceAfter = balanceAfter < 50 && !willUseSubscription

    const handleConfirm = () => {
        onConfirm()
        onOpenChange(false)
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        Confirm Bulk Scan
                    </DialogTitle>
                    <DialogDescription>
                        You are about to scan {stockCount} stock{stockCount !== 1 ? 's' : ''}
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    {/* Cost Breakdown */}
                    {willUseSubscription && subscriptionInfo ? (
                        <div className="rounded-lg border bg-green-50 dark:bg-green-950/20 p-4 space-y-3">
                            <div className="flex items-start gap-2">
                                <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                                <div className="flex-1">
                                    <div className="font-semibold text-green-900 dark:text-green-100">
                                        Using {subscriptionInfo.plan_type} Subscription
                                    </div>
                                    <div className="text-sm text-green-700 dark:text-green-300 mt-1">
                                        Scans remaining today: {subscriptionInfo.scans_remaining} of {subscriptionInfo.daily_limit}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="rounded-lg border bg-muted/50 p-4 space-y-3">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium">💰 Total cost:</span>
                                <div className="text-right">
                                    <div className="font-bold text-lg">₹{totalCost.toFixed(2)}</div>
                                    <div className="text-xs text-muted-foreground">
                                        ₹{perStockCost} per stock
                                    </div>
                                </div>
                            </div>

                            <div className="h-px bg-border" />

                            <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground flex items-center gap-2">
                                    <Wallet className="h-4 w-4" />
                                    Your wallet balance:
                                </span>
                                <span className="font-medium">₹{walletBalance.toFixed(2)}</span>
                            </div>

                            {sufficientBalance && (
                                <>
                                    <div className="h-px bg-border" />
                                    <div className="flex items-center justify-between text-sm font-semibold">
                                        <span>Balance after scan:</span>
                                        <span className={cn(
                                            isLowBalanceAfter && "text-orange-500"
                                        )}>
                                            ₹{balanceAfter.toFixed(2)}
                                        </span>
                                    </div>
                                </>
                            )}
                        </div>
                    )}

                    {/* Success Message */}
                    {sufficientBalance && !willUseSubscription && (
                        <div className="flex items-start gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900">
                            <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                            <div className="text-sm text-green-800 dark:text-green-200">
                                Amount will be deducted from your wallet.
                            </div>
                        </div>
                    )}

                    {/* Low Balance Warning */}
                    {isLowBalanceAfter && sufficientBalance && (
                        <div className="flex items-start gap-2 p-3 rounded-lg bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-900">
                            <AlertTriangle className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                            <div className="text-sm text-orange-800 dark:text-orange-200">
                                <div className="font-medium">Low Balance Warning</div>
                                <div className="text-xs mt-1">
                                    Your balance will be low after this scan. Consider topping up your wallet.
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
                                    You need ₹{(totalCost - walletBalance).toFixed(2)} more to complete this scan. Please add credits to your wallet or subscribe to a plan.
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
                        {sufficientBalance ? 'OK' : 'Add Credits'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
