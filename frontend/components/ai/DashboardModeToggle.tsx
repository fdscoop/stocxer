"use client";

import React from 'react';
import { Button } from '@/components/ui/button';
import { MessageSquare, LayoutDashboard, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

export type DashboardMode = 'dashboard' | 'chat' | 'hybrid';

interface DashboardModeToggleProps {
  mode: DashboardMode;
  onModeChange: (mode: DashboardMode) => void;
  showHybrid?: boolean;
}

export function DashboardModeToggle({ 
  mode, 
  onModeChange,
  showHybrid = true 
}: DashboardModeToggleProps) {
  return (
    <div className="inline-flex items-center rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 p-1">
      <Button
        variant={mode === 'dashboard' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => onModeChange('dashboard')}
        className={cn(
          "gap-2",
          mode === 'dashboard' && "bg-white dark:bg-gray-900 shadow-sm"
        )}
      >
        <LayoutDashboard className="w-4 h-4" />
        <span className="hidden sm:inline">Dashboard</span>
      </Button>

      {showHybrid && (
        <Button
          variant={mode === 'hybrid' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => onModeChange('hybrid')}
          className={cn(
            "gap-2",
            mode === 'hybrid' && "bg-white dark:bg-gray-900 shadow-sm"
          )}
        >
          <Sparkles className="w-4 h-4" />
          <span className="hidden sm:inline">Hybrid</span>
        </Button>
      )}

      <Button
        variant={mode === 'chat' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => onModeChange('chat')}
        className={cn(
          "gap-2",
          mode === 'chat' && "bg-white dark:bg-gray-900 shadow-sm"
        )}
      >
        <MessageSquare className="w-4 h-4" />
        <span className="hidden sm:inline">AI Chat</span>
        <span className="ml-1 px-1.5 py-0.5 text-[10px] font-bold bg-blue-500 text-white rounded">BETA</span>
      </Button>
    </div>
  );
}
