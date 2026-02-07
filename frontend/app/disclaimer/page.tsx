import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft, AlertTriangle } from 'lucide-react'

export const metadata: Metadata = {
    title: 'Disclaimer - Stocxer AI',
    description: 'Legal disclaimer for Stocxer AI market analytics platform - not investment advice',
}

export default function DisclaimerPage() {
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
                    <div className="p-3 rounded-xl bg-yellow-500/20">
                        <AlertTriangle className="w-8 h-8 text-yellow-400" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-white">Disclaimer</h1>
                        <p className="text-gray-400">Important Legal Notice</p>
                    </div>
                </div>

                {/* Main Disclaimer Box */}
                <div className="mb-8 p-6 rounded-2xl bg-gradient-to-b from-red-500/10 to-orange-500/10 border border-red-500/30">
                    <h2 className="text-xl font-bold text-red-400 mb-4">⚠️ Not Investment Advice</h2>
                    <p className="text-gray-300 leading-relaxed text-lg">
                        Stocxer AI provides algorithmic analysis and trading signals for
                        <strong className="text-yellow-400"> educational and informational purposes only</strong>.
                        These signals are <strong className="text-red-400">NOT personalized investment advice</strong> and
                        should not be considered as such. We do not guarantee profit or trading success.
                    </p>
                </div>

                {/* Content */}
                <div className="prose prose-invert max-w-none space-y-8">
                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">General Disclaimer</h2>
                        <p className="text-gray-400 leading-relaxed">
                            The information provided on Stocxer AI platform is for general informational purposes only.
                            All information on the Platform is provided in good faith, however we make no representation
                            or warranty of any kind, express or implied, regarding the accuracy, adequacy, validity,
                            reliability, availability, or completeness of any information on the Platform.
                        </p>
                    </section>

                    <section className="p-6 rounded-xl bg-red-500/5 border border-red-500/20">
                        <h2 className="text-xl font-semibold text-red-400 mb-4">Regulatory Notice</h2>
                        <ul className="text-gray-400 leading-relaxed space-y-3">
                            <li className="flex items-start gap-3">
                                <span className="text-red-500 mt-1">•</span>
                                <span>Stocxer AI and Cadreago De Private Limited are <strong className="text-red-400">NOT registered
                                    as SEBI investment advisers</strong>.</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-red-500 mt-1">•</span>
                                <span>We do not hold any license to provide investment advisory services in India or any other jurisdiction.</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="text-red-500 mt-1">•</span>
                                <span>The Platform should not be construed as personalized investment advice.</span>
                            </li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">Trading & Investment Risks</h2>
                        <div className="p-4 rounded-xl bg-orange-500/10 border border-orange-500/20 mb-4">
                            <p className="text-orange-300 font-semibold">
                                Trading in stocks, options, and derivatives involves substantial risk of loss and
                                is not suitable for all investors.
                            </p>
                        </div>
                        <ul className="text-gray-400 leading-relaxed list-disc pl-6 space-y-2">
                            <li>You could lose some or all of your invested capital</li>
                            <li>Past performance is not indicative of future results</li>
                            <li>Probability assessments are not predictions and may not be accurate</li>
                            <li>Market conditions can change rapidly and unexpectedly</li>
                            <li>Leverage in derivatives trading can amplify both gains and losses</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">About Watchman AI v4.0</h2>
                        <p className="text-gray-400 leading-relaxed">
                            Watchman AI v4.0 is our proprietary analytical engine that processes market data to generate
                            probability-based insights. Important limitations:
                        </p>
                        <ul className="text-gray-400 leading-relaxed list-disc pl-6 space-y-2 mt-4">
                            <li>AI analysis is based on historical patterns which may not repeat</li>
                            <li>Probability scores are estimates, not guarantees</li>
                            <li>The model may have biases or limitations not immediately apparent</li>
                            <li>Technical analysis has inherent limitations in predicting market movements</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">No Professional Relationship</h2>
                        <p className="text-gray-400 leading-relaxed">
                            Use of Stocxer AI does not create a professional relationship including but not limited to:
                        </p>
                        <ul className="text-gray-400 leading-relaxed list-disc pl-6 space-y-2 mt-4">
                            <li>Investment advisor-client relationship</li>
                            <li>Broker-client relationship</li>
                            <li>Financial planner-client relationship</li>
                            <li>Any fiduciary relationship</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">User Responsibility</h2>
                        <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
                            <p className="text-blue-300">
                                <strong>You are solely responsible for your own investment and trading decisions.</strong>
                                We strongly recommend consulting with a qualified financial advisor before making any
                                investment decisions.
                            </p>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">Third-Party Information</h2>
                        <p className="text-gray-400 leading-relaxed">
                            The Platform may display market data from third-party sources. We do not verify the accuracy
                            of third-party data and are not responsible for any errors or omissions in such data.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">Limitation of Liability</h2>
                        <p className="text-gray-400 leading-relaxed">
                            Under no circumstances shall Cadreago De Private Limited, its directors, employees, or
                            affiliates be liable for any direct, indirect, incidental, consequential, special, or
                            exemplary damages arising from the use of the Platform, including but not limited to
                            trading losses, lost profits, or any other financial loss.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">Contact Us</h2>
                        <p className="text-gray-400 leading-relaxed mb-4">
                            If you have any questions about this Disclaimer, please contact us:
                        </p>
                        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                            <p className="text-white font-semibold">Cadreago De Private Limited</p>
                            <p className="text-gray-400">Email: cadreagode@gmx.com</p>
                            <p className="text-gray-400">Country: India</p>
                        </div>
                    </section>
                </div>
            </div>
        </main>
    )
}
