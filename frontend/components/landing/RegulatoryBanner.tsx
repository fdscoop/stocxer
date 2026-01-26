'use client'

import { AlertTriangle, ExternalLink, Info } from 'lucide-react'
import Link from 'next/link'

export default function RegulatoryBanner() {
    return (
        <div className="w-full bg-gradient-to-r from-yellow-500/10 via-orange-500/10 to-yellow-500/10 border-b border-yellow-500/20">
            <div className="max-w-6xl mx-auto px-3 sm:px-6 lg:px-8 py-2 sm:py-3">
                {/* Stack on mobile, side by side on desktop */}
                <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-4">
                    {/* Fyers Requirement */}
                    <div className="flex flex-wrap items-center justify-center gap-1.5 sm:gap-2">
                        <Info className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-blue-400 flex-shrink-0" />
                        <span className="text-xs sm:text-sm text-gray-300">
                            <span className="text-blue-400 font-semibold">Fyers account</span> required
                        </span>
                        <Link
                            href="https://fyers.in"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] sm:text-xs text-blue-400 hover:text-blue-300 bg-blue-500/20 hover:bg-blue-500/30 rounded transition-colors font-medium"
                        >
                            Open Account
                            <ExternalLink className="w-2.5 h-2.5 sm:w-3 sm:h-3" />
                        </Link>
                    </div>

                    {/* Separator - hidden on mobile */}
                    <div className="hidden sm:block w-px h-4 bg-gray-600" />

                    {/* Regulatory Notice */}
                    <div className="flex flex-wrap items-center justify-center gap-1.5 sm:gap-2">
                        <AlertTriangle className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-yellow-500 flex-shrink-0" />
                        <span className="text-xs sm:text-sm text-gray-400 text-center">
                            <span className="text-yellow-400">Educational & informational</span> — Not advice
                        </span>
                    </div>
                </div>
            </div>
        </div>
    )
}
