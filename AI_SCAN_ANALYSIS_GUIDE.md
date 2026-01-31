# AI Scan Analysis Guide

## Overview
The AI Assistant can analyze your option scan results and provide intelligent insights, recommendations, and answer questions about your trades.

## How It Works

### 1. **Scan Options First**
- Go to the Options Scanner page
- Configure your scan parameters:
  - Index (NIFTY, BANKNIFTY, etc.)
  - Expiry date
  - Minimum Volume
  - Minimum Open Interest
  - Analysis Mode
- Click "Scan Options" to get results

### 2. **AI Analysis**
Once you have scan results, the AI automatically receives:
- All scanned options with strikes, prices, volume, OI
- Probability analysis (bullish/bearish percentages)
- Your selected filters and parameters
- Timestamp of the scan

### 3. **Ask Questions**
Click the "AI Assistant" button (marked with BETA badge) and ask questions like:

**General Analysis**
- "Analyze these 15 NIFTY options signals"
- "What are the top 3 opportunities from this scan?"
- "Summarize the key insights from these results"

**Specific Recommendations**
- "What's the best strike price to trade based on this data?"
- "Which option has the best risk-reward ratio?"
- "Should I trade CE or PE based on this analysis?"

**Risk Analysis**
- "What are the risks in trading these options?"
- "Explain the probability analysis"
- "Why is the bullish probability 68%?"

**Educational**
- "How do I interpret volume and OI in options?"
- "What does the IV indicate for these strikes?"
- "Explain the Greeks for the top signal"

## Features

### Context-Aware Analysis
The AI knows:
- Which index you're scanning (NIFTY, BANKNIFTY, etc.)
- What expiry you selected
- Your volume and OI filters
- All scan results with complete data
- Probability analysis results

### Smart Suggestions
Suggestions automatically update based on:
- Whether you have scan results or not
- The probability direction detected
- The number of options found

### Cost Optimization
The AI system includes:
- **Rate Limiting**: 10 queries/min, 100/hour, 500/day
- **Query Deduplication**: Identical queries within 10 min use cached results
- **Context Optimization**: Scan data is intelligently truncated to save tokens
- **Redis Caching**: Responses cached for 30 minutes

## Usage Tips

### Before Scanning
❌ **Don't:** Ask AI about scans before scanning
✅ **Do:** Read the blue info banner explaining AI features

### After Scanning
✅ **Do:** 
- Ask specific questions about the results
- Request comparisons between options
- Get explanations for probability analysis
- Ask for risk assessments

### Best Practices
1. **Scan first**, then analyze with AI
2. **Be specific** in your questions
3. **Use suggestions** for common queries
4. **Review context** shown in chat header
5. **Check BETA badge** - feature is in testing

## Technical Details

### API Endpoint
```
POST /api/ai/chat
```

### Request Format
```json
{
  "query": "Your question here",
  "scan_data": {
    "symbol": "NIFTY",
    "expiry": "weekly",
    "results": [...],
    "probability": {...},
    "filters": {...}
  },
  "use_cache": true
}
```

### Response Format
```json
{
  "response": "AI analysis text",
  "citations": [...],
  "cached": false,
  "tokens_used": 1234,
  "confidence_score": 0.85,
  "query_type": "analysis"
}
```

## Troubleshooting

### "No scan results" message
**Problem:** Trying to analyze before scanning
**Solution:** Click "Scan Options" button first

### AI not seeing scan data
**Problem:** Scan data not passed to AI
**Solution:** Refresh page and scan again

### 404 error on AI endpoint
**Problem:** Backend not running
**Solution:** Start backend with `python main.py`

### Rate limit exceeded
**Problem:** Too many queries
**Solution:** Wait 1 minute or use suggested queries

## Cost Information

### Token Usage
- Simple query: ~100-200 tokens
- Complex analysis: ~300-500 tokens  
- With full scan context: ~500-1000 tokens

### Pricing (Cohere Command-R-Plus)
- $0.00015 per token
- ~$0.075 per complex query with context
- 60-70% savings with caching enabled

### Daily Limits
- 500 queries per day (rate limited)
- Unlimited with proper API key billing

## Examples

### Example 1: First Time User
```
1. Visit Options Scanner
2. See blue banner: "AI Assistant Ready - Scan options first..."
3. Configure: NIFTY, Weekly expiry
4. Click "Scan Options"
5. Wait for results
6. Click "AI Assistant" button (BETA badge)
7. Ask: "Analyze these NIFTY options signals"
```

### Example 2: Experienced User
```
1. Quick scan with saved preferences
2. Results show 23 options
3. Open AI chat
4. Ask: "Which 3 options have best volume/OI ratio?"
5. Get instant analysis with specific strikes
6. Follow up: "What's the risk for 22500 CE?"
```

### Example 3: Learning Mode
```
1. Scan options
2. Ask: "Explain probability analysis for beginners"
3. Ask: "What does 68% bullish mean?"
4. Ask: "How should I use this information?"
```

## Integration Points

### Options Page
- File: `frontend/app/options/page.tsx`
- Scan data automatically passed to `useAIChat` hook
- Context updates in real-time as results change

### AI Chat Hook
- File: `frontend/lib/hooks/useAIChat.ts`
- Sends scan_data with every query
- Handles responses and caching

### Backend Service
- File: `main.py` - `/api/ai/chat` endpoint
- File: `src/services/ai_analysis_service.py`
- Cost optimizers in `src/services/ai_cost_optimizer.py`

## Status: BETA

This feature is currently in BETA testing:
- Core functionality is stable
- UI/UX improvements ongoing
- Cost optimization actively monitored
- Feedback welcome for improvements

---

**Need Help?** Check the main [AI_CHAT_INTEGRATION_GUIDE.md](./AI_CHAT_INTEGRATION_GUIDE.md) for setup details.
