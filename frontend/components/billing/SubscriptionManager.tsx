'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
    Crown, 
    Zap, 
    Sparkles, 
    Calendar, 
    CreditCard, 
    AlertTriangle, 
    CheckCircle,
    ArrowRight,
    X,
    Coins,
    TrendingUp,
    Info
} from 'lucide-react'
import { getApiUrl } from '@/lib/config'

interface SubscriptionDetails {
    user_id: string
    plan_type: string
    subscription_active: boolean
    subscription_start: string | null
    subscription_end: string | null
    auto_renew: boolean
    payment_method: string | null
    amount_paid: number
    next_billing_date: string | null
}

interface CreditBalance {
    balance: number
    lifetime_purchased: number
    lifetime_spent: number
}

interface CreditPack {
    id: string
    name: string
    amount_inr: number
    credits: number
    bonus_credits: number
    total_credits: number
}

interface PlanOption {
    id: string
    name: string
    price: number
    period: string
    features: string[]
    recommended?: boolean
    icon: any
    gradient: string
}

const plans: PlanOption[] = [
    {
        id: 'free',
        name: 'Free Trial',
        price: 0,
        period: 'forever',
        features: [
            '100 credits to explore',
            'All features included',
            'No card required'
        ],
        icon: Sparkles,
        gradient: 'from-gray-600 to-gray-700',
    },
    {
        id: 'medium',
        name: 'Medium',
        price: 4999,
        period: 'month',
        features: [
            '30,000 scans/month',
            'Watchman AI v3.5',
            '25 stocks per bulk scan',
            'Email support'
        ],
        recommended: true,
        icon: Zap,
        gradient: 'from-purple-600 to-blue-600',
    },
    {
        id: 'pro',
        name: 'Pro',
        price: 9999,
        period: 'month',
        features: [
            '150,000 scans/month',
            'Unlimited bulk scans',
            'Accuracy tracking',
            'Historical data',
            'Priority support',
            'Early access'
        ],
        icon: Crown,
        gradient: 'from-cyan-600 to-blue-600',
    },
]

export default function SubscriptionManager() {
    const router = useRouter()
    const [subscription, setSubscription] = useState<SubscriptionDetails | null>(null)
    const [creditBalance, setCreditBalance] = useState<CreditBalance | null>(null)
    const [creditPacks, setCreditPacks] = useState<CreditPack[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [showCancelModal, setShowCancelModal] = useState(false)
    const [cancelling, setCancelling] = useState(false)

    useEffect(() => {
        // Check if user is logged in before fetching data
        const token = localStorage.getItem('auth_token') || 
                     localStorage.getItem('token') || 
                     localStorage.getItem('jwt_token')
        
        if (!token) {
            setError('Please log in to view subscription details')
            setLoading(false)
            return
        }
        
        fetchSubscriptionData()
        fetchCreditData()
    }, [])

    const fetchSubscriptionData = async () => {
        try {
            const token = localStorage.getItem('auth_token') || 
                         localStorage.getItem('token') || 
                         localStorage.getItem('jwt_token')
            
            console.log('Subscription token check:', { 
                auth_token: !!localStorage.getItem('auth_token'),
                token: !!localStorage.getItem('token'),
                jwt_token: !!localStorage.getItem('jwt_token'),
                hasToken: !!token
            })
            
            if (!token) {
                setError('Please log in to view subscription')
                setLoading(false)
                setTimeout(() => {
                    router.push('/login?redirect=/subscription')
                }, 2000)
                return
            }

            const apiBase = getApiUrl()
            const response = await fetch(`${apiBase}/api/billing/subscription/details`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })

            if (response.status === 401) {
                console.error('Unauthorized - clearing tokens and redirecting to login')
                localStorage.removeItem('auth_token')
                localStorage.removeItem('token')
                localStorage.removeItem('jwt_token')
                setError('Session expired. Please log in again.')
                setLoading(false)
                setTimeout(() => {
                    router.push('/login?redirect=/subscription')
                }, 2000)
                return
            }

            if (response.ok) {
                const data = await response.json()
                setSubscription(data)
            } else {
                console.error('Failed to load subscription:', response.status)
                setError('Failed to load subscription details')
            }

            setLoading(false)
        } catch (err) {
            console.error('Subscription fetch error:', err)
            setError('Failed to load subscription data')
            setLoading(false)
        }
    }

    const fetchCreditData = async () => {
        try {
            const token = localStorage.getItem('auth_token') || 
                         localStorage.getItem('token') || 
                         localStorage.getItem('jwt_token')
            
            if (!token) return

            const apiBase = getApiUrl()
            
            // Fetch credit balance from billing status
            const statusResponse = await fetch(`${apiBase}/api/billing/status`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })
            
            if (statusResponse.ok) {
                const statusData = await statusResponse.json()
                setCreditBalance({
                    balance: statusData.credit_balance || 0,
                    lifetime_purchased: statusData.lifetime_credits_purchased || 0,
                    lifetime_spent: statusData.lifetime_credits_spent || 0
                })
            }
            
            // Fetch available credit packs (public endpoint)
            const packsResponse = await fetch(`${apiBase}/api/billing/credits/packs`)
            if (packsResponse.ok) {
                const packsData = await packsResponse.json()
                setCreditPacks(packsData)
            }
        } catch (err) {
            console.error('Error fetching credit data:', err)
        }
    }

    const handleUpgrade = async (planId: string) => {
        const plan = plans.find(p => p.id === planId)
        if (!plan || plan.price === 0) return

        try {
            const token = localStorage.getItem('auth_token') || 
                         localStorage.getItem('token') || 
                         localStorage.getItem('jwt_token')
            
            if (!token) {
                alert('Please log in to upgrade')
                router.push('/login?redirect=/subscription')
                return
            }

            const apiBase = getApiUrl()

            // Create subscription order (regular payment, not recurring)
            const orderResponse = await fetch(`${apiBase}/api/billing/subscription/create-order`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ 
                    plan_type: planId,
                    billing_period: 'monthly'
                })
            })

            if (!orderResponse.ok) {
                const errorData = await orderResponse.json()
                throw new Error(errorData.detail || 'Failed to create subscription order')
            }

            const { order } = await orderResponse.json()

            // Load Razorpay
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
                description: `${plan.name} Plan - Monthly`,
                order_id: order.order_id,
                handler: async function (response: any) {
                    try {
                        const verifyResponse = await fetch(`${apiBase}/api/billing/subscription/verify-payment`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${token}`
                            },
                            body: JSON.stringify({
                                razorpay_order_id: response.razorpay_order_id,
                                razorpay_payment_id: response.razorpay_payment_id,
                                razorpay_signature: response.razorpay_signature,
                                plan_type: planId
                            })
                        })

                        if (verifyResponse.ok) {
                            const result = await verifyResponse.json()
                            if (result.success) {
                                alert(result.message || 'Subscription activated successfully!')
                                fetchSubscriptionData()
                            } else {
                                console.error('Subscription verification failed:', result)
                                alert('Payment verification failed. Please contact support.')
                            }
                        } else {
                            const errorText = await verifyResponse.text()
                            console.error('Subscription verification HTTP error:', errorText)
                            alert('Payment verification failed. Please contact support.')
                        }
                    } catch (error) {
                        console.error('Verification error:', error)
                        alert('Payment verification failed. Please contact support.')
                    }
                },
                prefill: {
                    email: localStorage.getItem('userEmail') || ''
                },
                theme: {
                    color: '#8b5cf6'
                }
            }

            const rzp = new (window as any).Razorpay(options)
            rzp.open()

        } catch (err) {
            console.error('Subscription creation error:', err)
            alert(err instanceof Error ? err.message : 'Failed to create subscription')
        }
    }

    const handleCancelSubscription = async () => {
        setCancelling(true)
        try {
            const token = localStorage.getItem('auth_token') || 
                         localStorage.getItem('token') || 
                         localStorage.getItem('jwt_token')
            
            if (!token) {
                alert('Please log in')
                return
            }

            const apiBase = getApiUrl()
            const response = await fetch(`${apiBase}/api/billing/subscription/cancel`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })

            if (response.ok) {
                alert('Subscription cancelled successfully. You can continue using your plan until the end of the billing period.')
                setShowCancelModal(false)
                fetchSubscriptionData()
            } else {
                alert('Failed to cancel subscription. Please contact support.')
            }
        } catch (err) {
            console.error('Cancel error:', err)
            alert('Failed to cancel subscription')
        } finally {
            setCancelling(false)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-[#0a0a0f]">
                <div className="text-white text-xl">Loading subscription details...</div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen bg-[#0a0a0f] p-4">
                <div className="max-w-md w-full bg-white/5 border border-red-500/30 rounded-2xl p-8 text-center">
                    <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
                        <AlertTriangle className="w-8 h-8 text-red-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Authentication Required</h2>
                    <p className="text-red-400 mb-6">{error}</p>
                    <button
                        onClick={() => router.push('/login?redirect=/subscription')}
                        className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-semibold transition-all"
                    >
                        Go to Login
                    </button>
                </div>
            </div>
        )
    }

    const currentPlan = plans.find(p => p.id === subscription?.plan_type) || plans[0]

    return (
        <div className="min-h-screen bg-[#0a0a0f] text-white p-6">
            <div className="max-w-7xl mx-auto">
                <h1 className="text-4xl font-bold mb-8 bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                    Subscription Manager
                </h1>

                {/* Current Subscription Status */}
                <div className="mb-12">
                    <h2 className="text-2xl font-bold mb-4">Current Plan</h2>
                    <div className="bg-gradient-to-br from-white/10 to-white/5 border border-purple-500/30 rounded-2xl p-8">
                        <div className="flex items-start justify-between">
                            <div className="flex items-center gap-4">
                                <div className={`p-4 rounded-2xl bg-gradient-to-br ${currentPlan.gradient}`}>
                                    <currentPlan.icon className="w-8 h-8" />
                                </div>
                                <div>
                                    <h3 className="text-3xl font-bold mb-1">{currentPlan.name}</h3>
                                    <p className="text-gray-400">
                                        {currentPlan.price === 0 
                                            ? 'Free Plan' 
                                            : `₹${currentPlan.price.toLocaleString()}/${currentPlan.period}`}
                                    </p>
                                </div>
                            </div>
                            
                            {subscription?.subscription_active && (
                                <div className="text-right">
                                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-sm font-medium mb-2">
                                        <CheckCircle className="w-4 h-4" />
                                        Active
                                    </div>
                                    <p className="text-sm text-gray-400">
                                        Renews: {subscription.next_billing_date 
                                            ? new Date(subscription.next_billing_date).toLocaleDateString('en-IN', {
                                                year: 'numeric',
                                                month: 'long',
                                                day: 'numeric'
                                            })
                                            : 'N/A'}
                                    </p>
                                </div>
                            )}
                        </div>

                        <div className="mt-6 pt-6 border-t border-white/10">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {subscription?.subscription_active && (
                                    <>
                                        <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
                                            <Calendar className="w-5 h-5 text-purple-400" />
                                            <div>
                                                <div className="text-xs text-gray-400">Started</div>
                                                <div className="text-sm font-medium">
                                                    {new Date(subscription.subscription_start || '').toLocaleDateString()}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
                                            <CreditCard className="w-5 h-5 text-green-400" />
                                            <div>
                                                <div className="text-xs text-gray-400">Last Payment</div>
                                                <div className="text-sm font-medium">₹{subscription.amount_paid.toLocaleString()}</div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
                                            <AlertTriangle className="w-5 h-5 text-yellow-400" />
                                            <div>
                                                <div className="text-xs text-gray-400">Auto-Renew</div>
                                                <div className="text-sm font-medium">
                                                    {subscription.auto_renew ? 'Enabled' : 'Disabled'}
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>

                        {subscription?.subscription_active && (
                            <div className="mt-6 flex gap-4">
                                <button
                                    onClick={() => setShowCancelModal(true)}
                                    className="px-6 py-2 rounded-xl border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-all"
                                >
                                    Cancel Subscription
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Pay-As-You-Go Credits */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <Coins className="w-6 h-6 text-yellow-400" />
                        <h2 className="text-2xl font-bold">Pay-As-You-Go Credits</h2>
                    </div>
                    
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-6 mb-6">
                        {/* Credit Balance */}
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <div className="text-sm text-gray-400 mb-1">Current Balance</div>
                                <div className="text-4xl font-bold text-yellow-400">
                                    {creditBalance ? creditBalance.balance.toFixed(2) : '0.00'}
                                    <span className="text-xl text-gray-400 ml-2">credits</span>
                                </div>
                            </div>
                            <button
                                onClick={() => router.push('/billing')}
                                className="px-6 py-3 rounded-xl bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-500 hover:to-orange-500 transition-all font-semibold flex items-center gap-2"
                            >
                                <TrendingUp className="w-5 h-5" />
                                Buy Credits
                            </button>
                        </div>

                        {/* PAYG Stats */}
                        {creditBalance && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-6 border-t border-white/10">
                                <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
                                    <TrendingUp className="w-5 h-5 text-green-400" />
                                    <div>
                                        <div className="text-xs text-gray-400">Total Purchased</div>
                                        <div className="text-sm font-medium">
                                            {creditBalance.lifetime_purchased.toFixed(2)} credits
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
                                    <Coins className="w-5 h-5 text-blue-400" />
                                    <div>
                                        <div className="text-xs text-gray-400">Total Spent</div>
                                        <div className="text-sm font-medium">
                                            {creditBalance.lifetime_spent.toFixed(2)} credits
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* PAYG Pricing Info */}
                        <div className="mt-6 pt-6 border-t border-white/10">
                            <div className="flex items-start gap-2 mb-4">
                                <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                                <div>
                                    <h3 className="font-semibold mb-2">How PAYG Works</h3>
                                    <p className="text-sm text-gray-400 leading-relaxed">
                                        Buy credits only when you need them. No monthly commitment. Credits never expire.
                                    </p>
                                </div>
                            </div>
                            
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between items-center p-2 rounded bg-white/5">
                                    <span className="text-gray-400">Option Scan</span>
                                    <span className="font-semibold">₹0.98 per scan</span>
                                </div>
                                <div className="flex justify-between items-center p-2 rounded bg-white/5">
                                    <span className="text-gray-400">Stock Scan</span>
                                    <span className="font-semibold">₹0.85 per scan</span>
                                </div>
                                <div className="flex justify-between items-center p-2 rounded bg-white/5">
                                    <span className="text-gray-400">Bulk Scan (25 stocks)</span>
                                    <span className="font-semibold">₹17.50 per batch</span>
                                </div>
                            </div>

                            {/* Credit Packs Preview */}
                            {creditPacks.length > 0 && (
                                <div className="mt-6">
                                    <h4 className="text-sm font-semibold mb-3">Available Credit Packs</h4>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                        {creditPacks.slice(0, 4).map((pack) => (
                                            <div key={pack.id} className="p-3 rounded-lg border border-white/10 bg-white/5 text-center">
                                                <div className="text-lg font-bold text-yellow-400">
                                                    {pack.total_credits}
                                                </div>
                                                <div className="text-xs text-gray-400 mb-1">credits</div>
                                                <div className="text-sm font-semibold">₹{pack.amount_inr}</div>
                                                {pack.bonus_credits > 0 && (
                                                    <div className="text-xs text-green-400 mt-1">
                                                        +{pack.bonus_credits} bonus
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Available Plans */}
                <div>
                    <h2 className="text-2xl font-bold mb-4">
                        {subscription?.subscription_active ? 'Change Plan' : 'Choose Your Plan'}
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {plans.map((plan) => {
                            const isCurrentPlan = plan.id === subscription?.plan_type
                            const Icon = plan.icon

                            return (
                                <div
                                    key={plan.id}
                                    className={`relative rounded-2xl p-6 border transition-all ${
                                        plan.recommended
                                            ? 'border-purple-500/50 bg-gradient-to-b from-purple-500/10 to-transparent'
                                            : 'border-white/10 bg-white/5'
                                    } ${isCurrentPlan ? 'ring-2 ring-green-500' : ''}`}
                                >
                                    {plan.recommended && (
                                        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                                            <span className="px-4 py-1 rounded-full bg-gradient-to-r from-purple-600 to-blue-600 text-xs font-semibold">
                                                Most Popular
                                            </span>
                                        </div>
                                    )}

                                    {isCurrentPlan && (
                                        <div className="absolute -top-3 right-4">
                                            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-green-500 text-white text-xs font-semibold">
                                                <CheckCircle className="w-3 h-3" />
                                                Current Plan
                                            </span>
                                        </div>
                                    )}

                                    <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${plan.gradient} mb-4`}>
                                        <Icon className="w-6 h-6" />
                                    </div>

                                    <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                                    <div className="mb-4">
                                        {plan.price === 0 ? (
                                            <span className="text-3xl font-bold">Free</span>
                                        ) : (
                                            <>
                                                <span className="text-3xl font-bold">₹{plan.price.toLocaleString()}</span>
                                                <span className="text-gray-400">/{plan.period}</span>
                                            </>
                                        )}
                                    </div>

                                    <ul className="space-y-3 mb-6">
                                        {plan.features.map((feature, index) => (
                                            <li key={index} className="flex items-start gap-2 text-sm text-gray-300">
                                                <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                                                {feature}
                                            </li>
                                        ))}
                                    </ul>

                                    <button
                                        onClick={() => !isCurrentPlan && plan.price > 0 && handleUpgrade(plan.id)}
                                        disabled={isCurrentPlan || plan.price === 0}
                                        className={`w-full py-3 rounded-xl font-semibold transition-all ${
                                            isCurrentPlan
                                                ? 'bg-gray-600 cursor-not-allowed'
                                                : plan.price === 0
                                                ? 'bg-gray-700 cursor-not-allowed'
                                                : `bg-gradient-to-r ${plan.gradient} hover:opacity-90`
                                        }`}
                                    >
                                        {isCurrentPlan ? 'Current Plan' : plan.price === 0 ? 'Free Trial' : 'Upgrade Now'}
                                    </button>
                                </div>
                            )
                        })}
                    </div>
                </div>
            </div>

            {/* Cancel Confirmation Modal */}
            {showCancelModal && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#1a1a2e] border border-red-500/30 rounded-2xl p-8 max-w-md w-full">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-3 rounded-xl bg-red-500/20">
                                <AlertTriangle className="w-6 h-6 text-red-400" />
                            </div>
                            <h3 className="text-2xl font-bold">Cancel Subscription?</h3>
                        </div>

                        <p className="text-gray-400 mb-6">
                            Are you sure you want to cancel your subscription? You'll continue to have access until{' '}
                            {subscription?.subscription_end 
                                ? new Date(subscription.subscription_end).toLocaleDateString()
                                : 'the end of your billing period'}.
                        </p>

                        <div className="flex gap-4">
                            <button
                                onClick={() => setShowCancelModal(false)}
                                disabled={cancelling}
                                className="flex-1 py-3 rounded-xl border border-white/10 hover:bg-white/5 transition-all"
                            >
                                Keep Subscription
                            </button>
                            <button
                                onClick={handleCancelSubscription}
                                disabled={cancelling}
                                className="flex-1 py-3 rounded-xl bg-red-600 hover:bg-red-500 transition-all font-semibold disabled:opacity-50"
                            >
                                {cancelling ? 'Cancelling...' : 'Yes, Cancel'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
