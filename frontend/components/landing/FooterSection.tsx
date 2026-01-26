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
        { name: 'Contact Us', href: '/contact' },
    ],
    resources: [
        { name: 'How It Works', href: '#how-it-works' },
        { name: 'Pricing', href: '#pricing' },
        { name: 'FAQ', href: '/faq' },
    ],
    legal: [
        { name: 'Privacy Policy', href: '/privacy' },
        { name: 'Terms & Conditions', href: '/terms' },
        { name: 'Service Delivery Policy', href: '/shipping' },
        { name: 'Refund Policy', href: '/refund' },
        { name: 'Disclaimer', href: '/disclaimer' },
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
                            AI-powered data analysis tool providing probability-based patterns
                            for analytical and research purposes.
                        </p>

                        {/* Company Info */}
                        <div className="space-y-3 text-sm">
                            <div className="flex items-center gap-2 text-gray-400">
                                <Building2 className="w-4 h-4 text-purple-400" />
                                <span>Cadreago De Private Limited</span>
                            </div>
                            <div className="flex items-center gap-2 text-gray-400">
                                <MapPin className="w-4 h-4 text-purple-400" />
                                <span>India</span>
                            </div>
                            <div className="flex items-center gap-2 text-gray-400">
                                <Mail className="w-4 h-4 text-purple-400" />
                                <a href="mailto:cadreagode@gmx.com" className="hover:text-purple-400 transition-colors">
                                    cadreagode@gmx.com
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
                            © {new Date().getFullYear()} Cadreago De Private Limited. All rights reserved.
                        </p>

                        <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span>🇮🇳 Made in India</span>
                            <span>•</span>
                            <span>Not SEBI Registered</span>
                        </div>
                    </div>

                    {/* Final Disclaimer */}
                    <p className="mt-6 text-center text-xs text-gray-600 max-w-3xl mx-auto">
                        Stocxer AI is a data analysis tool for analytical, research, and informational purposes only.
                        It does not constitute investment advice or recommendations. Trading and investing involve risk.
                        Please consult a SEBI-registered financial advisor before making any financial decisions.
                    </p>
                </div>
            </div>
        </footer>
    )
}
