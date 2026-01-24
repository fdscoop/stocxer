'use client'

import { ArrowRight, BarChart3, Sparkles, TrendingUp } from 'lucide-react'
import Link from 'next/link'

export default function HeroSection() {
    return (
        <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
            {/* Animated Gradient Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-[#0a0a0f] via-[#0f0a1a] to-[#0a0f1a]">
                {/* Gradient Orbs */}
                <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-purple-600/20 rounded-full blur-[128px] animate-pulse" />
                <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-blue-600/20 rounded-full blur-[128px] animate-pulse" style={{ animationDelay: '1s' }} />
                <div className="absolute top-1/2 right-1/3 w-[300px] h-[300px] bg-cyan-500/10 rounded-full blur-[100px] animate-pulse" style={{ animationDelay: '2s' }} />
            </div>

            {/* Grid Pattern Overlay */}
            <div
                className="absolute inset-0 opacity-[0.03]"
                style={{
                    backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
                    backgroundSize: '50px 50px'
                }}
            />

            {/* Content */}
            <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                {/* Badge */}
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20 mb-8 backdrop-blur-sm">
                    <Sparkles className="w-4 h-4 text-purple-400" />
                    <span className="text-sm text-purple-300">Powered by Watchman AI v3.5</span>
                </div>

                {/* Main Headline */}
                <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
                    <span className="text-white">India's First </span>
                    <span className="bg-gradient-to-r from-purple-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">
                        ICT + AI
                    </span>
                    <br />
                    <span className="text-white">Market Analysis Platform</span>
                </h1>

                {/* Sub-headline */}
                <p className="text-lg sm:text-xl text-gray-400 max-w-3xl mx-auto mb-10 leading-relaxed">
                    Stop interpreting raw data. Get consolidated probability analysis powered by{' '}
                    <span className="text-purple-400 font-semibold">Smart Money Concepts</span>,{' '}
                    <span className="text-blue-400 font-semibold">Machine Learning</span>, and{' '}
                    <span className="text-cyan-400 font-semibold">News Sentiment</span> — for informed decision-making.
                </p>

                {/* CTAs */}
                <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
                    <Link
                        href="/login"
                        className="group relative inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 rounded-xl text-white font-semibold text-lg transition-all duration-300 shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 hover:scale-105"
                    >
                        <BarChart3 className="w-5 h-5" />
                        Start Free — 100 Credits
                        <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </Link>
                    <Link
                        href="#how-it-works"
                        className="group inline-flex items-center justify-center gap-2 px-8 py-4 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-purple-500/30 rounded-xl text-white font-semibold text-lg transition-all duration-300"
                    >
                        <TrendingUp className="w-5 h-5" />
                        See How It Works
                    </Link>
                </div>

                {/* Trust Badges */}
                <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16 max-w-4xl mx-auto">
                    {[
                        'ICT Order Block & FVG Detection',
                        'ML-Powered Probability Assessment',
                        'Real-time News Sentiment Scoring'
                    ].map((badge, i) => (
                        <div
                            key={i}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 backdrop-blur-sm"
                        >
                            <span className="text-green-400 text-lg">✓</span>
                            <span className="text-sm text-gray-300">{badge}</span>
                        </div>
                    ))}
                </div>

                {/* Floating Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
                    {[
                        { label: 'Indices Tracked', value: '6+', icon: '📊' },
                        { label: 'Stocks Analyzed', value: '500+', icon: '📈' },
                        { label: 'News Sources', value: 'Real-time', icon: '📰' },
                        { label: 'AI Engine', value: 'Watchman v3.5', icon: '🤖' },
                    ].map((stat, i) => (
                        <div
                            key={i}
                            className="group p-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 hover:border-purple-500/30 transition-all duration-300"
                        >
                            <div className="text-2xl mb-2">{stat.icon}</div>
                            <div className="text-2xl font-bold text-white group-hover:text-purple-400 transition-colors">
                                {stat.value}
                            </div>
                            <div className="text-sm text-gray-500">{stat.label}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Bottom Gradient Fade */}
            <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#0a0a0f] to-transparent" />
        </section>
    )
}
