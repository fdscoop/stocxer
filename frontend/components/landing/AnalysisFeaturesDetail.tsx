'use client'

import { TrendingUp, Calculator, Newspaper } from 'lucide-react'

const ictFeatures = [
    { name: 'Order Block Detection', description: 'Identifies institutional buying/selling zones' },
    { name: 'Fair Value Gap (FVG)', description: 'Spots price imbalances likely to be filled' },
    { name: 'Liquidity Sweep Alerts', description: 'Detects stop-hunt movements' },
    { name: 'Market Structure (BOS/CHoCH)', description: 'Tracks Break of Structure and Change of Character' },
]

const optionsFeatures = [
    { name: 'Greeks Calculator', description: 'Delta, Gamma, Theta, Vega, Rho' },
    { name: 'Implied Volatility (IV)', description: 'Black-Scholes based IV calculation' },
    { name: 'Open Interest (OI)', description: 'Track OI buildup and unwinding' },
    { name: 'Put-Call Ratio (PCR)', description: 'Monitor market sentiment via PCR' },
]

const sentimentFeatures = [
    { name: 'News Sentiment Scoring', description: 'Analyzes market news in real-time' },
    { name: 'Bullish/Bearish/Neutral', description: 'Classifies sentiment for quick reading' },
    { name: 'Market Mood Indicator', description: 'Combines news sentiment into overall mood' },
]

export default function AnalysisFeaturesDetail() {
    return (
        <section className="py-24 px-4 sm:px-6 lg:px-8 bg-[#0a0a0f]">
            <div className="max-w-6xl mx-auto">
                {/* Section Header */}
                <div className="text-center mb-16">
                    <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
                        <span className="text-white">What We </span>
                        <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                            Analyze
                        </span>
                    </h2>
                    <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                        Comprehensive analysis across ICT patterns, options data, and market sentiment
                    </p>
                </div>

                {/* Features Grid */}
                <div className="grid lg:grid-cols-3 gap-8">
                    {/* ICT / Smart Money */}
                    <div className="relative p-8 rounded-2xl bg-gradient-to-b from-blue-500/10 to-transparent border border-blue-500/20 backdrop-blur-sm">
                        <div className="inline-flex p-3 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 mb-6">
                            <TrendingUp className="w-6 h-6 text-white" />
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-2">ICT / Smart Money</h3>
                        <p className="text-gray-400 mb-6 text-sm">
                            Institutional trading patterns and price action analysis
                        </p>
                        <div className="space-y-4">
                            {ictFeatures.map((feature, index) => (
                                <div key={index} className="flex gap-3">
                                    <div className="mt-1">
                                        <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                                    </div>
                                    <div>
                                        <h4 className="text-sm font-semibold text-white">{feature.name}</h4>
                                        <p className="text-xs text-gray-500">{feature.description}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Options Analytics */}
                    <div className="relative p-8 rounded-2xl bg-gradient-to-b from-purple-500/10 to-transparent border border-purple-500/20 backdrop-blur-sm">
                        <div className="inline-flex p-3 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 mb-6">
                            <Calculator className="w-6 h-6 text-white" />
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-2">Options Analytics</h3>
                        <p className="text-gray-400 mb-6 text-sm">
                            Real-time Greeks, IV, OI, and PCR analysis
                        </p>
                        <div className="space-y-4">
                            {optionsFeatures.map((feature, index) => (
                                <div key={index} className="flex gap-3">
                                    <div className="mt-1">
                                        <div className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                                    </div>
                                    <div>
                                        <h4 className="text-sm font-semibold text-white">{feature.name}</h4>
                                        <p className="text-xs text-gray-500">{feature.description}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Sentiment Analysis */}
                    <div className="relative p-8 rounded-2xl bg-gradient-to-b from-green-500/10 to-transparent border border-green-500/20 backdrop-blur-sm">
                        <div className="inline-flex p-3 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 mb-6">
                            <Newspaper className="w-6 h-6 text-white" />
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-2">Sentiment Analysis</h3>
                        <p className="text-gray-400 mb-6 text-sm">
                            Market news sentiment scoring and mood tracking
                        </p>
                        <div className="space-y-4">
                            {sentimentFeatures.map((feature, index) => (
                                <div key={index} className="flex gap-3">
                                    <div className="mt-1">
                                        <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
                                    </div>
                                    <div>
                                        <h4 className="text-sm font-semibold text-white">{feature.name}</h4>
                                        <p className="text-xs text-gray-500">{feature.description}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </section>
    )
}
