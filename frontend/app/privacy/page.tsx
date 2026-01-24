import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft, Shield } from 'lucide-react'

export const metadata: Metadata = {
    title: 'Privacy Policy - Stocxer AI',
    description: 'Privacy Policy for Stocxer AI market analytics platform by FDS COOP LLP',
}

export default function PrivacyPage() {
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
                        <Shield className="w-8 h-8 text-purple-400" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-white">Privacy Policy</h1>
                        <p className="text-gray-400">Last updated: January 2026</p>
                    </div>
                </div>

                {/* Content */}
                <div className="prose prose-invert max-w-none space-y-8">
                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">1. Introduction</h2>
                        <p className="text-gray-400 leading-relaxed">
                            Welcome to Stocxer AI, operated by FDS COOP LLP (&quot;Company&quot;, &quot;we&quot;, &quot;us&quot;, or &quot;our&quot;).
                            This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you
                            use our market analytics platform.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">2. Information We Collect</h2>
                        <div className="text-gray-400 leading-relaxed space-y-4">
                            <p><strong className="text-white">Personal Information:</strong></p>
                            <ul className="list-disc pl-6 space-y-2">
                                <li>Email address (for account registration)</li>
                                <li>Name (optional)</li>
                                <li>Payment information (processed securely via third-party payment processors)</li>
                            </ul>
                            <p><strong className="text-white">Usage Data:</strong></p>
                            <ul className="list-disc pl-6 space-y-2">
                                <li>Scan history and preferences</li>
                                <li>Dashboard interactions</li>
                                <li>Device information and IP address</li>
                                <li>Browser type and version</li>
                            </ul>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">3. How We Use Your Information</h2>
                        <ul className="text-gray-400 leading-relaxed list-disc pl-6 space-y-2">
                            <li>To provide and maintain the Stocxer AI platform</li>
                            <li>To personalize your dashboard experience</li>
                            <li>To process payments and manage subscriptions</li>
                            <li>To communicate service updates and important notices</li>
                            <li>To improve our analytical models and features</li>
                            <li>To comply with legal obligations</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">4. Data Security</h2>
                        <p className="text-gray-400 leading-relaxed">
                            We implement industry-standard security measures to protect your personal information.
                            This includes encryption of data in transit and at rest, secure authentication protocols,
                            and regular security audits. However, no method of transmission over the Internet is 100% secure.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">5. Third-Party Services</h2>
                        <p className="text-gray-400 leading-relaxed">
                            We may use third-party services for payment processing, analytics, and hosting.
                            These services have their own privacy policies and we encourage you to review them.
                            We do not sell your personal information to third parties.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">6. Data Retention</h2>
                        <p className="text-gray-400 leading-relaxed">
                            We retain your personal information for as long as your account is active or as needed
                            to provide services. You may request deletion of your account and associated data at any time
                            by contacting our support team.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">7. Your Rights</h2>
                        <ul className="text-gray-400 leading-relaxed list-disc pl-6 space-y-2">
                            <li>Access your personal data</li>
                            <li>Correct inaccurate data</li>
                            <li>Request deletion of your data</li>
                            <li>Object to processing of your data</li>
                            <li>Export your data in a portable format</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">8. Cookies</h2>
                        <p className="text-gray-400 leading-relaxed">
                            We use cookies and similar tracking technologies to enhance your experience.
                            Essential cookies are required for the platform to function. You can manage
                            cookie preferences through your browser settings.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">9. Contact Us</h2>
                        <p className="text-gray-400 leading-relaxed">
                            If you have questions about this Privacy Policy, please contact us at:
                        </p>
                        <div className="mt-4 p-4 rounded-xl bg-white/5 border border-white/10">
                            <p className="text-white font-semibold">FDS COOP LLP</p>
                            <p className="text-gray-400">Email: help@stocxer.in</p>
                            <p className="text-gray-400">Country: India</p>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">10. Changes to This Policy</h2>
                        <p className="text-gray-400 leading-relaxed">
                            We may update this Privacy Policy from time to time. We will notify you of any changes
                            by posting the new policy on this page and updating the &quot;Last updated&quot; date.
                        </p>
                    </section>
                </div>
            </div>
        </main>
    )
}
