'use client'

import { useState } from 'react'
import { ChevronDown } from 'lucide-react'

const faqs = [
    {
        question: 'What features are included in Stocxer AI?',
        answer: 'All plans include: Stock Dashboard, Stock Screener, Options Scanner, Index Analyzer, live market data, technical analysis, probability scores, and AI-powered insights via Watchman AI v3.5. All users get the same features — differences are only in rate limits and bulk scan limits.',
    },
    {
        question: 'Is Watchman AI v3.5 available in the free trial?',
        answer: 'Yes! Watchman AI v3.5 is available in all plans including the free trial. When you sign up, you receive 100 token credits to explore all features at no cost.',
    },
    {
        question: 'What\'s the difference between plans?',
        answer: 'All plans provide access to the same features as the Pro plan. The main differences are rate limits (scans per month), bulk scan limits (stocks per scan), and support priority. Even free trial users get full feature access with 100 credits.',
    },
    {
        question: 'How is Stocxer different from Sensibull?',
        answer: 'Sensibull focuses on option chain data and strategy building. Stocxer provides automated ICT/Smart Money pattern detection, ML probability models, and news sentiment analysis — features no other Indian platform offers.',
    },
    {
        question: 'What is ICT analysis?',
        answer: 'ICT (Inner Circle Trader) concepts include Order Blocks, Fair Value Gaps, and Liquidity Sweeps — methods used by institutional traders to identify high-probability zones.',
    },
    {
        question: 'What Options Greeks do you calculate?',
        answer: 'We calculate Delta, Gamma, Theta, Vega, Rho, and Implied Volatility using Black-Scholes models.',
    },
    {
        question: 'Do you have risk assessment tools?',
        answer: 'Yes. We provide educational position sizing calculators and risk analysis tools for informational purposes.',
    },
    {
        question: 'Which brokers do you support?',
        answer: 'Currently Fyers. More brokers coming soon.',
    },
    {
        question: 'Is Stocxer SEBI registered?',
        answer: 'No. Stocxer AI is a data analysis tool for analytical, research, and informational purposes only — not a replacement for your own research and judgment. We do not provide investment advice or trading recommendations. Always do your due diligence and consider consulting a SEBI-registered financial advisor before making investment decisions.',
    },
    {
        question: 'Do credits expire?',
        answer: 'No. Pay As You Go credits never expire.',
    },
    {
        question: 'Can I cancel anytime?',
        answer: 'Yes. Monthly plans can be cancelled anytime with no penalty.',
    },
]

export default function FAQSection() {
    const [openIndex, setOpenIndex] = useState<number | null>(null)

    const toggleFAQ = (index: number) => {
        setOpenIndex(openIndex === index ? null : index)
    }

    return (
        <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-[#0a0a0f] to-[#0f0a1a]">
            <div className="max-w-4xl mx-auto">
                {/* Section Header */}
                <div className="text-center mb-16">
                    <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
                        <span className="text-white">Frequently Asked </span>
                        <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                            Questions
                        </span>
                    </h2>
                    <p className="text-gray-400 text-lg">
                        Everything you need to know about Stocxer AI
                    </p>
                </div>

                {/* FAQ List */}
                <div className="space-y-4">
                    {faqs.map((faq, index) => (
                        <div
                            key={index}
                            className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm overflow-hidden transition-all duration-300 hover:border-purple-500/30"
                        >
                            <button
                                onClick={() => toggleFAQ(index)}
                                className="w-full px-6 py-5 flex items-center justify-between text-left"
                            >
                                <span className="text-white font-semibold pr-8">{faq.question}</span>
                                <ChevronDown
                                    className={`w-5 h-5 text-purple-400 flex-shrink-0 transition-transform duration-300 ${
                                        openIndex === index ? 'rotate-180' : ''
                                    }`}
                                />
                            </button>
                            <div
                                className={`overflow-hidden transition-all duration-300 ${
                                    openIndex === index ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
                                }`}
                            >
                                <div className="px-6 pb-5 text-gray-400 leading-relaxed">
                                    {faq.answer}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Bottom CTA */}
                <div className="mt-12 text-center p-6 rounded-2xl bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20">
                    <p className="text-gray-300 mb-4">Still have questions?</p>
                    <a
                        href="mailto:cadreagode@gmx.com"
                        className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 rounded-xl text-white font-semibold transition-all duration-300"
                    >
                        Contact Support
                    </a>
                </div>
            </div>
        </section>
    )
}
