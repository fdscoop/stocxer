import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft, FileText } from 'lucide-react'

export const metadata: Metadata = {
    title: 'Terms & Conditions - Stocxer AI',
    description: 'Terms and Conditions for using Stocxer AI market analytics platform',
}

export default function TermsPage() {
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
                    <div className="p-3 rounded-xl bg-blue-500/20">
                        <FileText className="w-8 h-8 text-blue-400" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-white">Terms & Conditions</h1>
                        <p className="text-gray-400">Last updated: January 2026</p>
                    </div>
                </div>

                {/* Content */}
                <div className="prose prose-invert max-w-none space-y-8">
                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">1. Acceptance of Terms</h2>
                        <p className="text-gray-400 leading-relaxed">
                            By accessing or using Stocxer AI (&quot;the Platform&quot;), operated by Cadreago De Private Limited,
                            you agree to be bound by these Terms & Conditions. If you do not agree, please do not use
                            the Platform.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">2. Description of Service</h2>
                        <p className="text-gray-400 leading-relaxed">
                            Stocxer AI is a data analysis platform that provides market data analytics, probability-based patterns,
                            and analytical tools for Indian stock market instruments. The platform includes features
                            powered by Watchman AI v3.5, our proprietary analytical engine.
                        </p>
                        <div className="mt-4 p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
                            <p className="text-yellow-300 text-sm">
                                <strong>Important:</strong> Stocxer AI provides data analysis tools for analytical, research,
                                and informational purposes only. It does NOT provide investment advice,
                                trading recommendations, or guarantees of profit.
                            </p>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">3. User Accounts</h2>
                        <ul className="text-gray-400 leading-relaxed list-disc pl-6 space-y-2">
                            <li>You must provide accurate information during registration</li>
                            <li>You are responsible for maintaining the security of your account</li>
                            <li>You must be at least 18 years old to use the Platform</li>
                            <li>One account per user unless otherwise authorized</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">4. Subscription & Payments</h2>
                        <ul className="text-gray-400 leading-relaxed list-disc pl-6 space-y-2">
                            <li>Subscription fees are charged in Indian Rupees (₹)</li>
                            <li>All prices are exclusive of applicable taxes (GST)</li>
                            <li>Subscriptions auto-renew unless cancelled</li>
                            <li>Refunds are subject to our Refund Policy</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">5. Acceptable Use</h2>
                        <p className="text-gray-400 leading-relaxed mb-4">You agree NOT to:</p>
                        <ul className="text-gray-400 leading-relaxed list-disc pl-6 space-y-2">
                            <li>Use the Platform for any illegal purpose</li>
                            <li>Attempt to reverse engineer or copy our analytical models</li>
                            <li>Share your account credentials with others</li>
                            <li>Scrape, harvest, or automatically extract data from the Platform</li>
                            <li>Redistribute or resell Platform content without authorization</li>
                            <li>Interfere with the Platform&apos;s security or functionality</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">6. Intellectual Property</h2>
                        <p className="text-gray-400 leading-relaxed">
                            All content, including Watchman AI v3.5, analytical models, software, design, and trademarks,
                            are owned by Cadreago De Private Limited. You may not copy, modify, or distribute any
                            Platform content without express written permission.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">7. Disclaimer of Warranties</h2>
                        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                            <p className="text-red-300 text-sm">
                                THE PLATFORM IS PROVIDED &quot;AS IS&quot; WITHOUT WARRANTIES OF ANY KIND. WE DO NOT GUARANTEE
                                THE ACCURACY, COMPLETENESS, OR RELIABILITY OF ANY ANALYSIS OR INSIGHTS. TRADING INVOLVES
                                SUBSTANTIAL RISK OF LOSS. PAST PERFORMANCE IS NOT INDICATIVE OF FUTURE RESULTS.
                            </p>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">8. Limitation of Liability</h2>
                        <p className="text-gray-400 leading-relaxed">
                            To the maximum extent permitted by law, Cadreago De Private Limited shall not be liable
                            for any indirect, incidental, special, or consequential damages arising from your use of
                            the Platform, including but not limited to trading losses, lost profits, or data loss.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">9. Regulatory Compliance</h2>
                        <div className="p-4 rounded-xl bg-orange-500/10 border border-orange-500/20">
                            <p className="text-orange-300 text-sm">
                                Stocxer AI and Cadreago De Private Limited are NOT registered as SEBI investment advisers.
                                The Platform provides market analytics tools only and should not be construed as
                                personalized investment advice.
                            </p>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">10. Governing Law</h2>
                        <p className="text-gray-400 leading-relaxed">
                            These Terms shall be governed by and construed in accordance with the laws of India.
                            Any disputes shall be subject to the exclusive jurisdiction of the courts in
                            Bangalore, Karnataka, India.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">11. Termination</h2>
                        <p className="text-gray-400 leading-relaxed">
                            We reserve the right to suspend or terminate your account at any time for violation
                            of these Terms or for any other reason at our sole discretion. Upon termination,
                            your right to use the Platform will immediately cease.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">12. Contact Information</h2>
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
