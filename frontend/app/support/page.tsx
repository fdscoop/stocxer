import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft, Mail, MessageCircle, Clock, Send, HelpCircle, FileText, AlertTriangle, CreditCard } from 'lucide-react'

export const metadata: Metadata = {
    title: 'Support - Stocxer AI',
    description: 'Get help and support for Stocxer AI market analytics platform',
}

const supportCategories = [
    {
        icon: HelpCircle,
        title: 'General Questions',
        description: 'Questions about features, usage, and platform capabilities',
        color: 'purple',
    },
    {
        icon: AlertTriangle,
        title: 'Technical Issues',
        description: 'Problems with data loading, connections, or platform errors',
        color: 'orange',
    },
    {
        icon: CreditCard,
        title: 'Billing & Subscriptions',
        description: 'Payment issues, plan changes, refunds, and invoices',
        color: 'green',
    },
    {
        icon: FileText,
        title: 'Account Management',
        description: 'Login issues, profile updates, and account settings',
        color: 'blue',
    },
]

const quickLinks = [
    { name: 'FAQ', href: '/faq', description: 'Find answers to common questions' },
    { name: 'Privacy Policy', href: '/privacy', description: 'Learn how we protect your data' },
    { name: 'Terms & Conditions', href: '/terms', description: 'Understand our service terms' },
    { name: 'Refund Policy', href: '/refund', description: 'View our refund and cancellation policy' },
]

export default function SupportPage() {
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
                        <MessageCircle className="w-8 h-8 text-blue-400" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-white">Support Center</h1>
                        <p className="text-gray-400">We&apos;re here to help you succeed</p>
                    </div>
                </div>

                {/* Main Contact Card */}
                <div className="mb-12 p-8 rounded-2xl bg-gradient-to-br from-purple-600/20 to-blue-600/20 border border-purple-500/30">
                    <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                        <div>
                            <h2 className="text-2xl font-bold text-white mb-2">Need Help?</h2>
                            <p className="text-gray-300 max-w-lg">
                                Our support team is available to assist you with any questions or issues.
                                We typically respond within 24-48 hours during business days.
                            </p>
                        </div>
                        <a
                            href="mailto:help@stocxer.in"
                            className="inline-flex items-center gap-3 px-8 py-4 rounded-xl bg-purple-600 text-white font-semibold hover:bg-purple-500 transition-all hover:scale-105"
                        >
                            <Mail className="w-5 h-5" />
                            Email Support
                        </a>
                    </div>
                    <div className="mt-6 pt-6 border-t border-white/10 flex flex-wrap items-center gap-6 text-sm">
                        <div className="flex items-center gap-2 text-gray-400">
                            <Mail className="w-4 h-4 text-purple-400" />
                            <span>help@stocxer.in</span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-400">
                            <Clock className="w-4 h-4 text-purple-400" />
                            <span>Response time: 24-48 hours</span>
                        </div>
                    </div>
                </div>

                {/* Support Categories */}
                <section className="mb-12">
                    <h2 className="text-xl font-bold text-white mb-6">What do you need help with?</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {supportCategories.map((category, i) => {
                            const Icon = category.icon
                            const colorClasses = {
                                purple: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
                                orange: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
                                green: 'bg-green-500/20 text-green-400 border-green-500/30',
                                blue: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                            }
                            const classes = colorClasses[category.color as keyof typeof colorClasses]

                            return (
                                <a
                                    key={i}
                                    href={`mailto:help@stocxer.in?subject=${encodeURIComponent(category.title)}`}
                                    className="p-5 rounded-xl bg-white/5 border border-white/10 hover:border-purple-500/30 transition-all hover:bg-white/[0.07] group"
                                >
                                    <div className={`w-12 h-12 rounded-lg ${classes} flex items-center justify-center mb-4`}>
                                        <Icon className="w-6 h-6" />
                                    </div>
                                    <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-purple-300 transition-colors">
                                        {category.title}
                                    </h3>
                                    <p className="text-gray-400 text-sm">{category.description}</p>
                                </a>
                            )
                        })}
                    </div>
                </section>

                {/* Tips for Faster Support */}
                <section className="mb-12 p-6 rounded-2xl bg-blue-500/10 border border-blue-500/20">
                    <div className="flex items-start gap-4">
                        <div className="p-2 rounded-lg bg-blue-500/20">
                            <Send className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                            <h2 className="text-lg font-bold text-white mb-3">Tips for Faster Support</h2>
                            <ul className="text-gray-400 space-y-2 text-sm">
                                <li className="flex items-start gap-2">
                                    <span className="text-blue-400">•</span>
                                    <span>Include your registered email address in your support request</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-blue-400">•</span>
                                    <span>Describe the issue clearly with steps to reproduce (if applicable)</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-blue-400">•</span>
                                    <span>Include screenshots of any error messages</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-blue-400">•</span>
                                    <span>Mention your browser and device type</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-blue-400">•</span>
                                    <span>For billing queries, include your transaction ID or invoice number</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </section>

                {/* Quick Links */}
                <section className="mb-12">
                    <h2 className="text-xl font-bold text-white mb-6">Quick Links</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {quickLinks.map((link, i) => (
                            <Link
                                key={i}
                                href={link.href}
                                className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-purple-500/30 transition-all group"
                            >
                                <h3 className="text-white font-semibold mb-1 group-hover:text-purple-300 transition-colors">
                                    {link.name}
                                </h3>
                                <p className="text-gray-500 text-sm">{link.description}</p>
                            </Link>
                        ))}
                    </div>
                </section>

                {/* Company Info */}
                <section className="p-6 rounded-2xl bg-white/5 border border-white/10">
                    <h2 className="text-xl font-bold text-white mb-4">Company Information</h2>
                    <div className="space-y-3 text-gray-400">
                        <p><span className="text-white font-semibold">Company:</span> FDS COOP LLP</p>
                        <p><span className="text-white font-semibold">Email:</span> help@stocxer.in</p>
                        <p><span className="text-white font-semibold">Country:</span> India</p>
                    </div>
                    <div className="mt-6 pt-6 border-t border-white/10">
                        <p className="text-gray-500 text-sm">
                            Business hours: Monday to Friday, 10:00 AM - 6:00 PM IST
                        </p>
                    </div>
                </section>
            </div>
        </main>
    )
}
