'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { CreditCard, Zap, TrendingUp, Clock, ShoppingCart, CheckCircle, AlertCircle } from 'lucide-react'
import { getApiUrl } from '@/lib/config'

interface BillingStatus {
    user_id: string
    billing_type: string
    plan_type: string
    subscription_active: boolean
    subscription_end: string | null
    credits_balance: number
    today_usage: {
        option_scans: number
        stock_scans: number
        bulk_scans: number
    }
    limits: {
        daily_option_scans: number | null
        daily_stock_scans: number | null
        bulk_scan_limit: number | null
        daily_bulk_scans: number | null
    }
}

interface CreditPack {
    id: string
    name: string
    amount_inr: number
    credits: number
    bonus_credits: number
    total_credits: number
}

interface Transaction {
    id: string
    transaction_type: string
    amount: number
    description: string
    created_at: string
    balance_after: number
}

interface PaymentHistory {
    id: string
    user_id: string
    payment_type: string
    status: string
    amount_inr: number
    razorpay_payment_id: string
    payment_method?: string
    created_at: string
    metadata?: any
    failure_reason?: string
}

interface CombinedTransaction {
    id: string
    type: 'credit' | 'payment'
    transaction_type: string
    payment_type?: string
    status?: string
    amount: number
    description: string
    created_at: string
    balance_after?: number
    payment_method?: string
    razorpay_payment_id?: string
    failure_reason?: string
}

interface PaymentHistory {
    id: string
    user_id: string
    payment_type: string
    status: string
    amount_inr: number
    razorpay_payment_id: string
    payment_method?: string
    created_at: string
    metadata?: any
    failure_reason?: string
}

interface CombinedTransaction {
    id: string
    type: 'credit' | 'payment'
    transaction_type: string
    payment_type?: string
    status?: string
    amount: number
    description: string
    created_at: string
    balance_after?: number
    payment_method?: string
    razorpay_payment_id?: string
    failure_reason?: string
}

export default function BillingDashboard() {
    const router = useRouter()
    const [billingStatus, setBillingStatus] = useState<BillingStatus | null>(null)
    const [creditPacks, setCreditPacks] = useState<CreditPack[]>([])
    const [transactions, setTransactions] = useState<CombinedTransaction[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    useEffect(() => {
        // Check if user is logged in before fetching data
        const token = localStorage.getItem('auth_token') || 
                     localStorage.getItem('token') || 
                     localStorage.getItem('jwt_token')
        
        if (!token) {
            setError('Please log in to view billing information')
            setLoading(false)
            return
        }
        
        fetchBillingData()
    }, [])

    const fetchBillingData = async () => {
        try {
            // Check for token in all possible localStorage keys
            const token = localStorage.getItem('auth_token') || 
                         localStorage.getItem('token') || 
                         localStorage.getItem('jwt_token')
            
            console.log('Token check:', { 
                auth_token: !!localStorage.getItem('auth_token'),
                token: !!localStorage.getItem('token'),
                jwt_token: !!localStorage.getItem('jwt_token'),
                hasToken: !!token
            })
            
            if (!token) {
                setError('Please log in to view billing')
                setLoading(false)
                // Redirect to login after 2 seconds
                setTimeout(() => {
                    router.push('/login?redirect=/billing')
                }, 2000)
                return
            }

            const apiBase = getApiUrl()

            // Fetch billing status
            const statusResponse = await fetch(`${apiBase}/api/billing/status`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })

            if (statusResponse.status === 401) {
                // Token expired or invalid
                console.error('Unauthorized - clearing tokens and redirecting to login')
                localStorage.removeItem('auth_token')
                localStorage.removeItem('token')
                localStorage.removeItem('jwt_token')
                setError('Session expired. Please log in again.')
                setLoading(false)
                setTimeout(() => {
                    router.push('/login?redirect=/billing')
                }, 2000)
                return
            }

            if (statusResponse.ok) {
                const status = await statusResponse.json()
                setBillingStatus(status)
            } else {
                console.error('Failed to fetch billing status:', statusResponse.status)
            }

            // Fetch credit packs
            const packsResponse = await fetch(`${apiBase}/api/billing/credits/packs`)
            if (packsResponse.ok) {
                const packs = await packsResponse.json()
                setCreditPacks(packs)
            } else {
                console.error('Failed to fetch credit packs:', packsResponse.status)
            }

            // Fetch both credit transactions and payment history
            const [transactionsResponse, paymentHistoryResponse] = await Promise.all([
                fetch(`${apiBase}/api/billing/credits/transactions`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                }),
                fetch(`${apiBase}/api/billing/payments/history?limit=20`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                })
            ])
            
            if (transactionsResponse.status === 401 || paymentHistoryResponse.status === 401) {
                console.error('Unauthorized - session expired')
                localStorage.removeItem('auth_token')
                localStorage.removeItem('token')
                localStorage.removeItem('jwt_token')
                setError('Session expired. Please log in again.')
                setLoading(false)
                setTimeout(() => {
                    router.push('/login?redirect=/billing')
                }, 2000)
                return
            }
            
            // Combine credit transactions and payment history
            const combinedTransactions: CombinedTransaction[] = []
            
            // Add credit transactions
            if (transactionsResponse.ok) {
                const creditTxns: Transaction[] = await transactionsResponse.json()
                creditTxns.forEach(txn => {
                    combinedTransactions.push({
                        id: txn.id,
                        type: 'credit',
                        transaction_type: txn.transaction_type,
                        amount: txn.amount,
                        description: txn.description,
                        created_at: txn.created_at,
                        balance_after: txn.balance_after
                    })
                })
            }
            
            // Add payment history
            if (paymentHistoryResponse.ok) {
                const paymentData = await paymentHistoryResponse.json()
                const paymentHistory: PaymentHistory[] = paymentData.payment_history || []
                paymentHistory.forEach(payment => {
                    combinedTransactions.push({
                        id: payment.id,
                        type: 'payment',
                        transaction_type: payment.payment_type,
                        payment_type: payment.payment_type,
                        status: payment.status,
                        amount: payment.amount_inr,
                        description: `${payment.payment_type} payment - ${payment.status}`,
                        created_at: payment.created_at,
                        payment_method: payment.payment_method,
                        razorpay_payment_id: payment.razorpay_payment_id,
                        failure_reason: payment.failure_reason
                    })
                })
            }
            
            // Sort combined transactions by date (newest first)
            combinedTransactions.sort((a, b) => 
                new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
            )
            
            setTransactions(combinedTransactions)

            setLoading(false)
        } catch (err) {
            console.error('Billing data fetch error:', err)
            setError('Failed to load billing data')
            setLoading(false)
        }
    }

    const handleBuyCredits = async (packId: string) => {
        try {
            const token = localStorage.getItem('auth_token') || 
                         localStorage.getItem('token') || 
                         localStorage.getItem('jwt_token')
            
            if (!token) {
                alert('Please log in to purchase credits')
                router.push('/login?redirect=/billing')
                return
            }

            const apiBase = getApiUrl()

            // Create order
            const orderResponse = await fetch(`${apiBase}/api/billing/credits/create-order`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ pack_id: packId })
            })

            if (orderResponse.status === 401) {
                alert('Session expired. Please log in again.')
                localStorage.removeItem('auth_token')
                localStorage.removeItem('token')
                localStorage.removeItem('jwt_token')
                router.push('/login?redirect=/billing')
                return
            }

            if (!orderResponse.ok) {
                const errorData = await orderResponse.json().catch(() => ({ detail: 'Unknown error' }))
                throw new Error(errorData.detail || 'Failed to create order')
            }

            const { order, pack, user_id } = await orderResponse.json()

            // Load Razorpay if not already loaded
            if (!(window as any).Razorpay) {
                const script = document.createElement('script')
                script.src = 'https://checkout.razorpay.com/v1/checkout.js'
                script.async = true
                document.body.appendChild(script)
                await new Promise((resolve) => {
                    script.onload = resolve
                })
            }

            // Open Razorpay checkout
            const options = {
                key: order.key_id,
                amount: order.amount,
                currency: order.currency,
                name: 'Stocxer AI',
                description: `${pack.name} - ${pack.credits} Credits`,
                order_id: order.order_id,
                handler: async function (response: any) {
                    // Payment successful - verify on backend
                    try {
                        const verifyResponse = await fetch(`${apiBase}/api/billing/credits/verify-payment`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${token}`
                            },
                            body: JSON.stringify({
                                razorpay_order_id: response.razorpay_order_id,
                                razorpay_payment_id: response.razorpay_payment_id,
                                razorpay_signature: response.razorpay_signature
                            })
                        })

                        if (verifyResponse.ok) {
                            const result = await verifyResponse.json()
                            if (result.success) {
                                alert(result.message || 'Payment successful! Credits added to your account.')
                                // Refresh billing data
                                fetchBillingData()
                            } else {
                                console.error('Payment verification failed:', result)
                                alert('Payment verification failed. Please contact support.')
                                // Still refresh data in case webhook processed it
                                fetchBillingData()
                            }
                        } else {
                            // Parse error response
                            let errorMessage = 'Payment verification failed.'
                            try {
                                const errorData = await verifyResponse.json()
                                errorMessage = errorData.detail || errorMessage
                                console.error('Payment verification HTTP error:', errorData)
                            } catch {
                                const errorText = await verifyResponse.text()
                                console.error('Payment verification HTTP error:', errorText)
                            }
                            
                            // Check if payment was already processed (webhook may have handled it)
                            alert('Payment processing... Please wait while we verify your payment.')
                            
                            // Refresh billing data to check if webhook processed it
                            setTimeout(() => {
                                fetchBillingData()
                                // Check again after refresh if credits were added
                                setTimeout(() => {
                                    alert('Payment completed! Please refresh the page if you don\'t see your credits.')
                                }, 1000)
                            }, 2000)
                        }
                    } catch (error) {
                        console.error('Verification error:', error)
                        alert('Payment is being processed. Please refresh the page in a few seconds to see your credits.')
                        // Refresh billing data anyway - webhook might have processed it
                        setTimeout(() => fetchBillingData(), 2000)
                    }
                },
                prefill: {
                    email: localStorage.getItem('userEmail') || ''
                },
                theme: {
                    color: '#3b82f6'
                },
                modal: {
                    ondismiss: function() {
                        console.log('Payment cancelled by user')
                    }
                }
            }

            const rzp = new (window as any).Razorpay(options)
            rzp.open()

        } catch (err) {
            console.error('Purchase error:', err)
            alert('Failed to initiate purchase')
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-[#0a0a0f]">
                <div className="text-white text-xl">Loading billing data...</div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen bg-[#0a0a0f] p-4">
                <div className="max-w-md w-full bg-white/5 border border-red-500/30 rounded-2xl p-8 text-center">
                    <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
                        <AlertCircle className="w-8 h-8 text-red-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Authentication Required</h2>
                    <p className="text-red-400 mb-6">{error}</p>
                    <button
                        onClick={() => router.push('/login?redirect=/billing')}
                        className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-semibold transition-all"
                    >
                        Go to Login
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-[#0a0a0f] text-white p-6">
            <div className="max-w-7xl mx-auto">
                <h1 className="text-4xl font-bold mb-8 bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                    Billing & Credits
                </h1>

                {/* Current Plan Section */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    {/* Plan Card */}
                    <div className="bg-white/5 border border-purple-500/30 rounded-2xl p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-3 rounded-xl bg-gradient-to-br from-purple-600 to-blue-600">
                                <Zap className="w-6 h-6" />
                            </div>
                            <div>
                                <div className="text-gray-400 text-sm">Current Plan</div>
                                <div className="text-2xl font-bold capitalize">{billingStatus?.plan_type || 'Free'}</div>
                            </div>
                        </div>
                        {billingStatus?.subscription_active && (
                            <div className="text-sm text-gray-400">
                                Renews: {new Date(billingStatus.subscription_end || '').toLocaleDateString()}
                            </div>
                        )}
                    </div>

                    {/* Credits Balance */}
                    <div className="bg-white/5 border border-green-500/30 rounded-2xl p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-3 rounded-xl bg-gradient-to-br from-green-600 to-emerald-600">
                                <CreditCard className="w-6 h-6" />
                            </div>
                            <div>
                                <div className="text-gray-400 text-sm">Credits Balance</div>
                                <div className="text-2xl font-bold">₹{billingStatus?.credits_balance?.toFixed(2) || '0.00'}</div>
                            </div>
                        </div>
                        <button
                            onClick={() => document.getElementById('credit-packs')?.scrollIntoView({ behavior: 'smooth' })}
                            className="w-full py-2 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 transition-all font-semibold"
                        >
                            Buy Credits
                        </button>
                    </div>

                    {/* Today's Usage */}
                    <div className="bg-white/5 border border-cyan-500/30 rounded-2xl p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-600 to-blue-600">
                                <TrendingUp className="w-6 h-6" />
                            </div>
                            <div>
                                <div className="text-gray-400 text-sm">Today's Usage</div>
                                <div className="text-2xl font-bold">{billingStatus?.today_usage.option_scans || 0} Scans</div>
                            </div>
                        </div>
                        <div className="text-sm text-gray-400">
                            {billingStatus?.limits.daily_option_scans 
                                ? `Limit: ${billingStatus.limits.daily_option_scans}/day`
                                : 'Unlimited'}
                        </div>
                    </div>
                </div>

                {/* Credit Packs Section */}
                <div id="credit-packs" className="mb-8">
                    <h2 className="text-2xl font-bold mb-4">Buy Credit Packs</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
                        {creditPacks.map((pack) => (
                            <div key={pack.id} className="bg-white/5 border border-green-500/30 rounded-xl p-6 hover:border-green-500/60 transition-all">
                                <div className="flex items-center gap-2 mb-2">
                                    <ShoppingCart className="w-5 h-5 text-green-400" />
                                    <h3 className="font-bold">{pack.name}</h3>
                                </div>
                                <div className="text-3xl font-bold text-white mb-2">₹{pack.amount_inr}</div>
                                <div className="text-sm text-gray-400 mb-1">
                                    {pack.credits} credits
                                </div>
                                {pack.bonus_credits > 0 && (
                                    <div className="text-xs text-green-400 mb-3">
                                        + {pack.bonus_credits} bonus!
                                    </div>
                                )}
                                <button
                                    onClick={() => handleBuyCredits(pack.id)}
                                    className="w-full py-2 rounded-lg bg-green-600 hover:bg-green-500 transition-all font-semibold text-sm"
                                >
                                    Buy Now
                                </button>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Recent Transactions */}
                <div>
                    <h2 className="text-2xl font-bold mb-4">Recent Transactions</h2>
                    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                        {transactions.length === 0 ? (
                            <div className="p-8 text-center text-gray-400">
                                No transactions yet
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead className="bg-white/5">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                                Type
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                                Description
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                                Amount
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                                Balance
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                                Date
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/10">
                                        {transactions.map((txn) => (
                                            <tr key={txn.id}>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                                                        // Credit transactions
                                                        txn.type === 'credit' && txn.transaction_type === 'purchase' ? 'bg-green-500/20 text-green-400' :
                                                        txn.type === 'credit' && txn.transaction_type === 'debit' ? 'bg-red-500/20 text-red-400' :
                                                        // Payment history - subscription
                                                        txn.type === 'payment' && txn.payment_type === 'subscription' && txn.status === 'captured' ? 'bg-purple-500/20 text-purple-400' :
                                                        txn.type === 'payment' && txn.payment_type === 'subscription' && txn.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                                                        // Payment history - credits
                                                        txn.type === 'payment' && txn.payment_type === 'credits' && txn.status === 'captured' ? 'bg-green-500/20 text-green-400' :
                                                        txn.type === 'payment' && txn.payment_type === 'credits' && txn.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                                                        'bg-blue-500/20 text-blue-400'
                                                    }`}>
                                                        {(txn.transaction_type === 'purchase' || (txn.status === 'captured' && txn.payment_type === 'credits')) && <CheckCircle className="w-3 h-3" />}
                                                        {txn.transaction_type === 'debit' && <AlertCircle className="w-3 h-3" />}
                                                        {txn.status === 'captured' && txn.payment_type === 'subscription' && <TrendingUp className="w-3 h-3" />}
                                                        {txn.status === 'failed' && <AlertCircle className="w-3 h-3" />}
                                                        {txn.type === 'credit' ? 
                                                            (txn.transaction_type.charAt(0).toUpperCase() + txn.transaction_type.slice(1)) :
                                                            `${txn.payment_type?.charAt(0).toUpperCase()}${txn.payment_type?.slice(1)} ${txn.status?.charAt(0).toUpperCase()}${txn.status?.slice(1)}`
                                                        }
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="text-sm">
                                                        <div className="text-white">{txn.description}</div>
                                                        {txn.type === 'payment' && txn.payment_method && (
                                                            <div className="text-xs text-gray-400 mt-1">
                                                                Via {txn.payment_method}
                                                                {txn.razorpay_payment_id && (
                                                                    <span className="ml-2">ID: {txn.razorpay_payment_id.slice(-8)}</span>
                                                                )}
                                                            </div>
                                                        )}
                                                        {txn.failure_reason && (
                                                            <div className="text-xs text-red-400 mt-1">{txn.failure_reason}</div>
                                                        )}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className={`text-sm font-medium ${
                                                        // Credit transactions
                                                        txn.type === 'credit' && txn.transaction_type === 'purchase' ? 'text-green-400' :
                                                        txn.type === 'credit' && txn.transaction_type === 'debit' ? 'text-red-400' :
                                                        // Payment history - successful
                                                        txn.type === 'payment' && txn.status === 'captured' ? 'text-green-400' :
                                                        // Payment history - failed
                                                        txn.type === 'payment' && txn.status === 'failed' ? 'text-red-400' :
                                                        'text-white'
                                                    }`}>
                                                        {txn.type === 'credit' ? (
                                                            `${txn.transaction_type === 'purchase' ? '+' : '-'}${txn.amount} credits`
                                                        ) : (
                                                            `₹${txn.amount}`
                                                        )}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                                                    {txn.type === 'credit' && txn.balance_after !== undefined ? 
                                                        `${txn.balance_after} credits` : 
                                                        txn.type === 'payment' && txn.payment_type === 'subscription' ? 
                                                            (txn.status === 'captured' ? 'Subscription Active' : 'Failed') :
                                                            '-'
                                                    }
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                                                    {new Date(txn.created_at).toLocaleDateString()}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
