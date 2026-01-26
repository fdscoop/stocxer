'use client'

import { TrendingUp, Activity, BarChart2, Calculator, Newspaper, Target } from 'lucide-react'

const capabilities = [
    {
        icon: TrendingUp,
        title: 'Price Action Analysis',
        description: 'Detects ICT patterns: Order Blocks, FVG, BOS/CHoCH',
    },
    {
        icon: Activity,
        title: 'Momentum Evaluation',
        description: 'Measures trend strength across multiple timeframes',
    },
    {
        icon: BarChart2,
        title: 'Volatility Assessment',
        description: 'Tracks India VIX and instrument-specific volatility',
    },
    {
        icon: Calculator,
        title: 'Options Greeks',
        description: 'Delta, Gamma, Theta, Vega, Rho calculations',
    },
    {
        icon: Newspaper,
        title: 'News Sentiment',
        description: 'Real-time bullish/bearish/neutral scoring',
    },
    {
        icon: Target,
        title: 'Risk Analysis',
        description: 'Educational position sizing calculators',
    },
]

export default function WatchmanAISection() {
    return (
        <section className="py-24 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
            {/* Background */}
            <div className="absolute inset-0 bg-gradient-to-b from-[#0a0a0f] via-[#0f0a1a] to-[#0a0a0f]" />

            {/* Animated Background Elements */}
            <div className="absolute inset-0 overflow-hidden">
                {/* Neural Network Lines */}
                <svg className="absolute inset-0 w-full h-full opacity-10" viewBox="0 0 1000 600">
                    <defs>
                        <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0" />
                            <stop offset="50%" stopColor="#8B5CF6" stopOpacity="1" />
                            <stop offset="100%" stopColor="#06B6D4" stopOpacity="0" />
                        </linearGradient>
                    </defs>
                    {/* Animated lines */}
                    {[...Array(8)].map((_, i) => (
                        <line
                            key={i}
                            x1={100 + i * 100}
                            y1={100 + (i % 3) * 100}
                            x2={200 + i * 100}
                            y2={200 + ((i + 1) % 3) * 100}
                            stroke="url(#lineGradient)"
                            strokeWidth="2"
                            className="animate-pulse"
                            style={{ animationDelay: `${i * 0.2}s` }}
                        />
                    ))}
                    {/* Nodes */}
                    {[...Array(12)].map((_, i) => (
                        <circle
                            key={i}
                            cx={150 + (i % 4) * 200}
                            cy={150 + Math.floor(i / 4) * 150}
                            r="4"
                            fill="#8B5CF6"
                            className="animate-pulse"
                            style={{ animationDelay: `${i * 0.15}s` }}
                        />
                    ))}
                </svg>
            </div>

            <div className="relative z-10 max-w-6xl mx-auto">
                <div className="grid lg:grid-cols-2 gap-12 items-center">
                    {/* Left: Content */}
                    <div>
                        {/* Badge */}
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/30 mb-6">
                            <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" />
                            <span className="text-sm text-purple-300 font-medium">Advanced AI Engine</span>
                        </div>

                        {/* Title */}
                        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-6">
                            <span className="text-white">Powered by </span>
                            <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent">
                                Watchman AI v3.5
                            </span>
                        </h2>

                        {/* Description */}
                        <p className="text-lg text-gray-400 mb-8 leading-relaxed">
                            Watchman AI is Stocxer&apos;s proprietary analysis engine. It combines multiple analytical 
                            methods to generate probability-based data patterns for research and informational purposes.
                        </p>

                        {/* Important Note */}
                        <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20 mb-8">
                            <p className="text-sm text-purple-300">
                                <strong>Compliance Note:</strong> Watchman AI provides data analysis and probability models for 
                                analytical, research, and informational purposes only.
                            </p>
                        </div>

                        {/* Capabilities */}
                        <div className="grid grid-cols-2 gap-4">
                            {capabilities.map((cap, index) => (
                                <div
                                    key={index}
                                    className="flex items-start gap-3 p-3 rounded-lg bg-white/5 border border-white/10 hover:border-purple-500/30 transition-colors"
                                >
                                    <div className="p-2 rounded-lg bg-purple-500/20">
                                        <cap.icon className="w-4 h-4 text-purple-400" />
                                    </div>
                                    <div>
                                        <h4 className="text-sm font-semibold text-white">{cap.title}</h4>
                                        <p className="text-xs text-gray-500">{cap.description}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Right: AI Visualization */}
                    <div className="relative">
                        <div className="aspect-square max-w-md mx-auto relative">
                            {/* Outer Ring */}
                            <div className="absolute inset-0 rounded-full border-2 border-purple-500/20 animate-spin" style={{ animationDuration: '20s' }} />

                            {/* Middle Ring */}
                            <div className="absolute inset-8 rounded-full border-2 border-cyan-500/20 animate-spin" style={{ animationDuration: '15s', animationDirection: 'reverse' }} />

                            {/* Inner Ring */}
                            <div className="absolute inset-16 rounded-full border-2 border-pink-500/20 animate-spin" style={{ animationDuration: '10s' }} />

                            {/* Center Core */}
                            <div className="absolute inset-24 rounded-full bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center shadow-lg shadow-purple-500/30">
                                <div className="text-center">
                                    <div className="text-4xl font-bold text-white">v3.5</div>
                                    <div className="text-sm text-purple-200">Watchman AI</div>
                                </div>
                            </div>

                            {/* Floating Data Points */}
                            {[...Array(8)].map((_, i) => (
                                <div
                                    key={i}
                                    className="absolute w-3 h-3 bg-purple-500 rounded-full animate-ping"
                                    style={{
                                        top: `${20 + Math.sin(i * 0.8) * 30}%`,
                                        left: `${20 + Math.cos(i * 0.8) * 30}%`,
                                        animationDelay: `${i * 0.3}s`,
                                        animationDuration: '2s',
                                    }}
                                />
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </section>
    )
}
