/**
 * Translation utility to convert technical ICT trading terms to beginner-friendly language
 */

export interface HTFAnalysis {
    direction: 'bullish' | 'bearish' | 'neutral'
    strength: number
    structure_quality: 'HIGH' | 'MEDIUM' | 'LOW'
    premium_discount?: 'premium' | 'discount' | 'equilibrium'
}

export interface LTFEntry {
    found: boolean
    entry_type: string | null
    timeframe: string | null
    confidence: number
}

export interface ConfirmationStack {
    ml_prediction?: {
        direction: string
        confidence: number
        agrees_with_htf: boolean
    }
    futures_sentiment?: {
        sentiment: string
        agrees_with_htf: boolean
    }
    constituents?: {
        direction: string
        confidence: number
        agrees_with_htf: boolean
    }
}

export interface ConfidenceBreakdown {
    total: number
    level: string
    components: {
        ict_htf_structure: number
        ict_ltf_confirmation: number
        ml_alignment: number
        candlestick_patterns: number
        futures_basis: number
        constituents: number
    }
}

export interface BeginnerSignal {
    trend: {
        emoji: string
        direction: string
        directionRaw: string
        strength: {
            emoji: string
            text: string
            color: string
        }
        quality: {
            stars: string
            text: string
            color: string
        }
    }
    entryTiming: {
        message: string
        details: string
        color: string
    }
    conflicts: Array<{
        message: string
        severity: 'high' | 'medium' | 'low'
    }>
    recommendation: {
        emoji: string
        action: string
        color: string
        colorClass: string
        bgClass: string
        reasons: string[]
        advice: string
    }
    confidenceScore: number
    confidenceLevel: string
}

export function translateHTFAnalysis(htf?: HTFAnalysis) {
    if (!htf) {
        return {
            emoji: '❓',
            direction: 'Unclear',
            directionRaw: 'neutral',
            strength: { emoji: '--', text: '--', color: 'gray' },
            quality: { stars: '--', text: '--', color: 'gray' }
        }
    }

    const directionMap = {
        bullish: { emoji: '📈', text: 'Going Up', raw: 'bullish' },
        bearish: { emoji: '📉', text: 'Going Down', raw: 'bearish' },
        neutral: { emoji: '↔️', text: 'Sideways', raw: 'neutral' }
    }

    const strengthMap = (strength: number) => {
        if (strength >= 70) return { emoji: '🔥', text: 'Very Strong', color: 'green' }
        if (strength >= 50) return { emoji: '💪', text: 'Strong', color: 'lime' }
        if (strength >= 30) return { emoji: '👍', text: 'Moderate', color: 'yellow' }
        return { emoji: '👎', text: 'Weak', color: 'orange' }
    }

    const qualityMap = {
        HIGH: { stars: '⭐⭐⭐', text: 'High Quality', color: 'green' },
        MEDIUM: { stars: '⭐⭐', text: 'Medium Quality', color: 'yellow' },
        LOW: { stars: '⭐', text: 'Low Quality', color: 'orange' }
    }

    const dir = directionMap[htf.direction]

    return {
        emoji: dir.emoji,
        direction: dir.text,
        directionRaw: dir.raw,
        strength: strengthMap(htf.strength),
        quality: qualityMap[htf.structure_quality]
    }
}

export function translateLTFEntry(ltf?: LTFEntry) {
    if (!ltf || !ltf.found) {
        return {
            message: '⏸️ Checking timing...',
            details: 'Please wait for scan...',
            color: 'gray'
        }
    }

    if (ltf.confidence >= 70) {
        return {
            message: '✅ Good Entry Timing',
            details: `${ltf.entry_type || 'Setup'} detected on ${ltf.timeframe || 'chart'}`,
            color: 'green'
        }
    }

    if (ltf.confidence >= 50) {
        return {
            message: '⚠️ Fair Entry Timing',
            details: 'Entry is possible but not ideal',
            color: 'yellow'
        }
    }

    return {
        message: '❌ Poor Entry Timing',
        details: 'Wait for a better setup',
        color: 'red'
    }
}

export function detectConflicts(stack?: ConfirmationStack) {
    const conflicts: Array<{ message: string; severity: 'high' | 'medium' | 'low' }> = []

    if (!stack) return conflicts

    // ML vs HTF conflict
    if (stack.ml_prediction && !stack.ml_prediction.agrees_with_htf) {
        conflicts.push({
            message: `AI prediction (${stack.ml_prediction.direction}) disagrees with market trend`,
            severity: 'high'
        })
    }

    // Futures vs HTF conflict
    if (stack.futures_sentiment && !stack.futures_sentiment.agrees_with_htf) {
        conflicts.push({
            message: `Futures market (${stack.futures_sentiment.sentiment}) shows different sentiment`,
            severity: 'medium'
        })
    }

    // Constituents vs HTF conflict
    if (stack.constituents && !stack.constituents.agrees_with_htf) {
        conflicts.push({
            message: `Underlying stocks (${stack.constituents.direction}) moving differently`,
            severity: 'medium'
        })
    }

    return conflicts
}

export function translateRecommendation(
    action: string,
    htf?: HTFAnalysis,
    ltf?: LTFEntry,
    confidence?: number
) {
    const conf = confidence || 0

    if (action.includes('WAIT') || conf < 40) {
        return {
            emoji: '⏸️',
            action: 'WAIT',
            color: 'yellow',
            colorClass: 'text-yellow-500',
            bgClass: 'bg-yellow',
            reasons: [
                'Signal strength is too low',
                'Wait for clearer market direction',
                'Better opportunities may come'
            ],
            advice: 'Wait for clearer signals to reduce your risk.'
        }
    }

    if (action.includes('AVOID')) {
        return {
            emoji: '⛔',
            action: 'AVOID',
            color: 'red',
            colorClass: 'text-red-500',
            bgClass: 'bg-red',
            reasons: [
                'Market conditions are unfavorable',
                'High risk of loss',
                'Multiple conflicting signals'
            ],
            advice: 'Do not trade right now. Protect your capital.'
        }
    }

    if (action.includes('CALL') || action.includes('BUY')) {
        return {
            emoji: '🚀',
            action: action,
            color: 'green',
            colorClass: 'text-green-500',
            bgClass: 'bg-green',
            reasons: [
                htf?.direction === 'bullish' ? 'Market trend is up' : 'Setup detected',
                ltf?.found ? 'Good entry timing found' : 'Entry conditions met',
                `${conf}% confidence in this trade`
            ],
            advice: 'Consider this trade, but always use stop loss.'
        }
    }

    if (action.includes('PUT') || action.includes('SELL')) {
        return {
            emoji: '📉',
            action: action,
            color: 'red',
            colorClass: 'text-red-500',
            bgClass: 'bg-red',
            reasons: [
                htf?.direction === 'bearish' ? 'Market trend is down' : 'Setup detected',
                ltf?.found ? 'Good entry timing found' : 'Entry conditions met',
                `${conf}% confidence in this trade`
            ],
            advice: 'Consider this trade, but always use stop loss.'
        }
    }

    return {
        emoji: '❓',
        action: 'ANALYZING',
        color: 'gray',
        colorClass: 'text-gray-500',
        bgClass: 'bg-gray',
        reasons: ['Analyzing market conditions...'],
        advice: 'Please wait while we analyze the market.'
    }
}

export function getConfidenceColor(score: number) {
    if (score >= 80) return { text: 'text-green-500', bg: 'bg-green-500' }
    if (score >= 60) return { text: 'text-lime-500', bg: 'bg-lime-500' }
    if (score >= 40) return { text: 'text-yellow-500', bg: 'bg-yellow-500' }
    if (score >= 20) return { text: 'text-orange-500', bg: 'bg-orange-500' }
    return { text: 'text-red-500', bg: 'bg-red-500' }
}

export function translateToBeginnerTerms(signal: any): BeginnerSignal {
    const htf = signal.htf_analysis
    const ltf = signal.ltf_entry_model
    const stack = signal.confirmation_stack
    const breakdown = signal.confidence_breakdown

    const trend = translateHTFAnalysis(htf)
    const entryTiming = translateLTFEntry(ltf)
    const conflicts = detectConflicts(stack)
    const confidenceScore = breakdown?.total || signal.confidence?.score || 0
    const confidenceLevel = breakdown?.level || signal.confidence?.level || 'UNKNOWN'
    const recommendation = translateRecommendation(signal.action, htf, ltf, confidenceScore)

    return {
        trend,
        entryTiming,
        conflicts,
        recommendation,
        confidenceScore,
        confidenceLevel
    }
}
