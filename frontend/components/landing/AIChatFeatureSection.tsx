'use client'

import React from 'react'
import { MessageSquare, Zap, BarChart3, Shield, TrendingUp, ChevronRight } from 'lucide-react'
import Link from 'next/link'

export default function AIChatFeatureSection() {
  return (
    <section className="py-24 px-4 bg-[#0a0a0f] border-t border-gray-800">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full mb-6">
            <MessageSquare className="w-4 h-4 text-emerald-400" />
            <span className="text-sm font-medium text-emerald-400">POWERED BY WATCHMAN AI V3.5</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Chat with AI About Market Signals
          </h2>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Get instant explanations of trading signals, analyze market patterns, and learn trading concepts through real-time conversation.
          </p>
        </div>

        {/* Feature Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          {/* Feature 1 */}
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 rounded-xl p-6 hover:border-emerald-500/30 transition-all group">
            <div className="w-12 h-12 bg-emerald-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-emerald-500/20 transition-all">
              <MessageSquare className="w-6 h-6 text-emerald-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Ask About Signals</h3>
            <p className="text-gray-400 text-sm">
              Understand why the AI generated a BUY/SELL signal, what probability means, and what your targets and stop-losses are.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 rounded-xl p-6 hover:border-emerald-500/30 transition-all group">
            <div className="w-12 h-12 bg-emerald-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-emerald-500/20 transition-all">
              <TrendingUp className="w-6 h-6 text-emerald-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Market Analysis</h3>
            <p className="text-gray-400 text-sm">
              Ask for analysis of specific stocks, indices, or compare different signals to make informed decisions.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 rounded-xl p-6 hover:border-emerald-500/30 transition-all group">
            <div className="w-12 h-12 bg-emerald-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-emerald-500/20 transition-all">
              <Zap className="w-6 h-6 text-emerald-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Quick Explanations</h3>
            <p className="text-gray-400 text-sm">
              Get instant answers about technical indicators, ICT concepts, and trading terminology in simple language.
            </p>
          </div>

          {/* Feature 4 */}
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 rounded-xl p-6 hover:border-emerald-500/30 transition-all group">
            <div className="w-12 h-12 bg-emerald-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-emerald-500/20 transition-all">
              <BarChart3 className="w-6 h-6 text-emerald-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Compare Analysis</h3>
            <p className="text-gray-400 text-sm">
              Compare signals across different indices, understand scan types, and analyze scan results in real-time.
            </p>
          </div>

          {/* Feature 5 */}
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 rounded-xl p-6 hover:border-emerald-500/30 transition-all group">
            <div className="w-12 h-12 bg-emerald-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-emerald-500/20 transition-all">
              <Shield className="w-6 h-6 text-emerald-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Educational Content</h3>
            <p className="text-gray-400 text-sm">
              Learn about market concepts, trading strategies, and risk management with AI-powered explanations.
            </p>
          </div>

          {/* Feature 6 */}
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 rounded-xl p-6 hover:border-emerald-500/30 transition-all group">
            <div className="w-12 h-12 bg-emerald-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-emerald-500/20 transition-all">
              <MessageSquare className="w-6 h-6 text-emerald-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Save Chat History</h3>
            <p className="text-gray-400 text-sm">
              Keep your conversations organized with automatic chat history and easy-to-find previous discussions.
            </p>
          </div>
        </div>

        {/* Scan Types Comparison */}
        <div className="mb-16">
          <h3 className="text-2xl font-bold text-white mb-8 text-center">
            Understanding Scan Types
          </h3>
          <div className="grid md:grid-cols-2 gap-8">
            {/* Quick Scan */}
            <div className="bg-gradient-to-br from-blue-900/20 to-blue-800/10 border border-blue-500/30 rounded-xl p-8">
              <div className="flex items-center gap-3 mb-4">
                <Zap className="w-6 h-6 text-blue-400" />
                <h4 className="text-xl font-bold text-white">Quick Scan</h4>
              </div>
              <p className="text-gray-300 mb-6">
                Fast analysis for quick decision-making with the latest 5-minute candle data.
              </p>
              <ul className="space-y-3 text-sm text-gray-300">
                <li className="flex items-start gap-3">
                  <span className="text-blue-400 mt-1">✓</span>
                  <span>Based on latest 5-minute candle</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-400 mt-1">✓</span>
                  <span>Quick decision signals</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-400 mt-1">✓</span>
                  <span>Ideal for intraday trading</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-400 mt-1">✓</span>
                  <span>Lower analysis time</span>
                </li>
              </ul>
            </div>

            {/* Full Scan */}
            <div className="bg-gradient-to-br from-purple-900/20 to-purple-800/10 border border-purple-500/30 rounded-xl p-8">
              <div className="flex items-center gap-3 mb-4">
                <BarChart3 className="w-6 h-6 text-purple-400" />
                <h4 className="text-xl font-bold text-white">Full Scan</h4>
              </div>
              <p className="text-gray-300 mb-6">
                Comprehensive analysis across multiple timeframes for thorough market assessment.
              </p>
              <ul className="space-y-3 text-sm text-gray-300">
                <li className="flex items-start gap-3">
                  <span className="text-purple-400 mt-1">✓</span>
                  <span>Multi-timeframe analysis</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-purple-400 mt-1">✓</span>
                  <span>ICT Order Block detection</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-purple-400 mt-1">✓</span>
                  <span>Market sentiment analysis</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-purple-400 mt-1">✓</span>
                  <span>Complete signal details</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Pricing Section */}
        <div className="bg-gradient-to-r from-emerald-900/20 to-green-900/20 border border-emerald-500/30 rounded-2xl p-8 mb-12">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h3 className="text-2xl font-bold text-white mb-4">
                Affordable AI Chat Pricing
              </h3>
              <p className="text-gray-300 mb-6">
                Start with 100 free credits on signup. Each chat response costs ₹0.20 (~500 chats per 100 credits). Upgrade anytime for unlimited access.
              </p>
              <ul className="space-y-3 text-sm">
                <li className="flex items-center gap-3 text-gray-300">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full"></span>
                  Pay As You Go: ₹0.20 per chat message
                </li>
                <li className="flex items-center gap-3 text-gray-300">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full"></span>
                  Medium Plan: ₹4,999/month - Unlimited chat
                </li>
                <li className="flex items-center gap-3 text-gray-300">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full"></span>
                  Pro Plan: ₹9,999/month - Unlimited chat + priority support
                </li>
              </ul>
            </div>
            <div className="bg-[#1a1a2e] border border-gray-700 rounded-xl p-8">
              <h4 className="text-lg font-semibold text-white mb-6">
                What You Get Per Response:
              </h4>
              <div className="space-y-4">
                <div className="flex justify-between items-center pb-4 border-b border-gray-700">
                  <span className="text-gray-300">Clear explanation</span>
                  <span className="text-emerald-400">✓</span>
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-gray-700">
                  <span className="text-gray-300">Signal insights</span>
                  <span className="text-emerald-400">✓</span>
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-gray-700">
                  <span className="text-gray-300">Market analysis</span>
                  <span className="text-emerald-400">✓</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Saved in chat history</span>
                  <span className="text-emerald-400">✓</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <Link href="/login">
            <button className="group inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-700 hover:to-green-700 text-white font-semibold rounded-full transition-all shadow-lg hover:shadow-xl">
              <span>Start Chat for Free</span>
              <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </Link>
          <p className="text-sm text-gray-500 mt-4">
            100 free credits included • No card required
          </p>
        </div>
      </div>
    </section>
  )
}
