"use client";

import React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Sparkles, TrendingUp, TrendingDown, AlertTriangle, Target, ShieldAlert } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AIInsightCardProps {
  type: 'summary' | 'risk' | 'opportunity' | 'warning';
  title: string;
  content: string;
  confidence?: number;
  onExplainMore?: () => void;
  className?: string;
}

const typeConfig = {
  summary: {
    icon: Sparkles,
    color: 'blue',
    bgClass: 'bg-blue-50 dark:bg-blue-900/20',
    borderClass: 'border-blue-200 dark:border-blue-800',
    iconClass: 'text-blue-600 dark:text-blue-400'
  },
  risk: {
    icon: ShieldAlert,
    color: 'red',
    bgClass: 'bg-red-50 dark:bg-red-900/20',
    borderClass: 'border-red-200 dark:border-red-800',
    iconClass: 'text-red-600 dark:text-red-400'
  },
  opportunity: {
    icon: Target,
    color: 'green',
    bgClass: 'bg-green-50 dark:bg-green-900/20',
    borderClass: 'border-green-200 dark:border-green-800',
    iconClass: 'text-green-600 dark:text-green-400'
  },
  warning: {
    icon: AlertTriangle,
    color: 'amber',
    bgClass: 'bg-amber-50 dark:bg-amber-900/20',
    borderClass: 'border-amber-200 dark:border-amber-800',
    iconClass: 'text-amber-600 dark:text-amber-400'
  }
};

export function AIInsightCard({
  type,
  title,
  content,
  confidence,
  onExplainMore,
  className
}: AIInsightCardProps) {
  const config = typeConfig[type];
  const Icon = config.icon;

  return (
    <Card className={cn(
      'p-4 border-l-4',
      config.bgClass,
      config.borderClass,
      className
    )}>
      <div className="flex items-start gap-3">
        <div className={cn(
          'w-10 h-10 rounded-lg flex items-center justify-center shrink-0',
          config.bgClass
        )}>
          <Icon className={cn('w-5 h-5', config.iconClass)} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              {title}
              {confidence && (
                <Badge variant="outline" className="text-xs">
                  {Math.round(confidence * 100)}% confident
                </Badge>
              )}
            </h4>
          </div>

          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
            {content}
          </p>

          {onExplainMore && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onExplainMore}
              className="mt-2 -ml-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
            >
              <Sparkles className="w-3 h-3 mr-1" />
              Ask AI to explain more
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}

interface AIInsightsPanelProps {
  insights: Array<{
    type: 'summary' | 'risk' | 'opportunity' | 'warning';
    title: string;
    content: string;
    confidence?: number;
  }>;
  onExplainMore?: (insight: any) => void;
  isLoading?: boolean;
}

export function AIInsightsPanel({ insights, onExplainMore, isLoading }: AIInsightsPanelProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-4 animate-pulse">
            <div className="flex gap-3">
              <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full" />
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
              </div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  if (insights.length === 0) {
    return (
      <Card className="p-8 text-center">
        <Sparkles className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <p className="text-gray-500 dark:text-gray-400">
          No AI insights available yet. Scan for signals to get started.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {insights.map((insight, idx) => (
        <AIInsightCard
          key={idx}
          {...insight}
          onExplainMore={onExplainMore ? () => onExplainMore(insight) : undefined}
        />
      ))}
    </div>
  );
}
