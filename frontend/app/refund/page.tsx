import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft, RotateCcw } from 'lucide-react'

export const metadata: Metadata = {
    title: 'Refund Policy - Stocxer AI',
    description: 'Refund and cancellation policy for Stocxer AI subscriptions',
}

export default function RefundPage() {
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
                    <div className="p-3 rounded-xl bg-green-500/20">
                        <RotateCcw className="w-8 h-8 text-green-400" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-white">Refund Policy</h1>
                        <p className="text-gray-400">Last updated: January 2026</p>
                    </div>
                </div>

                {/* Quick Summary */}
                <div className="mb-8 p-6 rounded-2xl bg-gradient-to-b from-green-500/10 to-blue-500/10 border border-green-500/30">
                    <h2 className="text-lg font-bold text-green-400 mb-3">Quick Summary</h2>
                    <ul className="text-gray-300 space-y-2">
                        <li>✅ <strong className="text-white">7-day money-back guarantee</strong> for first-time subscribers</li>
                        <li>✅ Prorated refunds for annual plans within 30 days</li>
                        <li>✅ Cancel anytime with no additional charges</li>
                    </ul>
                </div>

                {/* Content */}
                <div className="prose prose-invert max-w-none space-y-8">
                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">1. Overview</h2>
                        <p className="text-gray-400 leading-relaxed">
                            We want you to be satisfied with Stocxer AI. This Refund Policy outlines the conditions
                            under which we offer refunds for subscription payments made through our platform.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">2. 7-Day Money-Back Guarantee (New Subscribers)</h2>
                        <p className="text-gray-400 leading-relaxed mb-4">
                            If you are a first-time subscriber to any paid plan (Starter or Pro), you are eligible
                            for a full refund within 7 days of your initial purchase, no questions asked.
                        </p>
                        <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
                            <p className="text-blue-300 text-sm">
                                <strong>Note:</strong> This guarantee applies only to your first subscription.
                                Re-subscriptions after cancellation are not eligible for the 7-day guarantee.
                            </p>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">3. Monthly Subscriptions</h2>
                        <ul className="text-gray-400 leading-relaxed list-disc pl-6 space-y-2">
                            <li>Monthly subscriptions can be cancelled at any time</li>
                            <li>No refunds for partial months after the 7-day period</li>
                            <li>Your access continues until the end of the current billing period</li>
                            <li>No automatic renewal charges after cancellation</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">4. Annual Subscriptions</h2>
                        <p className="text-gray-400 leading-relaxed mb-4">
                            For annual subscriptions:
                        </p>
                        <ul className="text-gray-400 leading-relaxed list-disc pl-6 space-y-2">
                            <li><strong className="text-white">Within 30 days:</strong> Prorated refund minus one month&apos;s subscription</li>
                            <li><strong className="text-white">After 30 days:</strong> No refund, but you can cancel to prevent renewal</li>
                            <li>Access continues until the end of the annual period</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">5. Non-Refundable Situations</h2>
                        <p className="text-gray-400 leading-relaxed mb-4">
                            Refunds will NOT be provided in the following cases:
                        </p>
                        <ul className="text-gray-400 leading-relaxed list-disc pl-6 space-y-2">
                            <li>Account suspended or terminated due to Terms of Service violations</li>
                            <li>Trading losses or unsatisfactory investment results</li>
                            <li>Dissatisfaction with analytical insights or probability assessments</li>
                            <li>Failure to use the platform during the subscription period</li>
                            <li>Technical issues on the user&apos;s end (device, internet, browser compatibility)</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">6. How to Request a Refund</h2>
                        <p className="text-gray-400 leading-relaxed mb-4">
                            To request a refund:
                        </p>
                        <ol className="text-gray-400 leading-relaxed list-decimal pl-6 space-y-2">
                            <li>Email us at <span className="text-purple-400">help@stocxer.in</span></li>
                            <li>Include your registered email address and subscription details</li>
                            <li>Provide the reason for your refund request</li>
                            <li>Allow 3-5 business days for review and processing</li>
                        </ol>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">7. Refund Processing</h2>
                        <ul className="text-gray-400 leading-relaxed list-disc pl-6 space-y-2">
                            <li>Approved refunds are processed within 5-7 business days</li>
                            <li>Refunds are credited to the original payment method</li>
                            <li>Bank processing times may add 3-10 additional business days</li>
                            <li>Refund amount is in Indian Rupees (₹)</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">8. Cancellation</h2>
                        <p className="text-gray-400 leading-relaxed mb-4">
                            You can cancel your subscription at any time:
                        </p>
                        <ul className="text-gray-400 leading-relaxed list-disc pl-6 space-y-2">
                            <li>Log into your account dashboard</li>
                            <li>Navigate to subscription settings</li>
                            <li>Click &quot;Cancel Subscription&quot;</li>
                            <li>Alternatively, email us at help@stocxer.in</li>
                        </ul>
                        <div className="mt-4 p-4 rounded-xl bg-green-500/10 border border-green-500/20">
                            <p className="text-green-300 text-sm">
                                <strong>No Penalties:</strong> There are no cancellation fees. You will not be charged
                                after cancellation, and your access continues until the end of your current billing period.
                            </p>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">9. Disputes</h2>
                        <p className="text-gray-400 leading-relaxed">
                            If you believe a charge was made in error or you disagree with a refund decision,
                            please contact us within 30 days. We will review your case and work to resolve the
                            issue fairly.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">10. Contact Us</h2>
                        <p className="text-gray-400 leading-relaxed mb-4">
                            For refund requests or questions about this policy:
                        </p>
                        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                            <p className="text-white font-semibold">Cadreago De Private Limited</p>
                            <p className="text-gray-400">Email: help@stocxer.in</p>
                            <p className="text-gray-400">Subject: Refund Request</p>
                            <p className="text-gray-400">Country: India</p>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">11. Policy Changes</h2>
                        <p className="text-gray-400 leading-relaxed">
                            We reserve the right to modify this Refund Policy at any time. Changes will be posted
                            on this page with an updated &quot;Last updated&quot; date. Continued use of the Platform after
                            changes constitutes acceptance of the new policy.
                        </p>
                    </section>
                </div>
            </div>
        </main>
    )
}
