// Beginner-Friendly Signal Translation
// Converts technical ICT terms to plain English

function translateToBeginnerTerms(signal) {
    const htf = signal.htf_analysis || {};
    const ltf = signal.ltf_entry_model || {};
    const confirmationStack = signal.confirmation_stack || {};
    const confidence = signal.confidence_breakdown || signal.confidence || {};

    return {
        // Market Trend (HTF Analysis)
        trend: {
            direction: translateDirection(htf.direction),
            directionRaw: htf.direction,
            strength: translateStrength(htf.strength || 0),
            strengthPct: htf.strength || 0,
            quality: translateQuality(htf.structure_quality),
            emoji: getDirectionEmoji(htf.direction)
        },

        // Entry Timing (LTF Entry Model)
        entryTiming: {
            isGood: ltf.found || false,
            message: ltf.found
                ? "✅ Good entry point available now!"
                : "⏸️ Wait for better timing",
            details: ltf.found && ltf.entry_zone
                ? `Best entry: ₹${ltf.entry_zone[0]}-${ltf.entry_zone[1]}`
                : "No clear entry point detected",
            confidence: ltf.confidence || 0
        },

        // Conflicts
        conflicts: detectConflicts(signal),

        // Simple recommendation
        recommendation: getSimpleRecommendation(signal),

        // Confidence
        confidenceScore: confidence.score || confidence.total || 0,
        confidenceLevel: confidence.level || 'UNKNOWN'
    };
}

function translateDirection(dir) {
    const map = {
        'bullish': 'Going Up',
        'bearish': 'Going Down',
        'neutral': 'Sideways'
    };
    return map[dir] || 'Unclear';
}

function getDirectionEmoji(dir) {
    const map = {
        'bullish': '⬆️',
        'bearish': '⬇️',
        'neutral': '↔️'
    };
    return map[dir] || '❓';
}

function translateStrength(strength) {
    if (strength >= 70) return { text: 'Strong', emoji: '💪', color: 'green' };
    if (strength >= 40) return { text: 'Medium', emoji: '👍', color: 'yellow' };
    return { text: 'Weak', emoji: '👎', color: 'red' };
}

function translateQuality(quality) {
    const map = {
        'HIGH': { text: 'Excellent setup', stars: '⭐⭐⭐', color: 'green' },
        'MEDIUM': { text: 'Fair setup', stars: '⭐⭐', color: 'yellow' },
        'LOW': { text: 'Poor setup', stars: '⭐', color: 'red' }
    };
    return map[quality] || { text: 'Unknown', stars: '❓', color: 'gray' };
}

function detectConflicts(signal) {
    const conflicts = [];
    const htf = signal.htf_analysis || {};
    const stack = signal.confirmation_stack || {};

    // Check ML conflict
    if (stack.ml_prediction && !stack.ml_prediction.agrees_with_htf) {
        const htfDir = translateDirection(htf.direction);
        const mlDir = translateDirection(stack.ml_prediction.direction);
        conflicts.push({
            type: 'AI vs Trend',
            message: `Trend says ${htfDir}, but AI predicts ${mlDir}`,
            icon: '⚠️'
        });
    }

    // Check futures conflict
    if (stack.futures_sentiment && !stack.futures_sentiment.agrees_with_htf) {
        conflicts.push({
            type: 'Futures vs Trend',
            message: 'Futures market sentiment conflicts with trend',
            icon: '⚠️'
        });
    }

    // Check constituents conflict
    if (stack.constituents && !stack.constituents.agrees_with_htf) {
        conflicts.push({
            type: 'Stocks vs Trend',
            message: 'Individual stocks moving against overall trend',
            icon: '⚠️'
        });
    }

    return conflicts;
}

function getSimpleRecommendation(signal) {
    const confidence = signal.confidence?.score || signal.confidence_breakdown?.total || 0;
    const action = signal.action || 'WAIT';
    const ltf = signal.ltf_entry_model || {};
    const conflicts = detectConflicts(signal);

    if (action === 'WAIT' || confidence < 40) {
        return {
            action: 'WAIT',
            emoji: '⏸️',
            color: 'yellow',
            colorClass: 'text-yellow-400',
            bgClass: 'bg-yellow-900',
            reasons: [
                confidence < 40 ? `Only ${confidence}% confident - too risky` : null,
                !ltf.found ? 'No good entry point now' : null,
                conflicts.length > 0 ? 'Mixed signals detected' : null
            ].filter(Boolean),
            advice: confidence < 20
                ? 'Wait for much clearer signals (need 60%+ confidence)'
                : 'Wait for better setup (need 60%+ confidence)'
        };
    }

    if (confidence >= 60) {
        const isCall = action.includes('CALL');
        return {
            action: isCall ? 'BUY CALL' : 'BUY PUT',
            emoji: isCall ? '📈' : '📉',
            color: isCall ? 'green' : 'red',
            colorClass: isCall ? 'text-green-400' : 'text-red-400',
            bgClass: isCall ? 'bg-green-900' : 'bg-red-900',
            reasons: [
                `${Math.round(confidence)}% confident`,
                ltf.found ? 'Good entry timing' : null,
                'Trend and signals align'
            ].filter(Boolean),
            advice: isCall
                ? 'Market may move up - consider calls'
                : 'Market may move down - consider puts'
        };
    }

    return {
        action: 'BE CAUTIOUS',
        emoji: '⚠️',
        color: 'orange',
        colorClass: 'text-orange-400',
        bgClass: 'bg-orange-900',
        reasons: [`${Math.round(confidence)}% confidence - moderate risk`],
        advice: 'Trade only if you understand the risks'
    };
}

function getConfidenceColor(confidence) {
    if (confidence >= 60) return { bg: 'bg-green-500', text: 'text-green-400' };
    if (confidence >= 40) return { bg: 'bg-yellow-500', text: 'text-yellow-400' };
    return { bg: 'bg-red-500', text: 'text-red-400' };
}

// Export for use in main HTML
if (typeof window !== 'undefined') {
    window.translateToBeginnerTerms = translateToBeginnerTerms;
    window.getConfidenceColor = getConfidenceColor;
}
