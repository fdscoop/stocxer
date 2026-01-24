'use client'

import { Search, Cpu, LayoutDashboard, ArrowRight } from 'lucide-react'

const steps = [
    {
        number: '01',
        icon: Search,
        title: 'Scan',
        subtitle: 'Select Market or Stock',
        description: 'Select an index (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, SENSEX, BANKEX) or individual stocks from NSE/BSE.',
        color: 'from-blue-500 to-cyan-500',
    },
    {
        number: '02',
        icon: Cpu,
        title: 'Analyze',
        subtitle: 'Watchman AI Processing',
        description: 'Watchman AI v3.5 runs ICT detection, ML models, options flow, and sentiment analysis automatically.',
        color: 'from-purple-500 to-pink-500',
    },
    {
        number: '03',
        icon: LayoutDashboard,
        title: 'View',
        subtitle: 'Clean Dashboard Results',
        description: 'Get a clean dashboard with probability scores, detected patterns, and sentiment indicators.',
        color: 'from-green-500 to-emerald-500',
    },
]

export default function HowItWorksSection() {
    return (
        <section className="py-24 px-4 sm:px-6 lg:px-8 bg-[#0a0a0f]">
            <div className="max-w-6xl mx-auto">
                {/* Section Header */}
                <div className="text-center mb-16">
                    <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
                        <span className="text-white">How </span>
                        <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                            It Works
                        </span>
                    </h2>
                    <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                        Three steps to smarter analysis
                    </p>
                </div>

                {/* Steps */}
                <div className="relative">
                    {/* Connection Line (Desktop) */}
                    <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-green-500 -translate-y-1/2 opacity-20" />

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {steps.map((step, index) => (
                            <div key={index} className="relative">
                                {/* Step Card */}
                                <div className="group relative p-8 rounded-2xl bg-gradient-to-b from-white/5 to-transparent border border-white/10 hover:border-purple-500/30 transition-all duration-300 h-full">
                                    {/* Step Number */}
                                    <div className={`absolute -top-4 left-8 px-4 py-1 rounded-full bg-gradient-to-r ${step.color} text-white text-sm font-bold`}>
                                        STEP {step.number}
                                    </div>

                                    {/* Icon */}
                                    <div className={`inline-flex p-4 rounded-2xl bg-gradient-to-br ${step.color} mb-6 mt-4`}>
                                        <step.icon className="w-8 h-8 text-white" />
                                    </div>

                                    {/* Title */}
                                    <h3 className="text-2xl font-bold text-white mb-1 group-hover:text-purple-400 transition-colors">
                                        {step.title}
                                    </h3>
                                    <p className="text-sm text-purple-400 mb-4">{step.subtitle}</p>

                                    {/* Description */}
                                    <p className="text-gray-400 leading-relaxed">
                                        {step.description}
                                    </p>
                                </div>

                                {/* Arrow (Mobile) */}
                                {index < steps.length - 1 && (
                                    <div className="lg:hidden flex justify-center my-4">
                                        <ArrowRight className="w-6 h-6 text-purple-500 rotate-90" />
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Bottom CTA */}
                <div className="mt-16 text-center">
                    <a
                        href="/screener"
                        className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 rounded-xl text-white font-semibold transition-all duration-300 shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40"
                    >
                        Start Your First Scan
                        <ArrowRight className="w-5 h-5" />
                    </a>
                </div>
            </div>
        </section>
    )
}
