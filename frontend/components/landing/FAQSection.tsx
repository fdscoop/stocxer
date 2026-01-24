'use client'

import { useState } from 'react'
import { ChevronDown } from 'lucide-react'

const faqs = [
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
        question: 'Do you have risk management tools?',
        answer: 'Yes. We provide position sizing calculator and stop-loss suggestions based on your capital and risk tolerance.',
    },
    {
        question: 'Which brokers do you support?',
        answer: 'Currently Fyers. More brokers coming soon.',
    },
    {
        question: 'Is Stocxer SEBI registered?',
        answer: 'No. Stocxer is a market analytics tool for informational and educational purposes only. We do not provide investment advice or trading recommendations.',
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
                        href="mailto:help@stocxer.in"
                        className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 rounded-xl text-white font-semibold transition-all duration-300"
                    >
                        Contact Support
                    </a>
                </div>
            </div>
        </section>
    )
}
