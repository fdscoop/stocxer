"use client";

import React, { useState, KeyboardEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  suggestions?: string[];
  placeholder?: string;
}

export function ChatInput({ 
  onSendMessage, 
  disabled = false, 
  suggestions = [],
  placeholder = "Ask about your signals, risk analysis, or trading strategy..."
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
      setShowSuggestions(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    onSendMessage(suggestion);
    setShowSuggestions(false);
    setMessage('');
  };

  const handleClickOutside = () => {
    setShowSuggestions(false);
  };

  return (
    <div className="relative border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
      {showSuggestions && suggestions.length > 0 && (
        <div 
          className="absolute bottom-full left-4 right-4 mb-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden max-h-48 z-40"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="p-2 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between gap-2 sticky top-0 bg-white dark:bg-gray-800">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-500" />
              <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                Quick Questions (Click to use)
              </span>
            </div>
            <button
              onClick={() => setShowSuggestions(false)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 ml-auto flex-shrink-0"
              type="button"
              title="Close suggestions"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="overflow-y-auto max-h-40">
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onMouseDown={(e) => {
                  e.preventDefault();
                  handleSuggestionClick(suggestion);
                }}
                className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors whitespace-normal text-wrap"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Textarea
            value={message}
            onChange={(e) => {
              setMessage(e.target.value);
              setShowSuggestions(false);
            }}
            onKeyDown={handleKeyDown}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 100)}
            placeholder={placeholder}
            disabled={disabled}
            className={cn(
              "min-h-[44px] max-h-32 resize-none",
              "pr-10"
            )}
            rows={1}
          />
          {suggestions.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSuggestions(!showSuggestions)}
              className="absolute right-2 top-2 h-6 w-6 p-0"
              type="button"
              title={showSuggestions ? "Hide suggestions" : "Show suggestions"}
            >
              <Sparkles className="w-4 h-4 text-gray-400" />
            </Button>
          )}
        </div>
        <Button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          className="px-4"
          size="lg"
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>

      <div className="mt-2 text-xs text-gray-500 flex items-center gap-1">
        <Sparkles className="w-3 h-3" />
        <span>AI-powered by Watchman i3.5 • Press Enter to send, Shift+Enter for new line</span>
      </div>
    </div>
  );
}
