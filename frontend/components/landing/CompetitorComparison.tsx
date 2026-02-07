'use client'

import { Check, X, AlertCircle } from 'lucide-react'

const features = [
    { name: 'ICT Top-Down Multi-Timeframe', stocxer: 'yes', sensibull: 'no', quantsapp: 'no', opstra: 'no' },
    { name: 'AMD Phase Detection (Bear/Bull Traps)', stocxer: 'yes', sensibull: 'no', quantsapp: 'no', opstra: 'no' },
    { name: 'ML Direction + Speed + IV Prediction', stocxer: 'yes', sensibull: 'no', quantsapp: 'no', opstra: 'no' },
    { name: 'P&L Simulation (5 scenarios × 5 horizons)', stocxer: 'yes', sensibull: 'no', quantsapp: 'no', opstra: 'no' },
    { name: 'Trade Grading (A–F with win probability)', stocxer: 'yes', sensibull: 'no', quantsapp: 'no', opstra: 'no' },
    { name: 'Scalp Feasibility Analyzer', stocxer: 'yes', sensibull: 'no', quantsapp: 'no', opstra: 'no' },
    { name: 'Options Greeks Calculator', stocxer: 'yes', sensibull: 'yes', quantsapp: 'yes', opstra: 'yes' },
    { name: 'OI / IV / PCR Analysis', stocxer: 'yes', sensibull: 'yes', quantsapp: 'yes', opstra: 'yes' },
    { name: 'Nifty 50 Constituent Probability', stocxer: 'yes', sensibull: 'no', quantsapp: 'no', opstra: 'no' },
    { name: 'News Sentiment Analysis', stocxer: 'yes', sensibull: 'no', quantsapp: 'limited', opstra: 'no' },
    { name: 'AI Chat (Signal Explanations)', stocxer: 'yes', sensibull: 'no', quantsapp: 'no', opstra: 'no' },
    { name: 'Pay As You Go Pricing', stocxer: 'yes', sensibull: 'no', quantsapp: 'no', opstra: 'no' },
    { name: 'Broker Integration', stocxer: 'Fyers', sensibull: 'Multiple', quantsapp: 'no', opstra: 'no' },
]

const StatusIcon = ({ status }: { status: string }) => {
    if (status === 'yes') {
        return <Check className="w-5 h-5 text-green-400" />
    } else if (status === 'limited') {
        return <AlertCircle className="w-5 h-5 text-yellow-400" />
    } else if (status === 'no') {
        return <X className="w-5 h-5 text-red-400" />
    }
    return <span className="text-gray-400 text-sm">{status}</span>
}

export default function CompetitorComparison() {
    return (
        <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-[#0a0a0f] to-[#0f0a1a]">
            <div className="max-w-7xl mx-auto">
                {/* Section Header */}
                <div className="text-center mb-16">
                    <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
                        <span className="text-white">How </span>
                        <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                            Stocxer Compares
                        </span>
                    </h2>
                    <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                        Feature-by-feature comparison with leading Indian data analysis platforms
                    </p>
                </div>

                {/* Desktop Table */}
                <div className="hidden lg:block overflow-x-auto">
                    <div className="inline-block min-w-full align-middle">
                        <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm">
                            <table className="min-w-full divide-y divide-white/10">
                                <thead>
                                    <tr className="bg-white/5">
                                        <th className="px-6 py-4 text-left text-sm font-semibold text-white">Feature</th>
                                        <th className="px-6 py-4 text-center text-sm font-semibold">
                                            <div className="flex flex-col items-center gap-2">
                                                <span className="text-purple-400 text-lg">Stocxer</span>
                                                <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 text-xs">You're here</span>
                                            </div>
                                        </th>
                                        <th className="px-6 py-4 text-center text-sm font-semibold text-gray-400">Sensibull</th>
                                        <th className="px-6 py-4 text-center text-sm font-semibold text-gray-400">Quantsapp</th>
                                        <th className="px-6 py-4 text-center text-sm font-semibold text-gray-400">Opstra</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/10">
                                    {features.map((feature, index) => (
                                        <tr key={index} className="hover:bg-white/5 transition-colors">
                                            <td className="px-6 py-4 text-sm text-gray-300">{feature.name}</td>
                                            <td className="px-6 py-4 text-center">
                                                <div className="flex justify-center">
                                                    <StatusIcon status={feature.stocxer} />
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <div className="flex justify-center">
                                                    <StatusIcon status={feature.sensibull} />
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <div className="flex justify-center">
                                                    <StatusIcon status={feature.quantsapp} />
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <div className="flex justify-center">
                                                    <StatusIcon status={feature.opstra} />
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Mobile View */}
                <div className="lg:hidden space-y-4">
                    {features.map((feature, index) => (
                        <div key={index} className="p-4 rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm">
                            <h3 className="text-white font-semibold mb-3">{feature.name}</h3>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="flex items-center justify-between p-2 rounded-lg bg-purple-500/10 border border-purple-500/20">
                                    <span className="text-sm text-purple-300">Stocxer</span>
                                    <StatusIcon status={feature.stocxer} />
                                </div>
                                <div className="flex items-center justify-between p-2 rounded-lg bg-white/5">
                                    <span className="text-sm text-gray-400">Sensibull</span>
                                    <StatusIcon status={feature.sensibull} />
                                </div>
                                <div className="flex items-center justify-between p-2 rounded-lg bg-white/5">
                                    <span className="text-sm text-gray-400">Quantsapp</span>
                                    <StatusIcon status={feature.quantsapp} />
                                </div>
                                <div className="flex items-center justify-between p-2 rounded-lg bg-white/5">
                                    <span className="text-sm text-gray-400">Opstra</span>
                                    <StatusIcon status={feature.opstra} />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Legend */}
                <div className="mt-8 flex flex-wrap justify-center gap-6 text-sm text-gray-400">
                    <div className="flex items-center gap-2">
                        <Check className="w-4 h-4 text-green-400" />
                        <span>Yes</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <X className="w-4 h-4 text-red-400" />
                        <span>No</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 text-yellow-400" />
                        <span>Limited</span>
                    </div>
                </div>
            </div>
        </section>
    )
}
