'use client'

import {
    Brain,
    Layout,
    Filter,
    User,
    History,
    Smartphone,
    CheckCircle2
} from 'lucide-react'

const benefits = [
    {
        icon: Brain,
        title: 'Deep Analysis Without Clutter',
        description: 'Get sophisticated market analysis powered by Watchman AI v3.5 without information overload.',
        features: ['Multi-timeframe analysis', 'Probability scoring', 'Pattern recognition'],
    },
    {
        icon: Layout,
        title: 'Clean Data Presentation',
        description: 'View processed, relevant insights in an intuitive interface designed for quick decision-making.',
        features: ['Visual dashboards', 'Real-time updates', 'Organized layouts'],
    },
    {
        icon: Filter,
        title: 'No Option Chain Overload',
        description: 'Skip the complexity of raw option chains. See only what matters for your analysis.',
        features: ['Filtered data', 'Key metrics only', 'Noise reduction'],
    },
    {
        icon: User,
        title: 'User-Specific Dashboards',
        description: 'Access your personalized dashboard with insights tailored to your scanning preferences.',
        features: ['Personal scan history', 'Saved preferences', 'Custom alerts'],
    },
    {
        icon: History,
        title: 'Accuracy Tracking',
        description: 'Track the historical performance of analytical models for transparency and continuous improvement.',
        features: ['Performance metrics', 'Historical records', 'Model accuracy'],
    },
    {
        icon: Smartphone,
        title: 'Mobile-Friendly Interface',
        description: 'Access Stocxer AI on any device with a fully responsive, touch-optimized experience.',
        features: ['Responsive design', 'Touch gestures', 'Offline support'],
    },
]

export default function BenefitsSection() {
    return (
        <section className="py-24 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
            {/* Background */}
            <div className="absolute inset-0 bg-gradient-to-b from-[#0a0a0f] via-[#0a0f14] to-[#0a0a0f]" />

            {/* Gradient Orb */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-blue-600/5 rounded-full blur-[120px]" />

            <div className="relative z-10 max-w-6xl mx-auto">
                {/* Section Header */}
                <div className="text-center mb-16">
                    <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
                        <span className="text-white">Key </span>
                        <span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                            Benefits
                        </span>
                    </h2>
                    <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                        Why traders choose Stocxer AI for their market analytics needs
                    </p>
                </div>

                {/* Benefits Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {benefits.map((benefit, index) => (
                        <div
                            key={index}
                            className="group relative p-6 rounded-2xl bg-gradient-to-b from-white/5 to-transparent border border-white/10 hover:border-cyan-500/30 transition-all duration-300"
                        >
                            {/* Icon */}
                            <div className="inline-flex p-3 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 mb-4">
                                <benefit.icon className="w-6 h-6 text-white" />
                            </div>

                            {/* Content */}
                            <h3 className="text-xl font-semibold text-white mb-2 group-hover:text-cyan-400 transition-colors">
                                {benefit.title}
                            </h3>
                            <p className="text-gray-400 text-sm mb-4 leading-relaxed">
                                {benefit.description}
                            </p>

                            {/* Features List */}
                            <ul className="space-y-2">
                                {benefit.features.map((feature, i) => (
                                    <li key={i} className="flex items-center gap-2 text-sm text-gray-500">
                                        <CheckCircle2 className="w-4 h-4 text-cyan-500" />
                                        {feature}
                                    </li>
                                ))}
                            </ul>

                            {/* Hover Glow */}
                            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-500 opacity-0 group-hover:opacity-5 transition-opacity duration-300" />
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}
