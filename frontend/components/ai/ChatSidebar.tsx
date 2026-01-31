"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { X, Bot, Trash2, History } from 'lucide-react';
import { ChatMessage, MessageProps } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { cn } from '@/lib/utils';

interface ChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onSendMessage: (message: string) => Promise<void>;
  messages: MessageProps[];
  isLoading: boolean;
  suggestions?: string[];
  signalContext?: any;
}

export function ChatSidebar({
  isOpen,
  onClose,
  onSendMessage,
  messages,
  isLoading,
  suggestions = [],
  signalContext
}: ChatSidebarProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [chatHistory, setChatHistory] = useState<MessageProps[]>(messages);

  useEffect(() => {
    setChatHistory(messages);
  }, [messages]);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory]);

  const handleClearChat = () => {
    if (confirm('Clear chat history?')) {
      setChatHistory([]);
      localStorage.removeItem('ai-chat-history');
    }
  };

  const defaultSuggestions = suggestions.length > 0 ? suggestions : [
    "Explain this signal in simple terms",
    "What's the risk/reward ratio?",
    "Compare with yesterday's signals",
    "What's the best entry point?",
    "Should I take this trade?",
    "What are the key support levels?"
  ];

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        "fixed top-0 right-0 h-full w-full sm:w-96 bg-white dark:bg-gray-900 shadow-2xl z-50 transition-transform duration-300 ease-in-out",
        isOpen ? "translate-x-0" : "translate-x-full"
      )}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  AI Assistant
                  <span className="px-1.5 py-0.5 text-[10px] font-bold bg-blue-500 text-white rounded">BETA</span>
                </h3>
                <p className="text-xs text-gray-500">Powered by Cohere</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearChat}
                className="text-gray-500 hover:text-gray-700"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Context Indicator */}
          {signalContext && (
            <div className="px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border-b border-blue-100 dark:border-blue-800">
              <p className="text-xs text-blue-700 dark:text-blue-300">
                💡 Context: {signalContext.symbol || 'Current Scan'} - {signalContext.signal || 'Analysis Active'}
              </p>
            </div>
          )}

          {/* Messages */}
          <ScrollArea className="flex-1 p-4" ref={scrollRef}>
            {chatHistory.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900/20 dark:to-purple-900/20 rounded-full flex items-center justify-center mb-4">
                  <Bot className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                </div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                  AI Trading Assistant
                </h4>
                <p className="text-sm text-gray-500 mb-6 max-w-xs">
                  Ask me anything about your signals, risk management, or trading strategies
                </p>
                <div className="w-full space-y-2">
                  <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Try asking:
                  </p>
                  {defaultSuggestions.slice(0, 3).map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => onSendMessage(suggestion)}
                      className="w-full text-left p-3 text-sm bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {chatHistory.map((msg) => (
                  <ChatMessage key={msg.id} {...msg} />
                ))}
                {isLoading && (
                  <ChatMessage
                    id="loading"
                    role="assistant"
                    content=""
                    timestamp={new Date().toISOString()}
                    isLoading={true}
                  />
                )}
              </div>
            )}
          </ScrollArea>

          {/* Input */}
          <ChatInput
            onSendMessage={onSendMessage}
            disabled={isLoading}
            suggestions={defaultSuggestions}
          />
        </div>
      </div>
    </>
  );
}
