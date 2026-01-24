'use client'

import { Mail, MapPin, Building2, Cpu } from 'lucide-react'
import Link from 'next/link'

const footerLinks = {
    product: [
        { name: 'Dashboard', href: '/' },
        { name: 'Stock Screener', href: '/screener' },
        { name: 'Options Scanner', href: '/' },
        { name: 'Index Analyzer', href: '/analyzer' },
    ],
    account: [
        { name: 'Billing & Credits', href: '/billing' },
        { name: 'Subscription', href: '/subscription' },
        { name: 'Support', href: '/support' },
    ],
    resources: [
        { name: 'How It Works', href: '#how-it-works' },
        { name: 'Pricing', href: '#pricing' },
        { name: 'FAQ', href: '/faq' },
    ],
    legal: [
        { name: 'Privacy Policy', href: '/privacy' },
        { name: 'Terms & Conditions', href: '/terms' },
        { name: 'Disclaimer', href: '/disclaimer' },
        { name: 'Refund Policy', href: '/refund' },
    ],
}

export default function FooterSection() {
    return (
        <footer className="bg-[#060608] border-t border-white/5">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
                {/* Main Footer Content */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 mb-12">
                    {/* Brand Column */}
                    <div className="lg:col-span-2">
                        {/* Logo */}
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
                                <Cpu className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <span className="text-xl font-bold text-white">Stocxer AI</span>
                                <div className="text-xs text-purple-400">Powered by Watchman AI v3.5</div>
                            </div>
                        </div>

                        <p className="text-gray-400 text-sm mb-6 max-w-sm">
                            Data-driven market analytics platform providing probability-based insights
                            for informed trading decisions.
                        </p>

                        {/* Company Info */}
                        <div className="space-y-3 text-sm">
                            <div className="flex items-center gap-2 text-gray-400">
                                <Building2 className="w-4 h-4 text-purple-400" />
                                <span>FDS COOP LLP</span>
                            </div>
                            <div className="flex items-center gap-2 text-gray-400">
                                <MapPin className="w-4 h-4 text-purple-400" />
                                <span>India</span>
                            </div>
                            <div className="flex items-center gap-2 text-gray-400">
                                <Mail className="w-4 h-4 text-purple-400" />
                                <a href="mailto:help@stocxer.in" className="hover:text-purple-400 transition-colors">
                                    help@stocxer.in
                                </a>
                            </div>
                        </div>
                    </div>

                    {/* Product Links */}
                    <div>
                        <h4 className="text-white font-semibold mb-4">Product</h4>
                        <ul className="space-y-3">
                            {footerLinks.product.map((link, i) => (
                                <li key={i}>
                                    <Link
                                        href={link.href}
                                        className="text-gray-400 text-sm hover:text-purple-400 transition-colors"
                                    >
                                        {link.name}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Account Links */}
                    <div>
                        <h4 className="text-white font-semibold mb-4">Account</h4>
                        <ul className="space-y-3">
                            {footerLinks.account.map((link, i) => (
                                <li key={i}>
                                    <Link
                                        href={link.href}
                                        className="text-gray-400 text-sm hover:text-purple-400 transition-colors"
                                    >
                                        {link.name}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Resources Links */}
                    <div>
                        <h4 className="text-white font-semibold mb-4">Resources</h4>
                        <ul className="space-y-3">
                            {footerLinks.resources.map((link, i) => (
                                <li key={i}>
                                    <Link
                                        href={link.href}
                                        className="text-gray-400 text-sm hover:text-purple-400 transition-colors"
                                    >
                                        {link.name}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Legal Links */}
                    <div>
                        <h4 className="text-white font-semibold mb-4">Legal</h4>
                        <ul className="space-y-3">
                            {footerLinks.legal.map((link, i) => (
                                <li key={i}>
                                    <Link
                                        href={link.href}
                                        className="text-gray-400 text-sm hover:text-purple-400 transition-colors"
                                    >
                                        {link.name}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="pt-8 border-t border-white/5">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                        <p className="text-gray-500 text-sm text-center md:text-left">
                            © {new Date().getFullYear()} FDS COOP LLP. All rights reserved.
                        </p>

                        <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span>🇮🇳 Made in India</span>
                            <span>•</span>
                            <span>Not SEBI Registered</span>
                        </div>
                    </div>

                    {/* Final Disclaimer */}
                    <p className="mt-6 text-center text-xs text-gray-600 max-w-3xl mx-auto">
                        Stocxer AI is a market analytics tool for informational purposes only.
                        It does not constitute investment advice. Trading involves risk.
                        Please consult a qualified financial advisor.
                    </p>
                </div>
            </div>
        </footer>
    )
}
