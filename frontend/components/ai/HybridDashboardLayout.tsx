"use client";

import React, { useState, useEffect } from 'react';
import { ChatSidebar } from './ChatSidebar';
import { DashboardModeToggle, DashboardMode } from './DashboardModeToggle';
import { AIInsightsPanel } from './AIInsightCard';
import { QuickActionsBar } from './QuickActionsBar';
import { useAIChat } from '@/lib/hooks/useAIChat';
import { Button } from '@/components/ui/button';
import { MessageSquare, X, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface HybridDashboardLayoutProps {
  children: React.ReactNode;
  signalData?: any;
  scanData?: any;
  scanId?: string;
  aiInsights?: Array<{
    type: 'summary' | 'risk' | 'opportunity' | 'warning';
    title: string;
    content: string;
    confidence?: number;
  }>;
  showModeToggle?: boolean;
  defaultMode?: DashboardMode;
}

export function HybridDashboardLayout({
  children,
  signalData,
  scanData,
  scanId,
  aiInsights = [],
  showModeToggle = true,
  defaultMode = 'dashboard'
}: HybridDashboardLayoutProps) {
  const [mode, setMode] = useState<DashboardMode>(defaultMode);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [showInsights, setShowInsights] = useState(false);

  const { messages, isLoading, sendMessage, loadHistory } = useAIChat({
    signalData,
    scanData,
    scanId
  });

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    // Auto-open chat in chat mode
    setIsChatOpen(mode === 'chat' || mode === 'hybrid');
    setShowInsights(mode === 'hybrid');
  }, [mode]);

  const handleSendMessage = async (message: string) => {
    await sendMessage(message);
  };

  const handleInsightExplain = (insight: any) => {
    setIsChatOpen(true);
    sendMessage(`Can you explain more about: ${insight.title}? ${insight.content}`);
  };

  return (
    <div className="relative min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header with Mode Toggle */}
      <div className="sticky top-0 z-30 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 py-3">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              Trading Dashboard
            </h1>
            {mode === 'hybrid' && (
              <div className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
                <Sparkles className="w-4 h-4" />
                <span>AI-Powered View</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            {showModeToggle && (
              <DashboardModeToggle mode={mode} onModeChange={setMode} />
            )}
            
            {mode === 'dashboard' && (
              <Button
                onClick={() => setIsChatOpen(true)}
                variant="outline"
                className="gap-2"
              >
                <MessageSquare className="w-4 h-4" />
                <span className="hidden sm:inline">AI Assistant</span>
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className={cn(
        "transition-all duration-300",
        mode === 'hybrid' && "grid grid-cols-1 lg:grid-cols-3 gap-6 p-6"
      )}>
        {/* Dashboard Content */}
        <div className={cn(
          mode === 'hybrid' ? "lg:col-span-2" : "w-full",
          mode === 'chat' && "hidden"
        )}>
          {children}
        </div>

        {/* AI Insights Panel (Hybrid Mode) */}
        {mode === 'hybrid' && showInsights && (
          <div className="lg:col-span-1 space-y-4">
            <div className="sticky top-20">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-blue-500" />
                  AI Insights
                </h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowInsights(false)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>

              <AIInsightsPanel
                insights={aiInsights}
                onExplainMore={handleInsightExplain}
              />

              <div className="mt-4">
                <QuickActionsBar
                  onActionClick={handleSendMessage}
                  disabled={isLoading}
                  compact
                />
              </div>
            </div>
          </div>
        )}

        {/* Full Chat View (Chat Mode) */}
        {mode === 'chat' && (
          <div className="w-full max-w-4xl mx-auto p-6">
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg h-[calc(100vh-200px)] flex flex-col">
              <div className="flex-1 overflow-hidden">
                <ChatSidebar
                  isOpen={true}
                  onClose={() => setMode('dashboard')}
                  onSendMessage={handleSendMessage}
                  messages={messages}
                  isLoading={isLoading}
                  signalContext={signalData}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Floating Chat Sidebar (Dashboard Mode) */}
      {mode === 'dashboard' && (
        <ChatSidebar
          isOpen={isChatOpen}
          onClose={() => setIsChatOpen(false)}
          onSendMessage={handleSendMessage}
          messages={messages}
          isLoading={isLoading}
          signalContext={signalData}
        />
      )}

      {/* Floating Action Button (Mobile) */}
      {mode === 'dashboard' && !isChatOpen && (
        <Button
          onClick={() => setIsChatOpen(true)}
          className="fixed bottom-6 right-6 rounded-full w-14 h-14 shadow-lg lg:hidden z-40"
          size="lg"
        >
          <MessageSquare className="w-6 h-6" />
        </Button>
      )}
    </div>
  );
}
