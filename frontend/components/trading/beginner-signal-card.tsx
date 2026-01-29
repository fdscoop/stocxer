import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { translateToBeginnerTerms, getConfidenceColor } from '@/lib/beginner-translate'

interface BeginnerSignalCardProps {
    signal: any
}

export function BeginnerSignalCard({ signal }: BeginnerSignalCardProps) {
    const simple = translateToBeginnerTerms(signal)

    return (
        <div className="space-y-4">
            {/* Market Trend */}
            <Card className="border-gray-700">
                <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-gray-400">📊 Market Trend</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                    <div className="flex items-center gap-2">
                        <span className="text-3xl">{simple.trend.emoji}</span>
                        <span className={`text-xl font-bold ${simple.trend.directionRaw === 'bullish' ? 'text-green-400' :
                                simple.trend.directionRaw === 'bearish' ? 'text-red-400' : 'text-yellow-400'
                            }`}>
                            {simple.trend.direction}
                        </span>
                    </div>
                    <div className="flex gap-2">
                        <Badge className={`text-xs px-2 py-0.5 bg-${simple.trend.strength.color}-900 text-${simple.trend.strength.color}-400`}>
                            {simple.trend.strength.emoji} {simple.trend.strength.text}
                        </Badge>
                        <Badge className={`text-xs px-2 py-0.5 bg-${simple.trend.quality.color}-900 text-${simple.trend.quality.color}-400`}>
                            {simple.trend.quality.stars} {simple.trend.quality.text}
                        </Badge>
                    </div>
                </CardContent>
            </Card>

            {/* Entry Timing */}
            <Card className="border-gray-700">
                <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-gray-400">⏰ Entry Timing</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className={`text-base font-semibold text-${simple.entryTiming.color}-400`}>
                        {simple.entryTiming.message}
                    </div>
                    <div className="text-sm text-gray-400 mt-1">
                        {simple.entryTiming.details}
                    </div>
                </CardContent>
            </Card>

            {/* Mixed Signals Warning */}
            {simple.conflicts && simple.conflicts.length > 0 && (
                <Card className="border-orange-700 bg-orange-900/10">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-orange-400">⚠️ Mixed Signals Detected</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-sm text-orange-300">
                            {simple.conflicts[0].message}
                        </div>
                        <div className="text-xs text-gray-400 mt-2">
                            This reduces our confidence in the signal. Be cautious.
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Recommended Action */}
            <Card className={`border-2 border-${simple.recommendation.color}-500/30 ${simple.recommendation.bgClass}/20`}>
                <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-gray-400">🚦 Recommended Action</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    <div className="flex items-center gap-3">
                        <span className="text-4xl">{simple.recommendation.emoji}</span>
                        <span className={`text-3xl font-black ${simple.recommendation.colorClass}`}>
                            {simple.recommendation.action}
                        </span>
                    </div>

                    <ul className="space-y-1 text-sm text-gray-300">
                        {simple.recommendation.reasons.map((reason, idx) => (
                            <li key={idx}>• {reason}</li>
                        ))}
                    </ul>

                    <div className={`bg-black/30 p-3 rounded-lg text-sm italic text-gray-400 border-l-4 border-${simple.recommendation.color}-500/50`}>
                        "{simple.recommendation.advice}"
                    </div>
                </CardContent>
            </Card>

            {/* Signal Strength */}
            <Card className="border-gray-700">
                <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-gray-400">💪 Signal Strength</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                        <span className={`text-2xl font-black ${getConfidenceColor(simple.confidenceScore).text}`}>
                            {Math.round(simple.confidenceScore)}%
                        </span>
                        <Badge variant="outline" className="text-xs">
                            {simple.confidenceLevel}
                        </Badge>
                    </div>

                    <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                        <div
                            className={`h-3 transition-all duration-1000 ${getConfidenceColor(simple.confidenceScore).bg}`}
                            style={{ width: `${simple.confidenceScore}%` }}
                        />
                    </div>

                    <div className="text-xs text-gray-400">
                        {simple.confidenceScore >= 80 && '🔥 Very strong signal - high probability'}
                        {simple.confidenceScore >= 60 && simple.confidenceScore < 80 && '👍 Good signal - decent probability'}
                        {simple.confidenceScore >= 40 && simple.confidenceScore < 60 && '⚠️ Moderate signal - proceed with caution'}
                        {simple.confidenceScore < 40 && '❌ Weak signal - better to wait'}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
