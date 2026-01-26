import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  metadataBase: new URL('https://stocxer.in'),
  title: {
    default: 'Stocxer AI - AI-Powered Market Data Analysis Tool',
    template: '%s | Stocxer AI'
  },
  description: 'Stocxer AI is an intuitive AI-based data analysis software for analytical, research, and informational purposes. Combines ICT Smart Money Concepts, ML models, and News Sentiment.',
  keywords: ['best stock analysis tool India', 'AI stock analysis software', 'stock market analysis tool', 'best trading analysis software India', 'AI market analysis India', 'stock analysis platform India', 'automated stock analysis', 'AI trading analytics', 'stock screener India', 'option analysis tool India', 'NIFTY analysis tool', 'BANKNIFTY analysis software', 'ICT analysis India', 'Smart Money Concepts', 'Options Greeks calculator', 'Watchman AI', 'market data analysis tool', 'stock research tool India', 'technical analysis software India', 'Indian stock market analysis'],
  authors: [{ name: 'Cadreago De Private Limited' }],
  creator: 'Cadreago De Private Limited',
  publisher: 'Cadreago De Private Limited',
  manifest: '/manifest.json',
  alternates: {
    canonical: 'https://stocxer.in',
  },
  openGraph: {
    type: 'website',
    locale: 'en_IN',
    url: 'https://stocxer.in',
    siteName: 'Stocxer AI',
    title: 'Stocxer AI - AI-Powered Market Data Analysis Tool',
    description: 'AI-based data analysis software for analytical, research, and informational purposes.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Stocxer AI - Market Data Analysis Tool',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Stocxer AI - AI-Powered Market Data Analysis Tool',
    description: 'AI-based data analysis software for analytical, research, and informational purposes.',
    images: ['/twitter-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: 'googlecf62b3df1f840c44',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: '#0a0a0f',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="Stocxer AI" />
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <link rel="apple-touch-icon" href="/icon.svg" />
        <link rel="canonical" href="https://stocxer.in" />
        {/* Preconnect to external domains for better performance */}
        <link rel="preconnect" href="https://stocxer-ai.onrender.com" />
        <link rel="preconnect" href="https://cxbcpmouqkajlxzmbomu.supabase.co" />
        {/* JSON-LD Structured Data */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'SoftwareApplication',
              name: 'Stocxer AI - Best Stock Analysis Tool India',
              applicationCategory: 'FinanceApplication',
              operatingSystem: 'Web',
              offers: {
                '@type': 'Offer',
                price: '0',
                priceCurrency: 'INR',
              },
              aggregateRating: {
                '@type': 'AggregateRating',
                ratingValue: '4.8',
                ratingCount: '150',
              },
              description: 'Best AI stock analysis software in India. Advanced market data analysis tool with Smart Money Concepts, ML models, and News Sentiment for analytical and research purposes.',
              keywords: 'best stock analysis tool India, AI stock analysis software, stock market analysis tool, trading analytics India',
              targetCountry: 'IN',
              inLanguage: 'en-IN',
              publisher: {
                '@type': 'Organization',
                name: 'Cadreago De Private Limited',
                email: 'cadreagode@gmx.com',
              },
              featureList: [
                'ICT Smart Money Concepts',
                'ML-powered market analysis',
                'News sentiment analysis',
                'Options Greeks calculator',
                'Stock screener',
                'NIFTY & BANKNIFTY analysis',
                'Watchman AI v3.5'
              ],
            }),
          }}
        />
      </head>
      <body className={`${inter.className} antialiased min-h-screen safe-area-inset-top safe-area-inset-bottom`}>
        {children}
      </body>
    </html>
  )
}
