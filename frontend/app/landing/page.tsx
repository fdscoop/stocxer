import type { Metadata } from 'next'
import HeroSection from '@/components/landing/HeroSection'
import FeaturesSection from '@/components/landing/FeaturesSection'
import HowItWorksSection from '@/components/landing/HowItWorksSection'
import CompetitorComparison from '@/components/landing/CompetitorComparison'
import WatchmanAISection from '@/components/landing/WatchmanAISection'
import AnalysisFeaturesDetail from '@/components/landing/AnalysisFeaturesDetail'
import AIIntegrationSection from '@/components/landing/AIIntegrationSection'
import PricingSection from '@/components/landing/PricingSection'
import FAQSection from '@/components/landing/FAQSection'
import DisclaimerSection from '@/components/landing/DisclaimerSection'
import FooterSection from '@/components/landing/FooterSection'

export const metadata: Metadata = {
    title: 'Stocxer AI - India\'s First ICT + AI Market Analysis Platform',
    description: 'Stop interpreting raw data. Get consolidated probability analysis powered by Smart Money Concepts, Machine Learning, and News Sentiment for informed decision-making.',
    keywords: [
        'ICT analysis India',
        'Smart Money Concepts',
        'ML market analysis',
        'News sentiment analysis',
        'Options Greeks calculator',
        'NIFTY analysis',
        'BANKNIFTY scanner',
        'trading analytics India',
        'Watchman AI',
        'Options analysis India',
    ],
    openGraph: {
        title: 'Stocxer AI - India\'s First ICT + AI Market Analysis Platform',
        description: 'ICT + ML + Sentiment analysis combined. No other Indian platform offers this.',
        type: 'website',
        locale: 'en_IN',
        siteName: 'Stocxer AI',
    },
    twitter: {
        card: 'summary_large_image',
        title: 'Stocxer AI - India\'s First ICT + AI Platform',
        description: 'Smart Money Concepts + Machine Learning + News Sentiment Analysis',
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

            {/* What Makes Us Different - 6 Differentiator Cards */}
            <FeaturesSection />

            {/* How It Works - 3 Steps */}
            <section id="how-it-works">
                <HowItWorksSection />
            </section>

            {/* Competitor Comparison Table */}
            <CompetitorComparison />

            {/* Watchman AI v3.5 Spotlight - 6 Features */}
            <WatchmanAISection />

            {/* Analysis Features Detail - ICT + Options + Sentiment */}
            <AnalysisFeaturesDetail />

            {/* AI Integration - Talk to Your Trading Account */}
            <AIIntegrationSection />

            {/* Pricing Section */}
            <section id="pricing">
                <PricingSection />
            </section>

            {/* FAQ Section */}
            <FAQSection />

            {/* Legal Disclaimer */}
            <DisclaimerSection />

            {/* Footer */}
            <FooterSection />
        </main>
    )
}
