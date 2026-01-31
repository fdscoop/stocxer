import type { Metadata } from 'next'
import RegulatoryBanner from '@/components/landing/RegulatoryBanner'
import HeroSection from '@/components/landing/HeroSection'
import FeaturesSection from '@/components/landing/FeaturesSection'
import HowItWorksSection from '@/components/landing/HowItWorksSection'
import CompetitorComparison from '@/components/landing/CompetitorComparison'
import WatchmanAISection from '@/components/landing/WatchmanAISection'
import AnalysisFeaturesDetail from '@/components/landing/AnalysisFeaturesDetail'
import AIIntegrationSection from '@/components/landing/AIIntegrationSection'
import AIChatFeatureSection from '@/components/landing/AIChatFeatureSection'
import PricingSection from '@/components/landing/PricingSection'
import FAQSection from '@/components/landing/FAQSection'
import DisclaimerSection from '@/components/landing/DisclaimerSection'
import FooterSection from '@/components/landing/FooterSection'

export const metadata: Metadata = {
    title: 'Best Stock Screener & Options Scanner India - AI Analysis Tool | Stocxer AI',
    description: 'Best AI stock screener & options scanner in India for analytical & research purposes. Advanced market data analysis with stock screener, options screener, NIFTY scanner, BANKNIFTY scanner. ICT Smart Money Concepts, ML models, News Sentiment & Options Greeks.',
    keywords: [
        'best stock screener India',
        'options screener India',
        'stock scanner India',
        'options scanner India',
        'NIFTY screener',
        'BANKNIFTY screener',
        'market scanner India',
        'stock filter tool India',
        'options filter India',
        'best stock analysis tool India',
        'AI stock analysis software',
        'stock market analysis tool',
        'equity screener India',
        'derivatives screener',
        'stock monitoring tool',
        'options monitoring tool',
        'market data screener',
        'technical screener India',
        'automated stock screener',
        'AI stock scanner',
        'stock analysis platform India',
        'AI market analysis India',
        'option analysis tool India',
        'stock research tool India',
        'options research tool',
        'stock tracking tool',
        'ICT analysis India',
        'Smart Money Concepts',
        'ML market analysis',
        'News sentiment analysis',
        'Options Greeks calculator',
        'Watchman AI',
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

            {/* AI Chat Feature - In-App Conversation */}
            <AIChatFeatureSection />

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
