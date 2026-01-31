'use client'

import React from 'react'
import { BookOpen, ArrowRight } from 'lucide-react'
import Link from 'next/link'

interface BlogPost {
  id: string
  title: string
  excerpt: string
  category: string
  readTime: string
  date: string
  slug: string
  keywords: string[]
}

const blogPosts: BlogPost[] = [
  {
    id: '1',
    title: 'Best Free AI Tool for Stock Market Analysis in India 2026',
    excerpt: 'Discover how to use free AI tools for stock analysis. Learn about the best AI stock screeners available in India without spending a rupee.',
    category: 'AI Tools',
    readTime: '8 min read',
    date: 'Jan 31, 2026',
    slug: 'best-free-ai-stock-analysis-tool',
    keywords: ['free AI tool', 'stock analysis', 'AI screener', 'India'],
  },
  {
    id: '2',
    title: 'AI Stock Screener vs Traditional Analysis: Which is Better?',
    excerpt: 'Compare AI-powered stock screening with traditional technical analysis. See why artificial intelligence is revolutionizing stock market research in India.',
    category: 'Market Analysis',
    readTime: '10 min read',
    date: 'Jan 28, 2026',
    slug: 'ai-stock-screener-vs-traditional',
    keywords: ['AI analysis', 'stock screener', 'technical analysis', 'market research'],
  },
  {
    id: '3',
    title: 'How AI Chat Helps Traders Understand Market Signals',
    excerpt: 'Learn how conversational AI can explain complex trading signals in simple language. Get insights on using AI chat for better trading decisions.',
    category: 'Trading Tips',
    readTime: '7 min read',
    date: 'Jan 25, 2026',
    slug: 'ai-chat-trading-signals',
    keywords: ['AI chat', 'trading signals', 'market signals', 'explanation'],
  },
  {
    id: '4',
    title: 'NIFTY and BANKNIFTY Analysis: Using AI Screeners for Better Trades',
    excerpt: 'Master NIFTY and BANKNIFTY trading with AI-powered screeners. Learn how smart money concepts and AI can improve your options trading.',
    category: 'Index Trading',
    readTime: '9 min read',
    date: 'Jan 22, 2026',
    slug: 'nifty-banknifty-ai-analysis',
    keywords: ['NIFTY', 'BANKNIFTY', 'AI screener', 'options trading'],
  },
  {
    id: '5',
    title: 'Free Stock Screener Features: What to Look for in 2026',
    excerpt: 'Complete guide to choosing the best free stock screener. Find out what features matter most for Indian stock market analysis.',
    category: 'Tools & Resources',
    readTime: '6 min read',
    date: 'Jan 20, 2026',
    slug: 'free-stock-screener-features',
    keywords: ['free screener', 'stock screening', 'features', 'comparison'],
  },
  {
    id: '6',
    title: 'Options Greeks Made Simple: AI-Powered Explanation',
    excerpt: 'Understand options Greeks without complex math. See how AI can simplify options analysis for Indian traders.',
    category: 'Options Trading',
    readTime: '8 min read',
    date: 'Jan 18, 2026',
    slug: 'options-greeks-ai-simplified',
    keywords: ['options', 'Greeks', 'AI explanation', 'options trading'],
  },
]

export default function BlogSection() {
  return (
    <section className="py-24 px-4 bg-[#0a0a0f] border-t border-gray-800">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full mb-6">
            <BookOpen className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-medium text-blue-400">TRADING INSIGHTS</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Learn AI-Powered Trading
          </h2>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Discover how to use free AI tools, understand market signals, and master trading with artificial intelligence.
          </p>
        </div>

        {/* Blog Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
          {blogPosts.map((post) => (
            <article
              key={post.id}
              className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 rounded-xl p-6 hover:border-blue-500/30 transition-all group flex flex-col"
            >
              {/* Category Badge */}
              <div className="mb-4">
                <span className="inline-block px-3 py-1 text-xs font-medium text-blue-400 bg-blue-500/10 rounded-full">
                  {post.category}
                </span>
              </div>

              {/* Title */}
              <h3 className="text-lg font-bold text-white mb-3 group-hover:text-blue-400 transition-colors line-clamp-2">
                {post.title}
              </h3>

              {/* Excerpt */}
              <p className="text-gray-400 text-sm mb-6 flex-grow line-clamp-3">
                {post.excerpt}
              </p>

              {/* Meta Info */}
              <div className="flex items-center justify-between mb-4 text-xs text-gray-500">
                <span>{post.date}</span>
                <span>{post.readTime}</span>
              </div>

              {/* Read More Link */}
              <Link
                href={`/blog/${post.slug}`}
                className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 font-medium group/link transition-colors"
              >
                Read Article
                <ArrowRight className="w-4 h-4 group-hover/link:translate-x-1 transition-transform" />
              </Link>

              {/* Keywords for SEO */}
              <div className="mt-4 pt-4 border-t border-gray-700 hidden">
                <p className="text-xs text-gray-500">
                  {post.keywords.join(', ')}
                </p>
              </div>
            </article>
          ))}
        </div>

        {/* View All Articles CTA */}
        <div className="text-center">
          <Link href="/blog">
            <button className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-full transition-all shadow-lg hover:shadow-xl">
              <span>View All Articles</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </Link>
        </div>
      </div>
    </section>
  )
}
