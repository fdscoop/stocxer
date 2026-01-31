# AI Chat Integration - Quick Reference

## 🚀 Quick Start (30 seconds)

### Backend Setup
```bash
# API key already configured in .env
# Just start the server
cd /Users/bineshbalan/TradeWise
source venv/bin/activate
python main.py
```

### Frontend Setup
```bash
cd frontend
npm run dev
```

## 💬 Basic Usage

### Add Chat to Any Page

```tsx
import { ChatSidebar } from '@/components/ai/ChatSidebar';
import { useAIChat } from '@/lib/hooks/useAIChat';
import { Button } from '@/components/ui/button';
import { MessageSquare } from 'lucide-react';

export default function MyPage() {
  const [chatOpen, setChatOpen] = useState(false);
  const { messages, sendMessage, isLoading } = useAIChat({
    signalData: mySignalData,  // Optional
    scanId: myScanId           // Optional
  });

  return (
    <>
      <Button onClick={() => setChatOpen(true)}>
        <MessageSquare className="w-4 h-4 mr-2" />
        Ask AI
      </Button>

      <ChatSidebar
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
        onSendMessage={sendMessage}
        messages={messages}
        isLoading={isLoading}
      />
    </>
  );
}
```

### Use Hybrid Dashboard

```tsx
import { HybridDashboardLayout } from '@/components/ai';

export default function OptionsPage() {
  return (
    <HybridDashboardLayout 
      defaultMode="hybrid"
      aiInsights={[
        {
          type: 'opportunity',
          title: 'High Confidence Signal',
          content: 'Strong bullish setup detected...',
          confidence: 0.85
        }
      ]}
    >
      {/* Your existing content */}
      <YourSignalCards />
    </HybridDashboardLayout>
  );
}
```

## 🎯 Quick Actions on Cards

```tsx
import { QuickActionsCompact } from '@/components/ai/QuickActionsBar';

function SignalCard({ signal }) {
  const { sendMessage } = useAIChat({ signalData: signal });

  return (
    <Card>
      <h3>{signal.name}</h3>
      <p>Entry: ₹{signal.entry_price}</p>
      
      <QuickActionsCompact 
        onActionClick={(prompt) => sendMessage(prompt)}
      />
    </Card>
  );
}
```

## 📡 API Calls

### Chat
```bash
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain this signal", "use_cache": true}'
```

### Explain Signal
```bash
curl -X POST http://localhost:8000/api/ai/explain-signal \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"signal_data": {...}, "detail_level": "normal"}'
```

### Usage Stats
```bash
curl http://localhost:8000/api/ai/usage-stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 💰 Cost Info

| Item | Value |
|------|-------|
| Cost per query | ~₹6.25 |
| Rate limit (min) | 10 calls |
| Rate limit (hour) | 100 calls |
| Rate limit (day) | 500 calls |
| Daily budget | ~₹3,112 |
| Cache TTL | 30 minutes |

## 🧪 Test It

```bash
cd /Users/bineshbalan/TradeWise
python test_ai_chat_integration.py
```

## 📚 Full Documentation

- **Complete Guide:** `AI_CHAT_INTEGRATION_GUIDE.md`
- **Summary:** `AI_CHAT_PHASE2_SUMMARY.md`
- **Examples:** `frontend/components/ai/INTEGRATION_EXAMPLE.tsx`

## 🎨 Components Available

| Component | Purpose |
|-----------|---------|
| `ChatSidebar` | Full chat interface |
| `ChatMessage` | Message bubbles |
| `ChatInput` | Input with suggestions |
| `HybridDashboardLayout` | Full layout |
| `DashboardModeToggle` | Mode switcher |
| `AIInsightCard` | AI insights |
| `QuickActionsBar` | Quick actions |
| `useAIChat` | React hook |

## 🔧 Configuration

### Environment Variables
```bash
COHERE_API_KEY=your_cohere_api_key_here
REDIS_URL=redis://localhost:6379
AI_CACHE_TTL=1800
```

### Customize Rate Limits
Edit `src/services/ai_cost_optimizer.py`:
```python
rate_limiter = RateLimiter(
    max_calls_per_minute=10,
    max_calls_per_hour=100,
    max_calls_per_day=500
)
```

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| "AI service not available" | Check `.env` has `COHERE_API_KEY` |
| "Rate limit exceeded" | Wait or increase limits |
| No responses | Check backend logs |
| Cache not working | Verify Redis is running |

## 📞 Support Files

- Test Suite: `test_ai_chat_integration.py`
- Backend Logs: `backend.log`
- Cost Optimizer: `src/services/ai_cost_optimizer.py`
- AI Service: `src/services/ai_analysis_service.py`

---

**Status:** ✅ Ready to use!

**Quick Links:**
- Full Guide: [AI_CHAT_INTEGRATION_GUIDE.md](AI_CHAT_INTEGRATION_GUIDE.md)
- Summary: [AI_CHAT_PHASE2_SUMMARY.md](AI_CHAT_PHASE2_SUMMARY.md)
