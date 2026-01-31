"use client";

import React from 'react';
import { Avatar } from '@/components/ui/avatar';
import { Card } from '@/components/ui/card';
import { Bot, User } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Citation {
  text: string;
  source: string;
  timestamp?: string;
}

export interface MessageProps {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: Citation[];
  isLoading?: boolean;
}

export function ChatMessage({ role, content, timestamp, citations, isLoading }: MessageProps) {
  const isUser = role === 'user';

  return (
    <div className={cn(
      "flex gap-3 mb-4",
      isUser ? "justify-end" : "justify-start"
    )}>
      {!isUser && (
        <Avatar className="w-8 h-8 bg-blue-500 flex items-center justify-center">
          <Bot className="w-5 h-5 text-white" />
        </Avatar>
      )}
      
      <div className={cn(
        "flex flex-col max-w-[80%]",
        isUser ? "items-end" : "items-start"
      )}>
        <Card className={cn(
          "px-4 py-3 shadow-sm",
          isUser 
            ? "bg-blue-600 text-white border-blue-600" 
            : "bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700"
        )}>
          {isLoading ? (
            <div className="flex items-center gap-2">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              </div>
              <span className="text-sm text-gray-500">Analyzing...</span>
            </div>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <p className="m-0 whitespace-pre-wrap">{content}</p>
            </div>
          )}
        </Card>

        {citations && citations.length > 0 && (
          <div className="mt-2 space-y-1">
            {citations.map((citation, idx) => (
              <div 
                key={idx}
                className="text-xs text-gray-500 dark:text-gray-400 flex items-start gap-2"
              >
                <span className="font-mono text-blue-600 dark:text-blue-400">[{idx + 1}]</span>
                <span>{citation.source}</span>
              </div>
            ))}
          </div>
        )}

        <span className="text-xs text-gray-400 mt-1">
          {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      {isUser && (
        <Avatar className="w-8 h-8 bg-gray-600 flex items-center justify-center">
          <User className="w-5 h-5 text-white" />
        </Avatar>
      )}
    </div>
  );
}
