import type { Metadata } from 'next'
import { BookOpen, Search } from 'lucide-react'

export const metadata: Metadata = {
  title: 'AI Stock Trading Blog - Free Stock Analysis Tips & Tutorials',
  description: 'Read expert articles about free AI tools for stock market analysis, options trading, NIFTY BANKNIFTY screeners, and AI-powered trading strategies in India.',
  keywords: [
    'stock trading blog',
    'AI stock analysis',
    'free AI tool articles',
    'NIFTY BANKNIFTY tips',
    'options trading guide',
    'stock market tutorials',
    'AI screener guide',
    'trading strategies',
  ],
}

export default function BlogPage() {
  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      {/* Header */}
      <section className="py-16 px-4 bg-gradient-to-b from-[#1a1a2e] to-[#0a0a0f]">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full mb-6">
            <BookOpen className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-medium text-blue-400">BLOG</span>
          </div>
          <h1 className="text-5xl font-bold text-white mb-6">
            Trading Insights & AI Market Analysis
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Learn how to use free AI tools for stock analysis, master trading strategies, and understand market signals with expert articles.
          </p>

          {/* Search Bar */}
          <div className="mt-8 flex items-center gap-3 bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 max-w-md mx-auto">
            <Search className="w-5 h-5 text-gray-500" />
            <input
              type="text"
              placeholder="Search articles..."
              className="flex-1 bg-transparent text-white placeholder-gray-500 outline-none"
            />
          </div>
        </div>
      </section>

      {/* Coming Soon Message */}
      <section className="py-24 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gradient-to-br from-blue-900/20 to-blue-800/10 border border-blue-500/30 rounded-2xl p-12">
            <h2 className="text-3xl font-bold text-white mb-4">Blog Coming Soon</h2>
            <p className="text-gray-400 text-lg mb-6">
              We're preparing comprehensive articles on AI stock analysis, free trading tools, and market insights. Check back soon for expert trading tips and strategies.
            </p>
            <ul className="text-left max-w-md mx-auto space-y-3 text-gray-300 mb-8">
              <li className="flex items-center gap-3">
                <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                How to use free AI tools for stock analysis
              </li>
              <li className="flex items-center gap-3">
                <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                Best practices for NIFTY and BANKNIFTY trading
              </li>
              <li className="flex items-center gap-3">
                <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                Options Greek simplified with AI explanations
              </li>
              <li className="flex items-center gap-3">
                <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                Stock screener comparison and reviews
              </li>
            </ul>
          </div>
        </div>
      </section>
    </main>
  )
}
