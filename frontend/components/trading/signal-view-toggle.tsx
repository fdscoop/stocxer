import React from 'react'
import { Button } from '@/components/ui/button'

interface SignalViewToggleProps {
    viewMode: 'beginner' | 'advanced'
    onViewChange: (mode: 'beginner' | 'advanced') => void
}

export function SignalViewToggle({ viewMode, onViewChange }: SignalViewToggleProps) {
    return (
        <div className="flex border-b border-gray-700">
            <Button
                variant="ghost"
                className={`flex-1 py-2 text-sm font-medium rounded-none border-b-2 ${viewMode === 'beginner'
                        ? 'border-blue-500 text-white'
                        : 'border-transparent text-gray-400 hover:text-gray-200'
                    }`}
                onClick={() => onViewChange('beginner')}
            >
                👶 Simpler View
            </Button>
            <Button
                variant="ghost"
                className={`flex-1 py-2 text-sm font-medium rounded-none border-b-2 ${viewMode === 'advanced'
                        ? 'border-blue-500 text-white'
                        : 'border-transparent text-gray-400 hover:text-gray-200'
                    }`}
                onClick={() => onViewChange('advanced')}
            >
                🔬 Advanced View
            </Button>
        </div>
    )
}
