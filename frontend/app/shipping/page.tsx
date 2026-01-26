import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft, Truck, Clock, CheckCircle, AlertTriangle, Zap, Globe } from 'lucide-react'

export const metadata: Metadata = {
    title: 'Service Delivery Policy - Stocxer AI',
    description: 'Service delivery and access policy for Stocxer AI digital trading platform',
}

export default function ShippingPage() {
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
                <div className="text-center mb-16">
                    <div className="inline-flex items-center gap-3 mb-6">
                        <div className="p-4 rounded-2xl bg-gradient-to-br from-purple-600 to-blue-600">
                            <Globe className="w-8 h-8 text-white" />
                        </div>
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
                        Service Delivery Policy
                    </h1>
                    <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                        Learn how we deliver our digital services and ensure instant access to Stocxer AI platform.
                    </p>
                </div>

                {/* Digital Service Notice */}
                <div className="bg-blue-900/30 border border-blue-500/50 rounded-2xl p-8 mb-12">
                    <div className="flex items-start gap-4">
                        <div className="p-2 rounded-lg bg-blue-600 mt-1">
                            <Zap className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-white mb-2">Digital Service Platform</h3>
                            <p className="text-blue-100 leading-relaxed">
                                Stocxer AI is a <strong>100% digital platform</strong> providing AI-powered market analytics and trading signals. 
                                There are no physical products or shipping involved. All services are delivered instantly through our web platform.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Service Delivery */}
                <div className="bg-white/5 border border-gray-500/30 rounded-2xl p-8 mb-12">
                    <h2 className="text-2xl font-bold text-white mb-8 flex items-center gap-3">
                        <CheckCircle className="w-6 h-6 text-green-400" />
                        How Our Services Are Delivered
                    </h2>

                    <div className="space-y-8">
                        <div className="flex gap-6">
                            <div className="flex-shrink-0 w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                                1
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-white mb-2">Account Creation</h3>
                                <p className="text-gray-300">
                                    Upon successful registration, your Stocxer AI account is created instantly and you gain immediate access to our platform.
                                </p>
                            </div>
                        </div>

                        <div className="flex gap-6">
                            <div className="flex-shrink-0 w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                                2
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-white mb-2">Service Activation</h3>
                                <p className="text-gray-300">
                                    All features and tools become available immediately after account verification. Premium features are activated instantly upon subscription payment confirmation.
                                </p>
                            </div>
                        </div>

                        <div className="flex gap-6">
                            <div className="flex-shrink-0 w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                                3
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-white mb-2">24/7 Access</h3>
                                <p className="text-gray-300">
                                    Our platform is accessible 24/7 from any device with internet connection. No downloads or installations required.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Access & Availability */}
                <div className="bg-white/5 border border-gray-500/30 rounded-2xl p-8 mb-12">
                    <h2 className="text-2xl font-bold text-white mb-8 flex items-center gap-3">
                        <Clock className="w-6 h-6 text-blue-400" />
                        Service Availability
                    </h2>

                    <div className="grid md:grid-cols-2 gap-8">
                        <div>
                            <h3 className="text-lg font-semibold text-white mb-4">Instant Activation</h3>
                            <ul className="space-y-3 text-gray-300">
                                <li className="flex items-center gap-3">
                                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                                    Free trial access: Immediate
                                </li>
                                <li className="flex items-center gap-3">
                                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                                    Subscription activation: Within 5 minutes
                                </li>
                                <li className="flex items-center gap-3">
                                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                                    Credit purchases: Instant
                                </li>
                                <li className="flex items-center gap-3">
                                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                                    Feature upgrades: Real-time
                                </li>
                            </ul>
                        </div>

                        <div>
                            <h3 className="text-lg font-semibold text-white mb-4">Platform Uptime</h3>
                            <ul className="space-y-3 text-gray-300">
                                <li className="flex items-center gap-3">
                                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                                    99.9% uptime guarantee
                                </li>
                                <li className="flex items-center gap-3">
                                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                                    Global CDN for fast access
                                </li>
                                <li className="flex items-center gap-3">
                                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                                    Scheduled maintenance notifications
                                </li>
                                <li className="flex items-center gap-3">
                                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                                    Backup systems for reliability
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Access Requirements */}
                <div className="bg-white/5 border border-gray-500/30 rounded-2xl p-8 mb-12">
                    <h2 className="text-2xl font-bold text-white mb-8 flex items-center gap-3">
                        <Globe className="w-6 h-6 text-purple-400" />
                        Access Requirements
                    </h2>

                    <div className="grid md:grid-cols-2 gap-8">
                        <div>
                            <h3 className="text-lg font-semibold text-white mb-4">Technical Requirements</h3>
                            <ul className="space-y-2 text-gray-300">
                                <li>• Modern web browser (Chrome, Firefox, Safari, Edge)</li>
                                <li>• Stable internet connection</li>
                                <li>• JavaScript enabled</li>
                                <li>• No special software required</li>
                            </ul>
                        </div>

                        <div>
                            <h3 className="text-lg font-semibold text-white mb-4">Supported Devices</h3>
                            <ul className="space-y-2 text-gray-300">
                                <li>• Desktop computers (Windows, Mac, Linux)</li>
                                <li>• Laptops and tablets</li>
                                <li>• Mobile phones (responsive design)</li>
                                <li>• Any device with web browser</li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Service Interruptions */}
                <div className="bg-yellow-900/30 border border-yellow-500/50 rounded-2xl p-8 mb-12">
                    <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                        <AlertTriangle className="w-6 h-6 text-yellow-400" />
                        Service Interruptions
                    </h2>

                    <div className="space-y-6">
                        <div>
                            <h3 className="text-lg font-semibold text-white mb-2">Planned Maintenance</h3>
                            <p className="text-gray-300">
                                We perform scheduled maintenance during low-traffic hours (usually 2:00 AM - 4:00 AM IST) with advance notice via email and platform notifications.
                            </p>
                        </div>

                        <div>
                            <h3 className="text-lg font-semibold text-white mb-2">Unexpected Outages</h3>
                            <p className="text-gray-300">
                                In rare cases of unexpected service interruptions, we work to restore service within 2 hours and provide compensation for premium subscribers if downtime exceeds 4 hours.
                            </p>
                        </div>

                        <div>
                            <h3 className="text-lg font-semibold text-white mb-2">Status Updates</h3>
                            <p className="text-gray-300">
                                Real-time service status is available at <span className="text-purple-400">status.stocxer.ai</span> and through our support channels.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Contact Information */}
                <div className="bg-purple-900/30 border border-purple-500/30 rounded-2xl p-8">
                    <h2 className="text-2xl font-bold text-white mb-6">Need Help?</h2>
                    <p className="text-gray-300 mb-6">
                        If you experience any issues with service delivery or platform access, our support team is here to help.
                    </p>
                    <div className="flex flex-wrap gap-4">
                        <Link
                            href="/contact"
                            className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-semibold transition-colors"
                        >
                            Contact Support
                        </Link>
                        <Link
                            href="/support"
                            className="inline-flex items-center gap-2 px-6 py-3 border border-purple-500 text-purple-400 hover:bg-purple-500/10 rounded-xl font-semibold transition-colors"
                        >
                            Help Center
                        </Link>
                    </div>
                </div>

                {/* Last Updated */}
                <div className="mt-12 pt-8 border-t border-gray-700 text-center">
                    <p className="text-sm text-gray-400">
                        Last updated: January 2026
                    </p>
                </div>
            </div>
        </main>
    )
}