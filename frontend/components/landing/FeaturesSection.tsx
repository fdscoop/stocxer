'use client'

import {
    TrendingUp,
    Brain,
    Calculator,
    Newspaper,
    Shield,
    LayoutDashboard,
    Layers,
    Activity
} from 'lucide-react'

const features = [
    {
        icon: TrendingUp,
        title: 'ICT Top-Down + AMD Detection',
        description: 'Multi-timeframe ICT analysis across 6 timeframes (Monthly to 15min) with Accumulation, Manipulation & Distribution phase detection — no other Indian platform offers this.',
        color: 'from-blue-500 to-cyan-500',
        bgColor: 'bg-blue-500/10',
        borderColor: 'border-blue-500/20',
    },
    {
        icon: Brain,
        title: 'ML Direction, Speed & IV Models',
        description: '5+ ML models predict price direction, move speed, IV contraction/expansion, and generate trade grades (A–F) with win probability scores.',
        color: 'from-purple-500 to-pink-500',
        bgColor: 'bg-purple-500/10',
        borderColor: 'border-purple-500/20',
    },
    {
        icon: Calculator,
        title: 'P&L Simulation & Theta Scenarios',
        description: 'Full options P&L simulation across 5 scenarios (best to worst case) with Greek-based theta decay projections at 15min, 30min, 1hr, 2hr, and EOD horizons.',
        color: 'from-green-500 to-emerald-500',
        bgColor: 'bg-green-500/10',
        borderColor: 'border-green-500/20',
    },
    {
        icon: Newspaper,
        title: 'News Sentiment & Constituent Scanning',
        description: 'Real-time sentiment scoring from market news plus Nifty 50 constituent probability analysis showing bullish/bearish stock breakdown.',
        color: 'from-yellow-500 to-orange-500',
        bgColor: 'bg-yellow-500/10',
        borderColor: 'border-yellow-500/20',
    },
    {
        icon: Shield,
        title: 'Confidence Stack & Risk Assessment',
        description: 'Weighted confidence breakdown across ICT structure, LTF confirmation, ML alignment, candlestick patterns, futures basis, and constituents.',
        color: 'from-cyan-500 to-blue-500',
        bgColor: 'bg-cyan-500/10',
        borderColor: 'border-cyan-500/20',
    },
    {
        icon: Activity,
        title: 'Scalp Feasibility & Intraday Mode',
        description: 'Auto-detects trading mode (intraday/swing), calculates scalp targets with index move requirements, per-lot P&L, and theta impact per minute.',
        color: 'from-pink-500 to-purple-500',
        bgColor: 'bg-pink-500/10',
        borderColor: 'border-pink-500/20',
    },
]

export default function FeaturesSection() {
    return (
        <section className="py-24 px-4 sm:px-6 lg:px-8 bg-[#0a0a0f]">
            <div className="max-w-6xl mx-auto">
                {/* Section Header */}
                <div className="text-center mb-16">
                    <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
                        <span className="text-white">Why Researchers Choose </span>
                        <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                            Stocxer AI
                        </span>
                    </h2>
                    <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                        Powerful data analysis features for market research and analytics
                    </p>
                </div>

                {/* Features Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {features.map((feature, index) => (
                        <div
                            key={index}
                            className={`group relative p-6 rounded-2xl ${feature.bgColor} border ${feature.borderColor} backdrop-blur-sm hover:scale-[1.02] transition-all duration-300`}
                        >
                            {/* Icon */}
                            <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${feature.color} mb-4`}>
                                <feature.icon className="w-6 h-6 text-white" />
                            </div>

                            {/* Content */}
                            <h3 className="text-xl font-semibold text-white mb-2 group-hover:text-purple-400 transition-colors">
                                {feature.title}
                            </h3>
                            <p className="text-gray-400 leading-relaxed">
                                {feature.description}
                            </p>

                            {/* Hover Glow */}
                            <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />
                        </div>
                    ))}
                </div>

                {/* Bottom Note */}
                <div className="mt-12 text-center">
                    <p className="text-gray-500 text-sm">
                        All features designed for <span className="text-purple-400">analytical, research & informational</span> purposes only
                    </p>
                </div>
            </div>
        </section>
    )
}
