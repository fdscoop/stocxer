# AI Chat Integration - Complete Guide

## 🎯 Overview

The TradeWise AI Chat Integration provides intelligent, context-aware analysis of trading signals using Cohere's advanced language models. This system features a hybrid dashboard/chat interface with comprehensive cost optimization.

## ✅ Completed Features

### Backend (Phase 1 ✓)
- ✅ Cohere SDK integrated (`cohere>=5.0.0`)
- ✅ AI analysis service module
- ✅ Chat API endpoints (`/api/ai/chat`, `/api/ai/explain-signal`, etc.)
- ✅ Context formatting for scans
- ✅ Prompt engineering templates
- ✅ Redis-based response caching
- ✅ Data context builder for LLM
- ✅ Signal explanation generator
- ✅ Historical comparison context
- ✅ Market insights aggregator

### Frontend (Phase 2 ✓)
- ✅ Chat sidebar/overlay component
- ✅ Message bubble components
- ✅ Chat input with suggestions
- ✅ Typing indicators
- ✅ Citation/reference display
- ✅ Chat history persistence (localStorage)
- ✅ Dashboard mode toggle (Dashboard/Hybrid/Chat)
- ✅ Hybrid layout wrapper
- ✅ State sharing between modes
- ✅ Quick action buttons
- ✅ AI insight cards

### Integration & Features (Phase 3 ✓)
- ✅ "Explain this signal" quick action
- ✅ Context-aware chat queries
- ✅ Smart prompt suggestions
- ✅ Multi-asset comparison queries
- ✅ Trade planning assistant

### Cost Optimization (Phase 4 ✓)
- ✅ Response caching strategy (Redis + in-memory)
- ✅ Query deduplication (10-minute window)
- ✅ Context window optimizer
- ✅ Rate limiting (10/min, 100/hr, 500/day)
- ✅ Graceful fallbacks
- ✅ Token usage tracking
- ✅ Cost estimation API

## 🚀 Quick Start

### 1. Environment Setup

The Cohere API key is already configured in `.env`:

```bash
COHERE_API_KEY=your_cohere_api_key_here
```

### 2. Start the Backend

```bash
cd /Users/bineshbalan/TradeWise
source venv/bin/activate
python main.py
```

The AI endpoints will be available at:
- `POST /api/ai/chat` - Main chat endpoint
- `POST /api/ai/explain-signal` - Quick signal explanations
- `POST /api/ai/compare-indices` - Compare multiple indices
- `POST /api/ai/trade-plan` - Generate trade plans
- `GET /api/ai/usage-stats` - Get usage and cost metrics
- `POST /api/ai/cache/clear` - Clear response cache

### 3. Start the Frontend

```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000` to see the hybrid dashboard.

## 📖 Usage Guide

### Basic Chat Integration

```tsx
import { ChatSidebar } from '@/components/ai/ChatSidebar';
import { useAIChat } from '@/lib/hooks/useAIChat';

function MyDashboard() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const { messages, isLoading, sendMessage } = useAIChat({
    signalData: yourSignalData,
    scanId: yourScanId
  });

  return (
    <>
      <Button onClick={() => setIsChatOpen(true)}>
        Ask AI
      </Button>

      <ChatSidebar
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        onSendMessage={sendMessage}
        messages={messages}
        isLoading={isLoading}
      />
    </>
  );
}
```

### Full Hybrid Dashboard

```tsx
import { HybridDashboardLayout } from '@/components/ai';

function OptionsPage() {
  const [aiInsights, setAiInsights] = useState([
    {
      type: 'opportunity',
      title: 'High Confidence Signal',
      content: 'ICT Bullish Reversal shows 78% confidence...',
      confidence: 0.78
    }
  ]);

  return (
    <HybridDashboardLayout
      signalData={scanResults}
      scanId={scanResults?.id}
      aiInsights={aiInsights}
      defaultMode="hybrid"
    >
      {/* Your dashboard content */}
      <YourSignalCards />
    </HybridDashboardLayout>
  );
}
```

### Quick Actions on Signal Cards

```tsx
import { QuickActionsCompact } from '@/components/ai/QuickActionsBar';

function SignalCard({ signal }) {
  const { sendMessage } = useAIChat({ signalData: signal });

  return (
    <div className="signal-card">
      <h3>{signal.name}</h3>
      <p>Entry: ₹{signal.entry_price}</p>
      
      <QuickActionsCompact
        onActionClick={(prompt) => sendMessage(prompt)}
      />
    </div>
  );
}
```

## 💰 Cost Management

### Current Configuration

- **Rate Limits:**
  - 10 calls per minute
  - 100 calls per hour
  - 500 calls per day

- **Caching:**
  - Redis cache with 30-minute TTL
  - Query deduplication (10-minute window)
  - Automatic context optimization

- **Estimated Costs:**
  - Cohere pricing: ~$0.15 per 1K tokens
  - Average query: ~500 tokens
  - Cost per query: ~$0.075 (~₹6.25)
  - Daily budget (500 calls): ~$37.50 (~₹3,112)

### Check Usage Stats

```bash
curl -X GET http://localhost:8000/api/ai/usage-stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "usage": {
    "calls_last_minute": 2,
    "calls_last_hour": 45,
    "calls_today": 234
  },
  "cost_estimate": {
    "queries_today": 234,
    "estimated_cost_today_usd": 17.55,
    "estimated_cost_today_inr": 1456.65
  },
  "rate_limits": {
    "remaining_this_minute": 8,
    "remaining_this_hour": 55,
    "remaining_today": 266
  }
}
```

### Optimize Costs

1. **Enable Caching:**
   - All responses are cached by default
   - Cache TTL: 30 minutes
   - Query normalization for better hit rates

2. **Use Query Deduplication:**
   - Automatically detects duplicate queries
   - 10-minute deduplication window
   - Prevents redundant API calls

3. **Context Optimization:**
   - Automatic context truncation
   - Removes unnecessary fields
   - Stays within token limits

4. **Rate Limiting:**
   - Protects against overuse
   - Graceful error messages
   - Configurable limits

## 🎨 UI Components

### Available Components

1. **ChatMessage** - Individual message bubbles
2. **ChatInput** - Input field with suggestions
3. **ChatSidebar** - Full chat interface
4. **DashboardModeToggle** - Switch between modes
5. **HybridDashboardLayout** - Complete layout wrapper
6. **AIInsightCard** - AI-generated insights
7. **QuickActionsBar** - Quick action buttons

### Customization

All components accept standard Tailwind classes and can be themed:

```tsx
<ChatSidebar
  className="custom-chat-styles"
  // ... other props
/>
```

## 📊 API Reference

### POST /api/ai/chat

**Request:**
```json
{
  "query": "Explain this signal",
  "signal_data": { /* signal object */ },
  "scan_data": { /* scan results */ },
  "scan_id": "uuid",
  "use_cache": true
}
```

**Response:**
```json
{
  "response": "This is a bullish reversal signal...",
  "citations": [
    {
      "text": "HTF shows bullish trend",
      "source": "Trading Signal Data"
    }
  ],
  "cached": false,
  "tokens_used": 456,
  "confidence_score": 0.85,
  "query_type": "signal_explanation"
}
```

### POST /api/ai/explain-signal

**Request:**
```json
{
  "signal_data": { /* signal object */ },
  "detail_level": "normal"  // brief, normal, detailed
}
```

**Response:**
```json
{
  "explanation": "This ICT Bullish Reversal signal...",
  "key_factors": ["HTF bullish", "LTF confirmation"],
  "confidence": 0.78
}
```

### GET /api/ai/usage-stats

Returns usage statistics and cost estimates (see Cost Management section).

## 🧪 Testing

### Test the AI Chat

```bash
# Test chat endpoint
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "What is a bullish reversal?",
    "use_cache": true
  }'

# Check usage stats
curl -X GET http://localhost:8000/api/ai/usage-stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Frontend Testing

1. Navigate to `/options` page
2. Click "AI Chat" or toggle to "Hybrid" mode
3. Ask questions about signals
4. Use quick actions on signal cards
5. Check chat history persistence

## 🔧 Troubleshooting

### AI Service Not Available

**Error:** "AI service is not available"

**Solution:**
- Verify `COHERE_API_KEY` is set in `.env`
- Restart the backend server
- Check logs for initialization errors

### Rate Limit Exceeded

**Error:** "Rate limit exceeded"

**Solution:**
- Wait for the limit window to reset
- Adjust limits in `ai_cost_optimizer.py`
- Increase cache TTL to reduce calls

### Poor Response Quality

**Solution:**
- Provide more context in signal_data
- Use specific, clear questions
- Try different detail levels
- Check query classification

### Cache Not Working

**Solution:**
- Verify Redis is running: `redis-cli ping`
- Check Redis connection in logs
- Falls back to in-memory cache automatically

## 📝 Next Steps

### Recommended Enhancements

1. **Analytics Dashboard:**
   - Track most asked questions
   - Monitor response quality
   - Visualize cost trends

2. **Advanced Features:**
   - Voice input for queries
   - Multi-language support
   - Custom AI personalities
   - Backtesting analysis

3. **Integration:**
   - Add to mobile app
   - Email/SMS summaries
   - Slack/Discord bot
   - WhatsApp integration

4. **Optimization:**
   - Fine-tune prompts
   - A/B test response formats
   - Implement query routing
   - Add response streaming

## 🎓 Prompt Engineering Tips

### Effective Queries

✅ **Good:**
- "Explain why this is a buy signal"
- "What are the risks of this trade?"
- "Compare NIFTY and BANKNIFTY signals today"
- "What's the best entry point for this setup?"

❌ **Avoid:**
- "Help" (too vague)
- "??????" (no question)
- Very long, complex questions
- Multiple unrelated questions at once

### Query Types

The system automatically classifies queries into:
- `signal_explanation` - Understanding signals
- `risk_analysis` - Risk assessment
- `trade_planning` - Entry/exit strategies
- `comparison` - Comparing multiple assets
- `general` - General trading questions

## 📞 Support

For issues or questions:
1. Check logs: `backend.log` and `frontend.log`
2. Review API response codes
3. Check usage stats endpoint
4. Verify cache and rate limits

## 📜 License & Credits

- Built with Cohere AI
- Uses FastAPI, Next.js, Tailwind CSS
- Redis caching for performance

---

**Last Updated:** January 31, 2026
**Version:** 2.0 (AI Chat Integration Complete)
