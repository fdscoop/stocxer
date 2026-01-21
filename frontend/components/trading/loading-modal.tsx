'use client'

import * as React from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Progress } from '@/components/ui/progress'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface LoadingStep {
  id: string
  label: string
  status: 'pending' | 'loading' | 'complete' | 'error'
}

interface LoadingModalProps {
  open: boolean
  title: string
  steps: LoadingStep[]
  progress: number
}

export function LoadingModal({ open, title, steps, progress }: LoadingModalProps) {
  return (
    <Dialog open={open}>
      <DialogContent className="sm:max-w-md" onPointerDownOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin" />
            {title}
          </DialogTitle>
          <DialogDescription>
            Processing your request. Please wait...
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-4">
          {steps.map((step) => (
            <div key={step.id} className="flex items-center gap-3">
              <div
                className={cn('w-4 h-4 rounded-full flex items-center justify-center', {
                  'bg-muted': step.status === 'pending',
                  'bg-primary animate-pulse': step.status === 'loading',
                  'bg-bullish': step.status === 'complete',
                  'bg-bearish': step.status === 'error',
                })}
              >
                {step.status === 'complete' && (
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                )}
                {step.status === 'loading' && (
                  <div className="w-2 h-2 bg-white rounded-full" />
                )}
              </div>
              <span
                className={cn('text-sm', {
                  'text-muted-foreground': step.status === 'pending',
                  'text-foreground': step.status === 'loading',
                  'text-bullish': step.status === 'complete',
                  'text-bearish': step.status === 'error',
                })}
              >
                {step.label}
              </span>
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <Progress value={progress} className="h-2" />
          <div className="text-center text-sm text-muted-foreground">{progress}%</div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
