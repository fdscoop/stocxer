'use client'

import React from 'react'
import { MessageCircle, Brain, TrendingUp, ChevronRight } from 'lucide-react'
import Link from 'next/link'

export default function AIIntegrationSection() {
  return (
    <section className="py-24 px-4 bg-gradient-to-b from-[#0a0a0f] to-[#1a1a2e]">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full mb-6">
            <Brain className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-medium text-blue-400">NEW FEATURE</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Talk to Your Trading Account
          </h2>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Connect Stocxer to Claude, Cursor, or Windsurf. 
            Get market analysis and portfolio insights through simple conversation.
          </p>
        </div>

        {/* Visual Demo */}
        <div className="max-w-4xl mx-auto mb-16">
          <div className="bg-[#1a1a2e] border border-gray-800 rounded-2xl p-8 shadow-2xl">
            {/* Chat Interface Mockup */}
            <div className="space-y-6">
              {/* User Message */}
              <div className="flex justify-end">
                <div className="bg-blue-600 text-white px-6 py-3 rounded-2xl rounded-tr-sm max-w-md">
                  <p className="text-sm">What are my current positions?</p>
                </div>
              </div>
              
              {/* AI Response */}
              <div className="flex justify-start">
                <div className="bg-gray-800 text-gray-200 px-6 py-4 rounded-2xl rounded-tl-sm max-w-md">
                  <p className="text-sm mb-2">You have 2 open positions:</p>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between items-center bg-green-500/10 px-3 py-2 rounded">
                      <span>NIFTY 24000 CE</span>
                      <span className="text-green-400">+₹3,250</span>
                    </div>
                    <div className="flex justify-between items-center bg-red-500/10 px-3 py-2 rounded">
                      <span>BANKNIFTY 51000 PE</span>
                      <span className="text-red-400">-₹1,180</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* User Message */}
              <div className="flex justify-end">
                <div className="bg-blue-600 text-white px-6 py-3 rounded-2xl rounded-tr-sm max-w-md">
                  <p className="text-sm">Should I buy RELIANCE today?</p>
                </div>
              </div>

              {/* AI Response */}
              <div className="flex justify-start">
                <div className="bg-gray-800 text-gray-200 px-6 py-4 rounded-2xl rounded-tl-sm max-w-md">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-4 h-4 text-green-400" />
                    <p className="text-sm font-semibold text-green-400">BUY Signal</p>
                  </div>
                  <p className="text-sm mb-2">RELIANCE shows bullish momentum:</p>
                  <ul className="text-sm space-y-1 text-gray-300">
                    <li>• Entry: ₹2,845</li>
                    <li>• Target: ₹2,920</li>
                    <li>• Stop Loss: ₹2,810</li>
                    <li>• Confidence: 78%</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Benefits Grid */}
        <div className="grid md:grid-cols-3 gap-8 mb-12">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <MessageCircle className="w-8 h-8 text-blue-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Natural Conversation
            </h3>
            <p className="text-gray-400">
              No complex dashboards. Just ask questions like you would to a friend.
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-purple-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Brain className="w-8 h-8 text-purple-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Smart Insights
            </h3>
            <p className="text-gray-400">
              AI understands context and provides actionable trading recommendations.
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-green-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <TrendingUp className="w-8 h-8 text-green-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Real-Time Data
            </h3>
            <p className="text-gray-400">
              Live portfolio updates and market analysis powered by Stocxer.
            </p>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <Link href="/mcp">
            <button className="group inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-full transition-all shadow-lg hover:shadow-xl">
              <span>Set Up AI Integration</span>
              <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </Link>
          <p className="text-sm text-gray-500 mt-4">
            Works with Claude Desktop, Cursor IDE, and Windsurf • Free to use
          </p>
        </div>
      </div>
    </section>
  )
}
