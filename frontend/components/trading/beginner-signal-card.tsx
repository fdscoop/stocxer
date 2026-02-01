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

            {/* Quick Scalp Targets (Beginner View) */}
            {signal?.scalp_feasibility && signal?.greeks?.delta && (
                <Card className="border-cyan-700/50">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-cyan-400">
                            ⚡ Quick Scalp Targets (Intraday)
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {/* Risk Warning */}
                        <div className="flex items-center gap-2">
                            <Badge
                                variant={
                                    !signal.scalp_feasibility.feasible || signal.scalp_feasibility.risk_level === 'EXTREME'
                                        ? 'destructive'
                                        : signal.scalp_feasibility.risk_level === 'HIGH'
                                        ? 'secondary'
                                        : 'default'
                                }
                                className="text-xs"
                            >
                                {!signal.scalp_feasibility.feasible || signal.scalp_feasibility.risk_level === 'EXTREME'
                                    ? '⛔ HIGH RISK - AVOID'
                                    : signal.scalp_feasibility.risk_level === 'HIGH'
                                    ? '⚠️ RISKY - BE CAREFUL'
                                    : '✅ VIABLE FOR SCALPING'
                                }
                            </Badge>
                        </div>

                        {/* Simple Target Display */}
                        <div className="bg-black/30 p-3 rounded-lg">
                            <div className="grid grid-cols-2 gap-3 text-sm">
                                <div>
                                    <span className="text-green-400">🎯 Quick Targets:</span>
                                    <div className="ml-4 space-y-1 text-xs text-gray-300">
                                        <div>+5 pts: ₹{signal.scalp_feasibility.targets.target_5.toFixed(1)}</div>
                                        <div>+10 pts: ₹{signal.scalp_feasibility.targets.target_10.toFixed(1)}</div>
                                        <div>+15 pts: ₹{signal.scalp_feasibility.targets.target_15.toFixed(1)}</div>
                                    </div>
                                </div>
                                <div>
                                    <span className="text-red-400">🛑 Stop Loss:</span>
                                    <div className="ml-4 text-xs text-red-300">
                                        ₹{signal.scalp_feasibility.targets.stop_loss.toFixed(1)}
                                    </div>
                                    <div className="mt-2">
                                        <span className="text-cyan-400">💰 Per Lot:</span>
                                        <div className="ml-4 text-xs text-cyan-300">
                                            ₹{signal.scalp_feasibility.per_lot_pnl.profit_5} - ₹{signal.scalp_feasibility.per_lot_pnl.profit_15}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Beginner Explanation */}
                        <div className="bg-blue-900/20 p-3 rounded-lg border border-blue-500/30">
                            <div className="text-xs text-blue-300 font-medium mb-1">
                                📚 What are Scalp Targets?
                            </div>
                            <div className="text-xs text-gray-300">
                                These are quick profit targets for very short-term trades (5-30 minutes). 
                                They require constant monitoring and are for experienced traders only.
                            </div>
                            {signal.scalp_feasibility.theta_impact?.per_hour > 1.5 && (
                                <div className="text-xs text-yellow-300 mt-1">
                                    ⚠️ Time decay: -₹{signal.scalp_feasibility.theta_impact.per_hour.toFixed(1)}/hour
                                </div>
                            )}
                        </div>

                        {/* Risk Recommendation */}
                        {signal.scalp_feasibility.recommendation && (
                            <div className="text-xs text-gray-400 italic border-l-2 border-gray-600 pl-3">
                                {signal.scalp_feasibility.recommendation}
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

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
