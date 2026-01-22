import type { Metadata } from 'next'
import HeroSection from '@/components/landing/HeroSection'
import FeaturesSection from '@/components/landing/FeaturesSection'
import WatchmanAISection from '@/components/landing/WatchmanAISection'
import HowItWorksSection from '@/components/landing/HowItWorksSection'
import BenefitsSection from '@/components/landing/BenefitsSection'
import PricingSection from '@/components/landing/PricingSection'
import DisclaimerSection from '@/components/landing/DisclaimerSection'
import FooterSection from '@/components/landing/FooterSection'

export const metadata: Metadata = {
    title: 'Stocxer AI - Data-Driven Market Analysis for Smarter Trading',
    description: 'Scan indices and stocks, apply deep analytical models with Watchman AI v3.5, and view clean, probability-based insights for informed trading decisions.',
    keywords: [
        'stock analysis',
        'market analytics',
        'trading insights',
        'NIFTY analysis',
        'BANKNIFTY scanner',
        'options analysis',
        'India stock market',
        'trading dashboard',
        'probability analysis',
        'Watchman AI',
    ],
    openGraph: {
        title: 'Stocxer AI - Data-Driven Market Analysis',
        description: 'Advanced market analytics platform powered by Watchman AI v3.5. Get probability-based insights for smarter trading decisions.',
        type: 'website',
        locale: 'en_IN',
        siteName: 'Stocxer AI',
    },
    twitter: {
        card: 'summary_large_image',
        title: 'Stocxer AI - Data-Driven Market Analysis',
        description: 'Advanced market analytics platform powered by Watchman AI v3.5.',
    },
    robots: {
        index: true,
        follow: true,
    },
}

export default function LandingPage() {
    return (
        <main className="min-h-screen bg-[#0a0a0f]">
            {/* Hero Section - Above the Fold */}
            <HeroSection />

            {/* What Stocxer AI Does */}
            <FeaturesSection />

            {/* Watchman AI v3.5 Spotlight */}
            <WatchmanAISection />

            {/* How It Works - 3 Steps */}
            <section id="how-it-works">
                <HowItWorksSection />
            </section>

            {/* Key Benefits */}
            <BenefitsSection />

            {/* Pricing Section */}
            <section id="pricing">
                <PricingSection />
            </section>

            {/* Legal Disclaimer */}
            <DisclaimerSection />

            {/* Footer */}
            <FooterSection />
        </main>
    )
}
