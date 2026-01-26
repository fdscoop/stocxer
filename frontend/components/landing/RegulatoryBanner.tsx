'use client'

import { AlertTriangle, ExternalLink, Info } from 'lucide-react'
import Link from 'next/link'

export default function RegulatoryBanner() {
    return (
        <div className="w-full bg-gradient-to-r from-yellow-500/10 via-orange-500/10 to-yellow-500/10 border-b border-yellow-500/20">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
                {/* Two-line banner for mobile, single line for desktop */}
                <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-4 text-center sm:text-left">
                    {/* Fyers Requirement */}
                    <div className="flex items-center gap-2">
                        <Info className="w-4 h-4 text-blue-400 flex-shrink-0" />
                        <span className="text-sm text-gray-300">
                            <span className="text-blue-400 font-semibold">Fyers trading account required</span>
                            {' '}to use Stocxer AI
                        </span>
                        <Link
                            href="https://fyers.in"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                        >
                            Open Fyers Account
                            <ExternalLink className="w-3 h-3" />
                        </Link>
                    </div>

                    {/* Separator */}
                    <div className="hidden sm:block w-px h-4 bg-gray-600" />

                    {/* Regulatory Notice */}
                    <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-yellow-500 flex-shrink-0" />
                        <span className="text-sm text-gray-400">
                            <span className="text-yellow-400">For analytical, research & informational purposes</span>
                            {' '}— Not investment advice
                        </span>
                    </div>
                </div>
            </div>
        </div>
    )
}
