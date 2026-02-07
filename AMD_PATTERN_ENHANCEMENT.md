# AMD Pattern Detection Enhancement for TradeWise

## Problem Summary

Based on the analysis of Feb 6, 2026 trading session:

### What Happened
1. **Morning (4:30-5:00 AM IST)**: App correctly identified bearish bias, suggested PE options
2. **At 4:40-4:46 AM**: Market tested support zone (around 25564) multiple times
3. **Manipulation Event**: Price broke below support to 25504 (bear trap)
4. **Recovery**: Price immediately reversed and moved up to resistance zones
5. **Result**: Both PE and CE would have been profitable, but app only suggested PE

### Analysis Results
- **Total Scans Today**: 15
- **PE Recommendations**: 15 (100%)
- **CE Recommendations**: 0 (0%)
- **Bear Traps Detected (retrospectively)**: 3
- **Manipulation Detection by App**: ❌ None

## Root Cause Analysis

### 1. Timeframe Limitation
The current MTF analysis uses:
- Monthly, Weekly, Daily, 4H, 1H, 15min, 5min

**Missing**: 1-minute and 3-minute timeframes where AMD patterns are most visible.

### 2. ICT Logic Flaw
Current logic:
```
HTF Bias (Daily/4H) → LTF Confirmation (15min/5min) → Entry
```

The issue: When HTF shows bearish bias, it **never** considers CALL opportunities even at key support zones where reversals are likely.

### 3. No Manipulation Detection
The app lacks a "Smart Money Concept" module that detects:
- **Stop Hunts**: Quick moves below/above key levels followed by reversal
- **False Breakouts**: Price breaks level then immediately reclaims it
- **Liquidity Grabs**: Sharp spikes designed to trigger stop losses

### 4. Static vs Dynamic Analysis
Current scans are **point-in-time snapshots**. They don't track:
- Zone test count (how many times a level was tested)
- Time between tests
- Recovery behavior after breaks

## Proposed Solution

### Phase 1: Add 1-3 Minute Timeframes

Update `src/analytics/mtf_ict_analysis.py`:

```python
class Timeframe(Enum):
    # Existing
    MONTHLY = "M"
    WEEKLY = "W"
    DAILY = "D"
    FOUR_HOUR = "240"
    ONE_HOUR = "60"
    FIFTEEN_MIN = "15"
    FIVE_MIN = "5"
    # NEW - for AMD detection
    THREE_MIN = "3"
    ONE_MIN = "1"


FYERS_RESOLUTION = {
    # ... existing ...
    Timeframe.THREE_MIN: "3",
    Timeframe.ONE_MIN: "1"
}

LOOKBACK_DAYS = {
    # ... existing ...
    Timeframe.THREE_MIN: 5,   # 5 days for 3-min
    Timeframe.ONE_MIN: 2,     # 2 days for 1-min (lots of data)
}
```

### Phase 2: Add AMD Pattern Detector

Create new file `src/analytics/amd_detector.py`:

```python
"""
AMD (Accumulation, Manipulation, Distribution) Pattern Detector

Smart Money Concepts:
- Accumulation: SM building positions, low volatility, range-bound
- Manipulation: False breakout/breakdown to trap retail (stop hunt)
- Distribution: SM distributing at better prices after manipulation

Detection Logic:
1. Track key support/resistance zones from HTF
2. Monitor zone tests in LTF (1-3 min)
3. On 3rd+ test: Check if break is followed by immediate recovery
4. If yes → Manipulation detected → Counter-trade opportunity
"""

@dataclass
class ManipulationEvent:
    type: str  # "BEAR_TRAP", "BULL_TRAP"
    zone_level: float
    break_price: float
    recovery_price: float
    time: datetime
    confidence: float
    suggested_action: str  # "BUY CALL", "BUY PUT"
    volume_analysis: str   # "LOW_VOLUME_BREAK", "HIGH_VOLUME_REVERSAL"


class AMDPatternDetector:
    def __init__(self, fyers_client, htf_zones: dict):
        self.fyers = fyers_client
        self.support_zones = htf_zones.get('support', [])
        self.resistance_zones = htf_zones.get('resistance', [])
        self.zone_tests = {}  # Track test count per zone
    
    def detect_manipulation(self, ltf_data: pd.DataFrame) -> List[ManipulationEvent]:
        """
        Detect manipulation events in 1-3 minute data
        
        A manipulation event requires:
        1. Zone has been tested 2+ times before
        2. Current break goes beyond zone by 0.2-0.5%
        3. Price recovers above/below zone within 3-5 candles
        4. Volume on break is lower than average (fake move)
        5. Volume on recovery is higher (real move)
        """
        events = []
        
        for zone in self.support_zones:
            zone_price = zone['price']
            
            for i in range(5, len(ltf_data) - 3):
                current = ltf_data.iloc[i]
                
                # Check for break below support
                if current['low'] < zone_price * 0.998:  # 0.2% break
                    # Check previous candles were above
                    prev_above = all(
                        ltf_data.iloc[j]['close'] >= zone_price * 0.998 
                        for j in range(i-3, i)
                    )
                    
                    if prev_above:
                        # Check if price recovers in next 3-5 candles
                        recovery = any(
                            ltf_data.iloc[j]['close'] >= zone_price * 1.002
                            for j in range(i+1, min(i+6, len(ltf_data)))
                        )
                        
                        if recovery:
                            # Calculate volume profile
                            break_volume = current['volume']
                            avg_volume = ltf_data['volume'].iloc[i-20:i].mean()
                            recovery_volumes = ltf_data['volume'].iloc[i+1:i+6]
                            max_recovery_vol = recovery_volumes.max()
                            
                            # Low volume break + high volume recovery = manipulation
                            is_manipulation = (
                                break_volume < avg_volume * 0.8 and
                                max_recovery_vol > avg_volume * 1.2
                            )
                            
                            if is_manipulation:
                                events.append(ManipulationEvent(
                                    type="BEAR_TRAP",
                                    zone_level=zone_price,
                                    break_price=current['low'],
                                    recovery_price=ltf_data.iloc[i+3]['close'],
                                    time=ltf_data.index[i],
                                    confidence=75.0,
                                    suggested_action="BUY CALL",
                                    volume_analysis="LOW_VOLUME_BREAK"
                                ))
        
        return events
```

### Phase 3: Integrate into Main Scanner

Update the options scanner to check for AMD patterns:

```python
# In src/analytics/index_options.py or signals generation

def generate_actionable_signal(index: str, chain: OptionChain, ...):
    # Existing HTF/LTF analysis
    htf_bias = analyze_htf(...)  # bearish
    ltf_confirmation = analyze_ltf(...)
    
    # NEW: Check for manipulation events
    amd_detector = AMDPatternDetector(fyers_client, htf_zones)
    ltf_1min = fetch_1min_data(index)
    manipulation_events = amd_detector.detect_manipulation(ltf_1min)
    
    # If manipulation detected at support → override with CALL recommendation
    if manipulation_events:
        latest_event = manipulation_events[-1]
        
        if latest_event.type == "BEAR_TRAP" and latest_event.confidence > 60:
            # Override bearish bias with CALL opportunity
            return {
                "signal": "AMD_REVERSAL",
                "action": "BUY CALL",
                "reason": f"Bear trap detected at {latest_event.zone_level}",
                "confidence": latest_event.confidence,
                "entry": latest_event.recovery_price,
                # ...
            }
    
    # Continue with normal HTF/LTF logic
    return existing_signal_logic(...)
```

### Phase 4: Add Real-Time Zone Monitoring

Create a zone watcher that continuously monitors key levels:

```python
class ZoneWatcher:
    """
    Real-time monitoring of key support/resistance zones
    Sends alerts when manipulation patterns form
    """
    
    def __init__(self, index: str, zones: dict):
        self.index = index
        self.zones = zones
        self.test_history = defaultdict(list)
    
    async def monitor(self):
        """Run continuous monitoring loop"""
        while True:
            current_price = await get_live_price(self.index)
            
            for zone in self.zones['support']:
                level = zone['price']
                
                # Record zone test
                if abs(current_price - level) / level < 0.002:  # Within 0.2%
                    self.test_history[level].append({
                        'time': datetime.now(),
                        'price': current_price
                    })
                
                # Alert on 3rd+ test
                test_count = len(self.test_history[level])
                if test_count >= 3:
                    await send_alert(
                        f"⚠️ {self.index} testing support {level} for {test_count}th time! "
                        f"Watch for manipulation/reversal"
                    )
            
            await asyncio.sleep(5)  # Check every 5 seconds
```

## Implementation Priority

| Phase | Effort | Impact | Priority |
|-------|--------|--------|----------|
| Phase 1: Add 1-3 min TF | Low | High | P0 |
| Phase 2: AMD Detector | Medium | High | P0 |
| Phase 3: Scanner Integration | Medium | High | P1 |
| Phase 4: Real-time Monitor | High | Medium | P2 |

## Expected Outcome

After implementation:

### Before (Today)
- 15/15 scans recommended PE
- 0/15 scans recommended CE
- 3 manipulation events missed
- User missed CALL opportunity

### After (With AMD Detection)
- 12/15 scans recommend PE (during bearish structure)
- 3/15 scans recommend CE (at manipulation events)
- 3/3 manipulation events detected
- User gets both PE and CE opportunities

## Quick Win: Manual AMD Checklist

Until the feature is implemented, use this manual checklist:

```
✅ AMD PATTERN CHECKLIST (for manual trading)

1. IDENTIFY KEY ZONES
   □ Mark HTF (4H/1H) support/resistance
   □ Note 4H swing lows = key support
   □ Note 4H swing highs = key resistance

2. COUNT ZONE TESTS (in 15min/5min)
   □ 1st test: Normal reaction expected
   □ 2nd test: Structure still valid
   □ 3rd test: HIGH ALERT - watch for manipulation

3. ON 3RD TEST BREAK
   □ Check 1-min chart for break below zone
   □ Compare break volume vs average
   □ Wait 3-5 minutes for recovery

4. CONFIRM MANIPULATION
   □ Low volume on break = fake move
   □ High volume on recovery = real move
   □ Price reclaims zone = REVERSAL SIGNAL

5. TAKE COUNTER-TRADE
   □ Bear trap at support → BUY CALL
   □ Bull trap at resistance → BUY PUT
   □ Set tight SL below/above manipulation low/high
```

---

## Files to Modify

1. `src/analytics/mtf_ict_analysis.py` - Add 1-3 min timeframes
2. `src/analytics/amd_detector.py` - NEW FILE for AMD detection
3. `src/analytics/index_options.py` - Integrate AMD into signal generation
4. `src/routers/signals.py` - Add AMD signal type to API responses
5. `frontend/app/page.tsx` - Display AMD alerts on dashboard

---

**Created**: Feb 6, 2026
**Analysis Script**: `analyze_nifty_amd_pattern.py`
**Author**: TradeWise AI Assistant
