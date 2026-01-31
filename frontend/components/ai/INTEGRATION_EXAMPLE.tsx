/**
 * Example: Integrating AI Chat into Options Scanner Page
 * 
 * This demonstrates how to add the AI Chat functionality to your existing pages.
 */

import { useState, useEffect } from 'react';
import { HybridDashboardLayout } from '@/components/ai';
import { QuickActionsCompact } from '@/components/ai/QuickActionsBar';

interface AIInsight {
  type: 'summary' | 'warning' | 'risk' | 'opportunity';
  title: string;
  content: string;
  confidence: number;
}

export default function OptionsPageWithAI() {
  const [scanResults, setScanResults] = useState<any>(null);
  const [aiInsights, setAiInsights] = useState<AIInsight[]>([]);

  // When scan completes, generate AI insights
  useEffect(() => {
    if (scanResults) {
      generateAIInsights(scanResults);
    }
  }, [scanResults]);

  const generateAIInsights = async (results: any) => {
    // Auto-generate insights from scan results
    const insights: AIInsight[] = [];

    if (results.confidence > 70) {
      insights.push({
        type: 'opportunity' as const,
        title: 'High Confidence Signal Detected',
        content: `${results.signal} shows ${results.confidence}% confidence. Strong setup detected.`,
        confidence: results.confidence / 100
      });
    }

    if (results.risk_reward_ratio_1 && parseFloat(results.risk_reward_ratio_1.split(':')[0]) > 2) {
      insights.push({
        type: 'summary' as const,
        title: 'Favorable Risk/Reward',
        content: `Risk-to-reward ratio of ${results.risk_reward_ratio_1} offers excellent potential upside.`,
        confidence: 0.85
      });
    }

    if (results.vix && results.vix > 20) {
      insights.push({
        type: 'warning' as const,
        title: 'Elevated Volatility',
        content: `VIX at ${results.vix} indicates higher market uncertainty. Consider position sizing.`,
        confidence: 0.9
      });
    }

    setAiInsights(insights);
  };

  return (
    <HybridDashboardLayout
      signalData={scanResults}
      scanId={scanResults?.id}
      aiInsights={aiInsights}
      defaultMode="hybrid"
    >
      {/* Your existing dashboard content */}
      <div className="space-y-6">
        {/* Signal Cards with Quick Actions */}
        {scanResults && (
          <div className="p-4 border rounded-lg">
            <h3>{scanResults.signal}</h3>
            <p>Entry: ₹{scanResults.entry_price}</p>
            
            {/* Add Quick AI Actions to each card */}
            <div className="mt-4 pt-4 border-t">
              <QuickActionsCompact
                onActionClick={(prompt) => {
                  // This will open the chat sidebar with the prompt
                  console.log('AI Action:', prompt);
                }}
              />
            </div>
          </div>
        )}
      </div>
    </HybridDashboardLayout>
  );
}

/**
 * Alternative: Simple Chat Sidebar Addition
 * 
 * If you don't want the full hybrid layout, just add the chat sidebar:
 */

import { ChatSidebar } from '@/components/ai/ChatSidebar';
import { useAIChat } from '@/lib/hooks/useAIChat';
import { Button } from '@/components/ui/button';
import { MessageSquare } from 'lucide-react';

export function SimpleAIChatIntegration() {
  const [scanData] = useState<any>(null); // Replace with your actual state
  const [isChatOpen, setIsChatOpen] = useState(false);
  const { messages, isLoading, sendMessage } = useAIChat({
    signalData: scanData,
    scanId: scanData?.id
  });

  return (
    <>
      {/* Your existing page content */}
      <div>
        <h1>Your Dashboard</h1>
        
        {/* Floating button to open chat */}
        <Button onClick={() => setIsChatOpen(true)}>
          <MessageSquare className="w-4 h-4 mr-2" />
          Ask AI
        </Button>
      </div>

      {/* Chat Sidebar */}
      <ChatSidebar
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        onSendMessage={sendMessage}
        messages={messages}
        isLoading={isLoading}
        signalContext={scanData}
      />
    </>
  );
}
