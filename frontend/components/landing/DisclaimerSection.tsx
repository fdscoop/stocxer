'use client'

import { AlertTriangle, Info, ExternalLink, Shield } from 'lucide-react'
import Link from 'next/link'

export default function DisclaimerSection() {
    return (
        <section className="py-10 sm:py-16 px-3 sm:px-6 lg:px-8 bg-gradient-to-b from-[#0a0a0f] to-[#0a0a12]">
            <div className="max-w-4xl mx-auto">
                {/* Fyers Account Requirement */}
                <div className="mb-6 sm:mb-8 rounded-xl sm:rounded-2xl bg-gradient-to-b from-blue-500/5 to-cyan-500/5 border border-blue-500/20 p-4 sm:p-6">
                    <div className="flex flex-col sm:flex-row items-start gap-3 sm:gap-4">
                        <div className="p-2 rounded-lg bg-blue-500/20 flex-shrink-0">
                            <Shield className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                        </div>
                        <div className="w-full">
                            <h3 className="text-lg sm:text-xl font-bold text-white mb-2">Fyers Trading Account Required</h3>
                            <p className="text-sm sm:text-base text-gray-400 mb-4">
                                Stocxer AI requires an active <strong className="text-blue-400">Fyers trading account</strong> to 
                                access live market data and portfolio information. We use Fyers API for secure, 
                                read-only access to market data.
                            </p>
                            <Link
                                href="https://fyers.in"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-2 px-3 sm:px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 rounded-lg text-blue-400 text-xs sm:text-sm font-medium transition-colors"
                            >
                                Open Fyers Account
                                <ExternalLink className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                            </Link>
                        </div>
                    </div>
                </div>

                {/* Main Disclaimer Card */}
                <div className="rounded-xl sm:rounded-2xl bg-gradient-to-b from-yellow-500/5 to-orange-500/5 border border-yellow-500/20 p-4 sm:p-8">
                    {/* Header */}
                    <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
                        <div className="p-1.5 sm:p-2 rounded-lg bg-yellow-500/20">
                            <AlertTriangle className="w-5 h-5 sm:w-6 sm:h-6 text-yellow-500" />
                        </div>
                        <h2 className="text-xl sm:text-2xl font-bold text-white">Important Disclaimer</h2>
                    </div>

                    {/* Main Disclaimer Text */}
                    <div className="space-y-3 sm:space-y-4 text-sm sm:text-base text-gray-300 leading-relaxed">
                        <p>
                            <strong className="text-white">Stocxer AI</strong> is an intuitive AI-based data analysis 
                            software that displays technical indicators and probability models for <strong className="text-yellow-400">analytical, 
                            research, and informational purposes only</strong>.
                        </p>

                        <p>
                            The platform does <strong className="text-red-400">not</strong> provide investment advice, 
                            stock recommendations, buy/sell signals, or guarantees of profit. All displayed data is 
                            derived from historical patterns and mathematical models, which may not accurately 
                            reflect future market conditions.
                        </p>

                        <p>
                            Users are <strong className="text-white">fully responsible</strong> for their own trading 
                            and investment decisions. We strongly recommend consulting with a SEBI-registered 
                            investment adviser before making any financial decisions.
                        </p>
                    </div>

                    {/* SEBI Notice */}
                    <div className="mt-4 sm:mt-6 p-3 sm:p-4 rounded-lg sm:rounded-xl bg-red-500/10 border border-red-500/20">
                        <div className="flex items-start gap-2 sm:gap-3">
                            <Info className="w-4 h-4 sm:w-5 sm:h-5 text-red-400 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="text-red-400 font-semibold mb-1 text-sm sm:text-base">SEBI Regulatory Notice</p>
                                <p className="text-gray-400 text-xs sm:text-sm">
                                    Stocxer AI and Cadreago De Private Limited are <strong className="text-red-300">not registered 
                                    with SEBI as investment advisers or research analysts</strong>. This platform 
                                    is a technology tool for market data visualization and educational analytics. 
                                    No content on this platform should be construed as personalized investment 
                                    advice or stock recommendations.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Compliance Statement */}
                    <div className="mt-4 sm:mt-6 p-3 sm:p-4 rounded-lg sm:rounded-xl bg-purple-500/10 border border-purple-500/20">
                        <p className="text-purple-300 text-xs sm:text-sm">
                            <strong>Compliance Statement:</strong> Stocxer AI is a data analysis tool designed 
                            for analytical, research, and informational purposes. It adheres to SEBI content 
                            guidelines and refrains from providing any form of investment recommendations, 
                            stock tips, or trading signals. Users utilize this software for their own 
                            independent research and analysis.
                        </p>
                    </div>

                    {/* Risk Warning */}
                    <div className="mt-4 sm:mt-6 p-3 sm:p-4 rounded-lg sm:rounded-xl bg-orange-500/10 border border-orange-500/20">
                        <p className="text-orange-300 text-xs sm:text-sm">
                            <strong>Risk Warning:</strong> Trading in stocks, derivatives, and F&O involves 
                            substantial risk of loss and is not suitable for all investors. Past performance 
                            of any analytical model is not indicative of future results. Please consult with 
                            a SEBI-registered financial advisor before making any investment decisions.
                        </p>
                    </div>
                </div>

                {/* Quick Legal Points */}
                <div className="mt-6 sm:mt-8 grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4">
                    {[
                        { title: 'Data Analysis Tool', desc: 'Software for analytical & research use' },
                        { title: 'Informational Only', desc: 'Not investment advice or recommendations' },
                        { title: 'User Responsibility', desc: 'You make your own trading decisions' },
                        { title: 'Fyers Account Required', desc: 'Requires active Fyers trading account' },
                    ].map((point, i) => (
                        <div
                            key={i}
                            className="p-3 sm:p-4 rounded-lg sm:rounded-xl bg-white/5 border border-white/10 text-center"
                        >
                            <h4 className="text-xs sm:text-sm font-semibold text-white mb-0.5 sm:mb-1">{point.title}</h4>
                            <p className="text-[10px] sm:text-xs text-gray-500 leading-tight">{point.desc}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}
