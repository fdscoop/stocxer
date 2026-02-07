'use client'

import { TrendingUp, Calculator, Newspaper, Layers } from 'lucide-react'

const ictFeatures = [
    { name: 'Order Block Detection', description: 'Identifies institutional buying/selling zones across 6 timeframes' },
    { name: 'Fair Value Gap (FVG)', description: 'Spots price imbalances likely to be filled on multiple timeframes' },
    { name: 'Market Structure (BOS/CHoCH)', description: 'Tracks Break of Structure and Change of Character' },
    { name: 'AMD Phase Detection', description: 'Identifies Accumulation, Manipulation & Distribution cycles' },
    { name: 'Bear & Bull Trap Detection', description: 'Alerts on manipulation phases designed to trap traders' },
    { name: 'Multi-Timeframe Confluence', description: 'Finds overlapping zones from Monthly down to 15min for high-probability setups' },
]

const optionsFeatures = [
    { name: 'Greeks Calculator', description: 'Delta, Gamma, Theta, Vega with per-hour/per-minute decay rates' },
    { name: 'P&L Simulation Engine', description: '5 scenarios (best to worst) across 5 time horizons' },
    { name: 'Theta Scenario Modeling', description: '15min, 30min, 1hr, 2hr, EOD projections with Greek decomposition' },
    { name: 'Scalp Feasibility Analyzer', description: 'Per-lot P&L, index move requirements & timing windows' },
    { name: 'IV Direction Prediction', description: 'ML-based IV contraction/expansion forecasting' },
    { name: 'Option Chain Live Scoring', description: 'Strikes ranked by LTP, Greeks, OI, Volume & momentum' },
]

const sentimentFeatures = [
    { name: 'News Sentiment Scoring', description: 'Real-time bullish/bearish/neutral analysis from 50+ sources' },
    { name: 'Constituent Probability', description: 'Nifty 50 stock-by-stock probability with bullish/bearish breakdown' },
    { name: 'Futures Basis Analysis', description: 'Monitors cash-futures basis % and OI trends for sentiment cues' },
    { name: 'Candlestick Confluence', description: 'Pattern detection with alignment scoring for confirmation' },
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
                        <h3 className="text-2xl font-bold text-white mb-2">ICT Top-Down + AMD</h3>
                        <p className="text-gray-400 mb-6 text-sm">
                            6-timeframe institutional analysis with manipulation detection
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
                        <h3 className="text-2xl font-bold text-white mb-2">Options & Simulation</h3>
                        <p className="text-gray-400 mb-6 text-sm">
                            Full P&L simulation, theta scenarios & scalp feasibility
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
                        <h3 className="text-2xl font-bold text-white mb-2">Sentiment & Confirmation</h3>
                        <p className="text-gray-400 mb-6 text-sm">
                            Multi-source confirmation stack with probability analysis
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
