import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft, Mail, Phone, MapPin, Clock, Send, MessageSquare } from 'lucide-react'

export const metadata: Metadata = {
    title: 'Contact Us - Stocxer AI',
    description: 'Get in touch with Stocxer AI team for support, inquiries, and feedback',
}

export default function ContactPage() {
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
                            <Mail className="w-8 h-8 text-white" />
                        </div>
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
                        Contact Us
                    </h1>
                    <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                        We're here to help! Get in touch with our team for any questions, support, or feedback about Stocxer AI.
                    </p>
                </div>

                {/* Contact Methods */}
                <div className="grid md:grid-cols-2 gap-8 mb-16">
                    {/* Email Support */}
                    <div className="bg-white/5 border border-purple-500/30 rounded-2xl p-8">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="p-3 rounded-xl bg-purple-600">
                                <Mail className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white">Email Support</h3>
                                <p className="text-gray-400">Get detailed help via email</p>
                            </div>
                        </div>
                        <div className="space-y-3">
                            <div>
                                <p className="text-sm text-gray-400">General Inquiries</p>
                                <a href="mailto:support@stocxer.ai" className="text-purple-400 hover:text-purple-300 font-medium">
                                    support@stocxer.ai
                                </a>
                            </div>
                            <div>
                                <p className="text-sm text-gray-400">Technical Support</p>
                                <a href="mailto:tech@stocxer.ai" className="text-purple-400 hover:text-purple-300 font-medium">
                                    tech@stocxer.ai
                                </a>
                            </div>
                            <div>
                                <p className="text-sm text-gray-400">Business Inquiries</p>
                                <a href="mailto:business@stocxer.ai" className="text-purple-400 hover:text-purple-300 font-medium">
                                    business@stocxer.ai
                                </a>
                            </div>
                        </div>
                    </div>

                    {/* Live Chat */}
                    <div className="bg-white/5 border border-blue-500/30 rounded-2xl p-8">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="p-3 rounded-xl bg-blue-600">
                                <MessageSquare className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white">Support Portal</h3>
                                <p className="text-gray-400">Quick help and resources</p>
                            </div>
                        </div>
                        <p className="text-gray-300 mb-6">
                            Visit our support portal for instant help, FAQs, and troubleshooting guides.
                        </p>
                        <Link
                            href="/support"
                            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold transition-colors"
                        >
                            <MessageSquare className="w-5 h-5" />
                            Visit Support Portal
                        </Link>
                    </div>
                </div>

                {/* Company Information */}
                <div className="bg-white/5 border border-gray-500/30 rounded-2xl p-8 mb-16">
                    <h3 className="text-2xl font-bold text-white mb-8 flex items-center gap-3">
                        <MapPin className="w-6 h-6 text-purple-400" />
                        Company Information
                    </h3>
                    <div className="grid md:grid-cols-2 gap-8">
                        <div>
                            <h4 className="text-lg font-semibold text-white mb-4">Cadreago De Private Limited</h4>
                            <div className="space-y-3 text-gray-300">
                                <div>
                                    <p className="text-sm text-gray-400">Registered Office</p>
                                    <p>India</p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-400">Business Type</p>
                                    <p>Financial Technology & AI Analytics</p>
                                </div>
                            </div>
                        </div>
                        <div>
                            <h4 className="text-lg font-semibold text-white mb-4">Business Hours</h4>
                            <div className="space-y-2 text-gray-300">
                                <div className="flex items-center gap-2">
                                    <Clock className="w-4 h-4 text-purple-400" />
                                    <span>Monday - Friday: 9:00 AM - 6:00 PM IST</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Clock className="w-4 h-4 text-purple-400" />
                                    <span>Saturday: 10:00 AM - 4:00 PM IST</span>
                                </div>
                                <p className="text-sm text-gray-400 mt-3">
                                    Email support is available 24/7 with responses within 24 hours
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Response Times */}
                <div className="bg-gradient-to-r from-purple-900/30 to-blue-900/30 border border-purple-500/30 rounded-2xl p-8">
                    <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                        <Clock className="w-6 h-6 text-purple-400" />
                        Response Times
                    </h3>
                    <div className="grid md:grid-cols-3 gap-6">
                        <div className="text-center">
                            <div className="text-3xl font-bold text-purple-400 mb-2">&lt; 1 Hour</div>
                            <p className="text-gray-300">Critical Issues</p>
                            <p className="text-sm text-gray-400">Platform downtime, payment issues</p>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-blue-400 mb-2">&lt; 24 Hours</div>
                            <p className="text-gray-300">General Support</p>
                            <p className="text-sm text-gray-400">Feature questions, account help</p>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-cyan-400 mb-2">&lt; 48 Hours</div>
                            <p className="text-gray-300">Feature Requests</p>
                            <p className="text-sm text-gray-400">New features, integrations</p>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="mt-16 text-center">
                    <p className="text-gray-400 text-sm">
                        For urgent technical issues, please mark your email as "URGENT" in the subject line.
                    </p>
                </div>
            </div>
        </main>
    )
}