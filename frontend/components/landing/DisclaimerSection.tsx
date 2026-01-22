'use client'

import { AlertTriangle, Info } from 'lucide-react'

export default function DisclaimerSection() {
    return (
        <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-[#0a0a0f] to-[#0a0a12]">
            <div className="max-w-4xl mx-auto">
                {/* Main Disclaimer Card */}
                <div className="rounded-2xl bg-gradient-to-b from-yellow-500/5 to-orange-500/5 border border-yellow-500/20 p-8">
                    {/* Header */}
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 rounded-lg bg-yellow-500/20">
                            <AlertTriangle className="w-6 h-6 text-yellow-500" />
                        </div>
                        <h2 className="text-2xl font-bold text-white">Important Disclaimer</h2>
                    </div>

                    {/* Main Disclaimer Text */}
                    <div className="space-y-4 text-gray-300 leading-relaxed">
                        <p>
                            <strong className="text-white">Stocxer AI</strong> provides analytical tools and probability-based
                            market insights for <strong className="text-yellow-400">informational and educational purposes only</strong>.
                        </p>

                        <p>
                            It does <strong className="text-red-400">not</strong> provide investment advice, trading recommendations,
                            or guarantees of profit. All analysis is based on historical data and mathematical models,
                            which may not accurately reflect future market conditions.
                        </p>

                        <p>
                            Users are fully responsible for their own trading and investment decisions.
                            Past performance of any analytical model is not indicative of future results.
                        </p>
                    </div>

                    {/* SEBI Notice */}
                    <div className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                        <div className="flex items-start gap-3">
                            <Info className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="text-red-400 font-semibold mb-1">Regulatory Notice</p>
                                <p className="text-gray-400 text-sm">
                                    Stocxer AI and Cadreago De Private Limited are <strong className="text-red-300">not registered
                                        as SEBI investment advisers</strong>. The platform provides market analytics tools only
                                    and should not be construed as personalized investment advice.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Risk Warning */}
                    <div className="mt-6 p-4 rounded-xl bg-orange-500/10 border border-orange-500/20">
                        <p className="text-orange-300 text-sm">
                            <strong>Risk Warning:</strong> Trading in stocks and derivatives involves substantial risk
                            of loss and is not suitable for all investors. Please consult with a qualified financial
                            advisor before making any investment decisions.
                        </p>
                    </div>
                </div>

                {/* Quick Legal Points */}
                <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {[
                        { title: 'No Guaranteed Returns', desc: 'All insights are probabilistic, not certain' },
                        { title: 'Educational Purpose', desc: 'Information provided for learning only' },
                        { title: 'User Responsibility', desc: 'You make your own trading decisions' },
                    ].map((point, i) => (
                        <div
                            key={i}
                            className="p-4 rounded-xl bg-white/5 border border-white/10 text-center"
                        >
                            <h4 className="text-sm font-semibold text-white mb-1">{point.title}</h4>
                            <p className="text-xs text-gray-500">{point.desc}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}
