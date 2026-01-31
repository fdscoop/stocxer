"use client";

import { useState, useCallback } from 'react';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: Array<{
    text: string;
    source: string;
    timestamp?: string;
  }>;
}

export interface ChatResponse {
  response: string;
  citations?: any[];
  cached?: boolean;
  tokens_used?: number;
  confidence_score?: number;
  query_type?: string;
}

interface UseAIChatOptions {
  signalData?: any;
  scanData?: any;
  scanId?: string;
  apiUrl?: string;
}

export function useAIChat(options: UseAIChatOptions = {}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = options.apiUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const sendMessage = useCallback(async (query: string) => {
    // Debug log what data we're sending
    console.log('🤖 AI Chat sending message:', {
      query,
      hasSignalData: !!options.signalData,
      hasScanData: !!options.scanData,
      signalDataPreview: options.signalData ? JSON.stringify(options.signalData).slice(0, 200) : null,
      scanDataPreview: options.scanData ? JSON.stringify(options.scanData).slice(0, 200) : null
    });

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      // Get token - try auth_token first, then access_token, then token
      const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token') || localStorage.getItem('token');
      
      if (!token) {
        console.error('🚫 No auth token found in localStorage');
        throw new Error('Please login to use AI chat');
      }
      
      console.log('🔑 Using token:', token.substring(0, 30) + '...');
      
      const response = await fetch(`${apiUrl}/api/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          query,
          signal_data: options.signalData,
          scan_data: options.scanData,
          scan_id: options.scanId,
          use_cache: true
        })
      });

      if (!response.ok) {
        // Handle 401 Unauthorized - token may be expired
        if (response.status === 401) {
          console.error('🚫 Token expired or invalid. Please login again.');
          // Clear invalid tokens
          localStorage.removeItem('auth_token');
          localStorage.removeItem('token');
          localStorage.removeItem('jwt_token');
          throw new Error('Session expired. Please login again.');
        }
        throw new Error(`API error: ${response.statusText}`);
      }

      const data: ChatResponse = await response.json();

      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        citations: data.citations
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Save to localStorage for persistence
      const history = [...messages, userMessage, assistantMessage];
      localStorage.setItem('ai-chat-history', JSON.stringify(history.slice(-20))); // Keep last 20 messages

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      console.error('AI Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [messages, apiUrl, options.signalData, options.scanData, options.scanId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    localStorage.removeItem('ai-chat-history');
  }, []);

  const loadHistory = useCallback(() => {
    try {
      const stored = localStorage.getItem('ai-chat-history');
      if (stored) {
        setMessages(JSON.parse(stored));
      }
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    loadHistory
  };
}
