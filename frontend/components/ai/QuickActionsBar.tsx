"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { 
  Sparkles, 
  MessageSquare, 
  TrendingUp, 
  Shield,
  Clock,
  Target
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  prompt: string;
  color: string;
}

const defaultActions: QuickAction[] = [
  {
    id: 'explain',
    label: 'Explain Signal',
    icon: <Sparkles className="w-4 h-4" />,
    prompt: 'Explain this signal in simple terms',
    color: 'blue'
  },
  {
    id: 'risk',
    label: 'Risk Analysis',
    icon: <Shield className="w-4 h-4" />,
    prompt: 'What are the risks of this trade?',
    color: 'red'
  },
  {
    id: 'entry',
    label: 'Entry Points',
    icon: <Target className="w-4 h-4" />,
    prompt: 'What are the best entry points?',
    color: 'green'
  },
  {
    id: 'timing',
    label: 'Best Timing',
    icon: <Clock className="w-4 h-4" />,
    prompt: 'When is the best time to enter this trade?',
    color: 'purple'
  },
  {
    id: 'compare',
    label: 'Compare',
    icon: <TrendingUp className="w-4 h-4" />,
    prompt: 'How does this compare to similar signals?',
    color: 'amber'
  },
  {
    id: 'custom',
    label: 'Ask AI',
    icon: <MessageSquare className="w-4 h-4" />,
    prompt: '',
    color: 'gray'
  }
];

interface QuickActionsBarProps {
  onActionClick: (prompt: string) => void;
  actions?: QuickAction[];
  disabled?: boolean;
  compact?: boolean;
}

export function QuickActionsBar({ 
  onActionClick, 
  actions = defaultActions,
  disabled = false,
  compact = false
}: QuickActionsBarProps) {
  const [showAll, setShowAll] = useState(false);
  
  const visibleActions = compact && !showAll ? actions.slice(0, 3) : actions;

  return (
    <div className="space-y-2">
      <div className={cn(
        "flex flex-wrap gap-2",
        compact && "gap-1.5"
      )}>
        {visibleActions.map((action) => (
          <Button
            key={action.id}
            variant="outline"
            size={compact ? "sm" : "default"}
            onClick={() => onActionClick(action.prompt || action.label)}
            disabled={disabled}
            className={cn(
              "gap-2",
              compact && "text-xs px-2 py-1 h-7"
            )}
          >
            {action.icon}
            <span>{action.label}</span>
          </Button>
        ))}
        
        {compact && !showAll && actions.length > 3 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowAll(true)}
            className="text-xs px-2 py-1 h-7"
          >
            +{actions.length - 3} more
          </Button>
        )}
      </div>
    </div>
  );
}

// Compact version for signal cards
export function QuickActionsCompact({ 
  onActionClick,
  disabled = false 
}: { 
  onActionClick: (prompt: string) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      <span className="text-xs text-gray-500 mr-1">Quick AI:</span>
      {defaultActions.slice(0, 3).map((action) => (
        <button
          key={action.id}
          onClick={() => onActionClick(action.prompt)}
          disabled={disabled}
          className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-md bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {action.icon}
          <span className="hidden sm:inline">{action.label}</span>
        </button>
      ))}
    </div>
  );
}
