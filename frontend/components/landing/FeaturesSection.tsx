'use client'

import {
    Scan,
    Brain,
    TrendingUp,
    Filter,
    History,
    Shield
} from 'lucide-react'

const features = [
    {
        icon: Scan,
        title: 'Market Scanning',
        description: 'Scan major indices and stocks across NSE & BSE with real-time data integration.',
        color: 'from-blue-500 to-cyan-500',
        bgColor: 'bg-blue-500/10',
        borderColor: 'border-blue-500/20',
    },
    {
        icon: Brain,
        title: 'Deep Analysis with Watchman AI v3.5',
        description: 'Perform advanced analysis of market data using our proprietary AI engine for probability-based insights.',
        color: 'from-purple-500 to-pink-500',
        bgColor: 'bg-purple-500/10',
        borderColor: 'border-purple-500/20',
    },
    {
        icon: TrendingUp,
        title: 'Probability Evaluation',
        description: 'Evaluate confidence levels and market conditions to understand potential scenarios.',
        color: 'from-green-500 to-emerald-500',
        bgColor: 'bg-green-500/10',
        borderColor: 'border-green-500/20',
    },
    {
        icon: Filter,
        title: 'Processed Insights Only',
        description: 'View clean, relevant insights without the noise of raw option chains or overwhelming data.',
        color: 'from-yellow-500 to-orange-500',
        bgColor: 'bg-yellow-500/10',
        borderColor: 'border-yellow-500/20',
    },
    {
        icon: History,
        title: 'Accuracy Tracking',
        description: 'Track historical performance of analytical models for continuous improvement and transparency.',
        color: 'from-cyan-500 to-blue-500',
        bgColor: 'bg-cyan-500/10',
        borderColor: 'border-cyan-500/20',
    },
    {
        icon: Shield,
        title: 'User-Specific Dashboard',
        description: 'Access your personalized dashboard with insights tailored to your scanning preferences.',
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
                        <span className="text-white">What </span>
                        <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                            Stocxer AI
                        </span>
                        <span className="text-white"> Does</span>
                    </h2>
                    <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                        A comprehensive market analytics platform that transforms complex data into actionable insights
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
                        All features designed for <span className="text-purple-400">informational and educational</span> purposes
                    </p>
                </div>
            </div>
        </section>
    )
}
