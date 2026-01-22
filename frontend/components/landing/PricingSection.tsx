'use client'

import { Check, Sparkles, Zap, Crown } from 'lucide-react'

const plans = [
    {
        name: 'Free',
        price: '₹0',
        period: 'forever',
        description: 'Get started with basic market analytics',
        icon: Sparkles,
        features: [
            'Limited scans per day',
            'Basic dashboard access',
            'Index overview data',
            'Community support',
        ],
        cta: 'Get Started Free',
        popular: false,
        gradient: 'from-gray-600 to-gray-700',
        borderColor: 'border-gray-700',
    },
    {
        name: 'Starter',
        price: '₹499',
        period: '/month',
        description: 'Perfect for active traders seeking insights',
        icon: Zap,
        features: [
            'Live index scanner',
            'Stock screener access',
            'Latest insights per instrument',
            'Watchman AI v3.5 analysis',
            'Email support',
            'Mobile app access',
        ],
        cta: 'Start Starter Plan',
        popular: true,
        gradient: 'from-purple-600 to-blue-600',
        borderColor: 'border-purple-500',
    },
    {
        name: 'Pro',
        price: '₹999',
        period: '/month',
        description: 'Full access to all analytics features',
        icon: Crown,
        features: [
            'Everything in Starter',
            'Full scanner access',
            'Accuracy tracking dashboard',
            'Advanced analytical features',
            'Historical data access',
            'Priority support',
            'Early access to new features',
        ],
        cta: 'Go Pro',
        popular: false,
        gradient: 'from-cyan-600 to-blue-600',
        borderColor: 'border-cyan-700',
    },
]

export default function PricingSection() {
    return (
        <section className="py-24 px-4 sm:px-6 lg:px-8 bg-[#0a0a0f]">
            <div className="max-w-6xl mx-auto">
                {/* Section Header */}
                <div className="text-center mb-16">
                    <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
                        <span className="text-white">Simple, </span>
                        <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                            Transparent
                        </span>
                        <span className="text-white"> Pricing</span>
                    </h2>
                    <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                        Choose the plan that fits your trading journey. No hidden fees, no aggressive upsells.
                    </p>
                </div>

                {/* Pricing Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
                    {plans.map((plan, index) => (
                        <div
                            key={index}
                            className={`relative rounded-2xl bg-gradient-to-b from-white/5 to-transparent border ${plan.borderColor} p-8 ${plan.popular ? 'ring-2 ring-purple-500/50 scale-[1.02]' : ''
                                } hover:scale-[1.02] transition-all duration-300`}
                        >
                            {/* Popular Badge */}
                            {plan.popular && (
                                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-purple-600 to-blue-600 text-white text-sm font-semibold">
                                    Most Popular
                                </div>
                            )}

                            {/* Plan Icon */}
                            <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${plan.gradient} mb-4`}>
                                <plan.icon className="w-6 h-6 text-white" />
                            </div>

                            {/* Plan Name */}
                            <h3 className="text-2xl font-bold text-white mb-2">{plan.name}</h3>

                            {/* Price */}
                            <div className="flex items-baseline gap-1 mb-2">
                                <span className="text-4xl font-bold text-white">{plan.price}</span>
                                <span className="text-gray-500">{plan.period}</span>
                            </div>

                            {/* Description */}
                            <p className="text-gray-400 text-sm mb-6">{plan.description}</p>

                            {/* Features */}
                            <ul className="space-y-3 mb-8">
                                {plan.features.map((feature, i) => (
                                    <li key={i} className="flex items-start gap-3 text-sm text-gray-300">
                                        <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                                        {feature}
                                    </li>
                                ))}
                            </ul>

                            {/* CTA Button */}
                            <button
                                className={`w-full py-3 rounded-xl font-semibold transition-all duration-300 ${plan.popular
                                        ? 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white shadow-lg shadow-purple-500/25'
                                        : 'bg-white/10 hover:bg-white/20 text-white'
                                    }`}
                            >
                                {plan.cta}
                            </button>
                        </div>
                    ))}
                </div>

                {/* Bottom Notes */}
                <div className="mt-12 text-center space-y-2">
                    <p className="text-gray-500 text-sm">
                        All prices are in Indian Rupees (₹). GST applicable as per regulations.
                    </p>
                    <p className="text-gray-500 text-sm">
                        Cancel anytime. No long-term commitments required.
                    </p>
                </div>
            </div>
        </section>
    )
}
