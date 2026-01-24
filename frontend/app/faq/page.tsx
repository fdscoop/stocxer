import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft, HelpCircle, ChevronDown } from 'lucide-react'

export const metadata: Metadata = {
    title: 'FAQ - Stocxer AI',
    description: 'Frequently Asked Questions about Stocxer AI market analytics platform',
}

const faqs = [
    {
        category: 'General',
        questions: [
            {
                question: 'What is Stocxer AI?',
                answer: 'Stocxer AI is a data-driven market analytics platform powered by Watchman AI v3.5. It provides probability-based insights, technical analysis, and decision-support tools for Indian stock market instruments including stocks, options, and derivatives.'
            },
            {
                question: 'Is Stocxer AI a SEBI registered investment advisor?',
                answer: 'No. Stocxer AI and FDS COOP LLP are NOT registered as SEBI investment advisers. The platform provides analytical tools for informational and educational purposes only. It does not constitute investment advice.'
            },
            {
                question: 'Who can use Stocxer AI?',
                answer: 'Anyone who is at least 18 years old and interested in Indian stock market analysis can use Stocxer AI. The platform is designed for traders, investors, and market enthusiasts who want data-driven insights.'
            },
        ]
    },
    {
        category: 'Platform Features',
        questions: [
            {
                question: 'What is Watchman AI v3.5?',
                answer: 'Watchman AI v3.5 is our proprietary analytical engine that processes market data using advanced algorithms to generate probability-based insights, identify patterns, and provide comprehensive market analysis.'
            },
            {
                question: 'What markets does Stocxer AI cover?',
                answer: 'Currently, Stocxer AI focuses on the Indian stock market, including NSE and BSE equities, NIFTY, BANKNIFTY, and FINNIFTY indices, and their derivatives (futures and options).'
            },
            {
                question: 'How often is the market data updated?',
                answer: 'Market data is updated in real-time during market hours when connected to your Fyers account. Historical data and analysis are refreshed regularly to ensure accuracy.'
            },
            {
                question: 'What features are included in the platform?',
                answer: 'Features include the Stock Dashboard, Stock Screener, Options Scanner, Index Analyzer, live market data, technical analysis, probability scores, and AI-powered insights. Available features vary by subscription plan.'
            },
        ]
    },
    {
        category: 'Fyers Integration',
        questions: [
            {
                question: 'Why do I need to connect my Fyers account?',
                answer: 'Fyers integration is required to access real-time market data. Stocxer AI uses Fyers API to fetch live prices, option chains, and market information. We do not execute trades or access your funds.'
            },
            {
                question: 'Is my Fyers account data safe?',
                answer: 'Yes. We only use read-only access to fetch market data. We do not have access to your trading credentials, funds, or the ability to place orders on your behalf.'
            },
            {
                question: 'What if I don\'t have a Fyers account?',
                answer: 'You will need a Fyers account to use the live market data features. You can create a free Fyers account at fyers.in. Some platform features may be limited without Fyers integration.'
            },
        ]
    },
    {
        category: 'Subscription & Billing',
        questions: [
            {
                question: 'What subscription plans are available?',
                answer: 'We offer Free, Starter (₹4,999/month), and Pro (₹9,999/month) plans. Each plan offers different levels of access to features like scans, AI insights, and premium indicators. Annual plans are available with discounts.'
            },
            {
                question: 'Can I cancel my subscription anytime?',
                answer: 'Yes, you can cancel your subscription at any time. Your access will continue until the end of your current billing period. There are no cancellation fees.'
            },
            {
                question: 'Is there a refund policy?',
                answer: 'Yes. First-time subscribers are eligible for a 7-day money-back guarantee. Annual subscribers can request prorated refunds within 30 days. Please see our full Refund Policy for details.'
            },
            {
                question: 'What payment methods are accepted?',
                answer: 'We accept all major payment methods including UPI, credit/debit cards, and net banking. All payments are processed securely through our payment processor.'
            },
        ]
    },
    {
        category: 'Trading & Signals',
        questions: [
            {
                question: 'Are the signals guaranteed to be profitable?',
                answer: 'No. Stocxer AI provides probability-based insights, not trading signals or guarantees. Trading involves substantial risk of loss. Past performance and probability scores are not indicative of future results.'
            },
            {
                question: 'Should I trade based solely on Stocxer AI analysis?',
                answer: 'No. Stocxer AI is a decision-support tool, not a replacement for your own research and judgment. Always do your due diligence and consider consulting a qualified financial advisor before making investment decisions.'
            },
            {
                question: 'What do the probability scores mean?',
                answer: 'Probability scores indicate the statistical likelihood of certain market outcomes based on historical patterns and current market conditions. They are estimates and should not be interpreted as predictions or guarantees.'
            },
        ]
    },
    {
        category: 'Technical Support',
        questions: [
            {
                question: 'How do I contact support?',
                answer: 'You can reach our support team at help@stocxer.in. We typically respond within 24-48 hours during business days.'
            },
            {
                question: 'What browsers are supported?',
                answer: 'Stocxer AI works best on modern browsers including Chrome, Firefox, Safari, and Edge (latest versions). Mobile responsive design is also supported.'
            },
            {
                question: 'Why is my data not loading?',
                answer: 'Data loading issues are usually related to Fyers connection. Try reconnecting your Fyers account, check if market is open (9:15 AM - 3:30 PM IST), or contact support if the issue persists.'
            },
        ]
    },
]

export default function FAQPage() {
    return (
        <main className="min-h-screen bg-[#0a0a0f] py-16 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto">
                {/* Back Link */}
                <Link
                    href="/landing"
                    className="inline-flex items-center gap-2 text-purple-400 hover:text-purple-300 mb-8 transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back to Home
                </Link>

                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <div className="p-3 rounded-xl bg-purple-500/20">
                        <HelpCircle className="w-8 h-8 text-purple-400" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-white">Frequently Asked Questions</h1>
                        <p className="text-gray-400">Find answers to common questions about Stocxer AI</p>
                    </div>
                </div>

                {/* Quick Links */}
                <div className="mb-12 p-6 rounded-2xl bg-gradient-to-b from-purple-500/10 to-blue-500/10 border border-purple-500/20">
                    <p className="text-gray-300 mb-4">Jump to a section:</p>
                    <div className="flex flex-wrap gap-2">
                        {faqs.map((category, i) => (
                            <a
                                key={i}
                                href={`#${category.category.toLowerCase().replace(/\s+/g, '-')}`}
                                className="px-4 py-2 rounded-lg bg-white/5 text-gray-300 text-sm hover:bg-purple-500/20 hover:text-purple-300 transition-colors"
                            >
                                {category.category}
                            </a>
                        ))}
                    </div>
                </div>

                {/* FAQ Sections */}
                <div className="space-y-12">
                    {faqs.map((category, categoryIndex) => (
                        <section
                            key={categoryIndex}
                            id={category.category.toLowerCase().replace(/\s+/g, '-')}
                        >
                            <h2 className="text-2xl font-bold text-white mb-6 pb-2 border-b border-white/10">
                                {category.category}
                            </h2>
                            <div className="space-y-4">
                                {category.questions.map((faq, faqIndex) => (
                                    <div
                                        key={faqIndex}
                                        className="rounded-xl bg-white/5 border border-white/10 overflow-hidden hover:border-purple-500/30 transition-colors"
                                    >
                                        <div className="p-5">
                                            <h3 className="text-lg font-semibold text-white mb-3 flex items-start gap-3">
                                                <ChevronDown className="w-5 h-5 text-purple-400 mt-1 flex-shrink-0" />
                                                {faq.question}
                                            </h3>
                                            <p className="text-gray-400 leading-relaxed pl-8">
                                                {faq.answer}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    ))}
                </div>

                {/* Contact Section */}
                <div className="mt-12 p-6 rounded-2xl bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20">
                    <h2 className="text-xl font-bold text-white mb-4">Still have questions?</h2>
                    <p className="text-gray-400 mb-4">
                        Can&apos;t find the answer you&apos;re looking for? Our support team is here to help.
                    </p>
                    <Link
                        href="/support"
                        className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-purple-600 text-white font-semibold hover:bg-purple-500 transition-colors"
                    >
                        Contact Support
                    </Link>
                </div>
            </div>
        </main>
    )
}
