import type { Metadata } from 'next'
import RegulatoryBanner from '@/components/landing/RegulatoryBanner'
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
    title: 'Best Stock Analysis Tool India - AI-Powered Market Analysis | Stocxer AI',
    description: 'Best AI stock analysis software in India for analytical & research purposes. Advanced market data analysis tool with ICT Smart Money Concepts, ML models, News Sentiment & Options Greeks. Automated stock screener for NIFTY & BANKNIFTY.',
    keywords: [
        'best stock analysis tool India',
        'AI stock analysis software',
        'stock market analysis tool',
        'best trading analysis software India',
        'AI market analysis India',
        'automated stock analysis',
        'stock analysis platform India',
        'AI trading analytics',
        'stock screener India',
        'option analysis tool India',
        'NIFTY analysis tool',
        'BANKNIFTY analysis software',
        'ICT analysis India',
        'Smart Money Concepts',
        'ML market analysis',
        'News sentiment analysis',
        'Options Greeks calculator',
        'Watchman AI',
        'stock research tool India',
        'technical analysis software India',
    ],
    openGraph: {
        title: 'Stocxer AI - AI-Powered Market Data Analysis Tool',
        description: 'An intuitive AI-based data analysis software for analytical, research, and informational purposes.',
        type: 'website',
        locale: 'en_IN',
        siteName: 'Stocxer AI',
    },
    twitter: {
        card: 'summary_large_image',
        title: 'Stocxer AI - AI-Powered Data Analysis Tool',
        description: 'Intuitive AI-based market data analysis software for research and informational purposes.',
    },
    robots: {
        index: true,
        follow: true,
    },
}

export default function LandingPage() {
    return (
        <main className="min-h-screen bg-[#0a0a0f]">
            {/* Regulatory Banner - SEBI Compliance */}
            <RegulatoryBanner />

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
