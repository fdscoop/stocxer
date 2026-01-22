'use client'

import * as React from 'react'
import { useRouter } from 'next/navigation'
import { Header } from '@/components/layout/header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { StatCard, StatsGrid } from '@/components/trading/stat-card'
import { SignalCard, SignalGrid, Signal } from '@/components/trading/signal-card'
import { ProbabilityBar, SentimentGauge } from '@/components/trading/probability-bar'
import { LoadingModal } from '@/components/trading/loading-modal'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { RefreshCw, TrendingUp, TrendingDown, BarChart3, Target, Users, Zap, ArrowUp, ArrowDown, Minus } from 'lucide-react'
import Link from 'next/link'
import { getApiUrl } from '@/lib/config'

// Types for scan results
interface ProbabilityAnalysis {
  expected_direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  probability_up: number
  probability_down: number
  expected_move_pct: number
  stocks_scanned: number
  total_stocks: number
  confidence: number
  bullish_stocks: number
  bearish_stocks: number
  bullish_pct?: number
  bearish_pct?: number
  market_regime?: string
  top_bullish_stocks?: Array<{ symbol: string; probability: number; expected_move: number }>
  top_bearish_stocks?: Array<{ symbol: string; probability: number; expected_move: number }>
  volume_surge_stocks?: Array<{ symbol: string; has_surge: boolean }>
}

interface OptionResult {
  symbol?: string
  strike: number
  type: 'CALL' | 'PUT' | 'CE' | 'PE'
  ltp: number
  change?: number
  change_pct?: number
  volume: number
  oi: number
  iv?: number
  delta?: number
  gamma?: number
  score?: number
  recommendation?: string
  probability_boost?: boolean
}

interface TradingSignal {
  action: string
  strike: number
  type: string
  entry_price: number
  target_1: number
  target_2: number
  stop_loss: number
  risk_reward: string
  confidence: number
  direction: string
  trading_symbol: string
}

interface ScanResults {
  probability_analysis?: ProbabilityAnalysis
  recommended_option_type?: 'CALL' | 'PUT' | 'STRADDLE'
  options?: OptionResult[]
  index?: string
  expiry?: string
  spot_price?: number
  market_data?: {
    spot_price: number
    atm_strike: number
    vix?: number
    expiry_date: string
    days_to_expiry: number
  }
  data_source?: 'live' | 'demo'
}

// Mock data for demonstration
const mockSignals: Signal[] = [
  {
    id: '1',
    symbol: 'RELIANCE',
    action: 'BUY',
    price: 2456.50,
    target: 2580.00,
    stopLoss: 2400.00,
    confidence: 85,
    timestamp: new Date().toISOString(),
    reasons: ['RSI Oversold', 'Support Level', 'Volume Breakout'],
  },
  {
    id: '2',
    symbol: 'TCS',
    action: 'SELL',
    price: 3890.00,
    target: 3750.00,
    stopLoss: 3950.00,
    confidence: 72,
    timestamp: new Date().toISOString(),
    reasons: ['Resistance Level', 'Bearish Divergence'],
  },
  {
    id: '3',
    symbol: 'HDFCBANK',
    action: 'BUY',
    price: 1654.25,
    target: 1720.00,
    stopLoss: 1620.00,
    confidence: 78,
    timestamp: new Date().toISOString(),
    reasons: ['Breakout', 'Bullish Momentum'],
  },
]

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = React.useState<{ email: string } | null>(null)
  const [selectedIndex, setSelectedIndex] = React.useState('NIFTY')
  const [signals, setSignals] = React.useState<Signal[]>(mockSignals)
  const [loading, setLoading] = React.useState(false)
  const [loadingMessage, setLoadingMessage] = React.useState('Loading Data...')
  const [loadingProgress, setLoadingProgress] = React.useState(0)
  const [loadingSteps, setLoadingSteps] = React.useState<Array<{ id: string; label: string; status: 'pending' | 'loading' | 'complete' | 'error' }>>([
    { id: '1', label: 'Fetching spot price...', status: 'pending' },
    { id: '2', label: 'Getting expiry dates...', status: 'pending' },
    { id: '3', label: 'Generating option symbols...', status: 'pending' },
    { id: '4', label: 'Fetching option chain data...', status: 'pending' },
    { id: '5', label: 'Analyzing data...', status: 'pending' },
    { id: '6', label: 'Generating signals...', status: 'pending' },
  ])
  const [currentTime, setCurrentTime] = React.useState<string>('')
  const [mounted, setMounted] = React.useState(false)
  const [scanResults, setScanResults] = React.useState<ScanResults | null>(null)
  const [tradingSignal, setTradingSignal] = React.useState<TradingSignal | null>(null)
  const [toast, setToast] = React.useState<{ message: string; type: 'success' | 'error' } | null>(null)

  // Calculate trading signal from scan results
  const calculateTradingSignal = (data: ScanResults): TradingSignal | null => {
    if (!data.probability_analysis || !data.options || data.options.length === 0) return null

    const prob = data.probability_analysis
    const recommendedType = data.recommended_option_type || 'CALL'

    // Find the RECOMMENDED option (the one with probability_boost = true)
    let bestOption = data.options.find(opt => opt.probability_boost === true)

    // Fallback: Find the best option matching the recommendation type
    if (!bestOption) {
      const matchingOptions = data.options.filter(opt => {
        const optType = opt.type === 'CE' ? 'CALL' : opt.type === 'PE' ? 'PUT' : opt.type
        return optType === recommendedType
      })

      bestOption = matchingOptions.length > 0
        ? matchingOptions.sort((a, b) => (b.score || 0) - (a.score || 0))[0]
        : data.options[0]
    }

    const entryPrice = bestOption.ltp
    const optionType = bestOption.type === 'CE' ? 'CALL' : bestOption.type === 'PE' ? 'PUT' : bestOption.type

    // Calculate realistic targets and stop loss based on option premium
    // Lower premiums need higher % gains, higher premiums need lower % gains
    let target1Multiplier = 1.30  // Default 30%
    let target2Multiplier = 1.80  // Default 80%
    let stopLossMultiplier = 0.75 // Default 25% loss

    // Adjust multipliers based on option price
    if (entryPrice < 50) {
      // Deep OTM options: higher % targets
      target1Multiplier = 1.50  // 50%
      target2Multiplier = 2.00  // 100%
      stopLossMultiplier = 0.60 // 40% loss
    } else if (entryPrice > 150) {
      // ITM or expensive options: lower % targets
      target1Multiplier = 1.20  // 20%
      target2Multiplier = 1.50  // 50%
      stopLossMultiplier = 0.80 // 20% loss
    }

    const target1 = Math.round(entryPrice * target1Multiplier * 100) / 100
    const target2 = Math.round(entryPrice * target2Multiplier * 100) / 100
    const stopLoss = Math.round(entryPrice * stopLossMultiplier * 100) / 100

    // Calculate risk-reward ratio
    const risk = entryPrice - stopLoss
    const reward1 = target1 - entryPrice
    const riskReward = risk > 0 ? `1:${(reward1 / risk).toFixed(1)}` : '1:2'

    // Determine action and direction
    const action = recommendedType === 'CALL' ? 'BUY CALL' : recommendedType === 'PUT' ? 'BUY PUT' : 'STRADDLE'
    const direction = prob.expected_direction

    // Calculate confidence
    const confidence = Math.round(prob.confidence * 100)

    // Build trading symbol
    const indexSymbol = data.index || 'NIFTY'
    const expiry = data.market_data?.expiry_date || data.expiry || ''
    const tradingSymbol = `${indexSymbol} ${bestOption.strike} ${optionType}`

    return {
      action,
      strike: bestOption.strike,
      type: optionType,
      entry_price: entryPrice,
      target_1: target1,
      target_2: target2,
      stop_loss: stopLoss,
      risk_reward: riskReward,
      confidence,
      direction,
      trading_symbol: tradingSymbol
    }
  }

  React.useEffect(() => {
    // Mark as mounted for client-side rendering
    setMounted(true)
    setCurrentTime(new Date().toLocaleTimeString('en-IN'))

    // Update time every minute
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString('en-IN'))
    }, 60000)

    // Check for auth token - redirect to landing if not logged in
    const token = localStorage.getItem('token') || localStorage.getItem('jwt_token')
    const email = localStorage.getItem('userEmail')
    if (token && email) {
      setUser({ email })
    } else {
      // Redirect to landing page if not authenticated
      router.push('/landing')
    }

    return () => clearInterval(timer)
  }, [router])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('jwt_token')
    localStorage.removeItem('userEmail')
    setUser(null)
    // Redirect to landing page after logout
    router.push('/landing')
  }

  const handleQuickScan = async () => {
    const token = localStorage.getItem('token') || localStorage.getItem('jwt_token')

    // Check if user is logged in
    if (!token) {
      setToast({ message: 'Please login first to scan options', type: 'error' })
      setTimeout(() => {
        setToast(null)
        router.push('/login')
      }, 2000)
      return
    }

    setLoading(true)
    setLoadingMessage('Loading Data...')
    setLoadingProgress(0)

    // Reset loading steps
    const resetSteps = [
      { id: '1', label: 'Fetching spot price...', status: 'pending' as const },
      { id: '2', label: 'Getting expiry dates...', status: 'pending' as const },
      { id: '3', label: 'Generating option symbols...', status: 'pending' as const },
      { id: '4', label: 'Fetching option chain data...', status: 'pending' as const },
      { id: '5', label: 'Analyzing data...', status: 'pending' as const },
      { id: '6', label: 'Generating signals...', status: 'pending' as const },
    ]
    setLoadingSteps(resetSteps)

    // Helper to update a step
    const updateStep = (stepId: string, status: 'pending' | 'loading' | 'complete' | 'error', progress: number) => {
      setLoadingSteps(prev => prev.map(s =>
        s.id === stepId ? { ...s, status } : s
      ))
      setLoadingProgress(progress)
    }

    try {
      // Step 1: Fetching spot price
      updateStep('1', 'loading', 10)

      console.log(`🔍 Scanning ${selectedIndex} options...`)

      const apiUrl = getApiUrl()

      // Step 1 complete, Step 2: Getting expiry dates
      updateStep('1', 'complete', 17)
      updateStep('2', 'loading', 25)

      // Get the next weekly expiry (for demo, using current date)
      const today = new Date()
      const nextThursday = new Date(today)
      nextThursday.setDate(today.getDate() + ((4 - today.getDay() + 7) % 7))
      const expiry = nextThursday.toISOString().split('T')[0]

      // Step 2 complete, Step 3: Generating option symbols
      updateStep('2', 'complete', 33)
      updateStep('3', 'loading', 40)

      const url = `${apiUrl}/options/scan?index=${selectedIndex}&expiry=${expiry}&min_volume=1000&min_oi=10000&strategy=all&include_probability=true`

      console.log(`📡 Fetching scan data from: ${url}`)
      console.log(`📈 Selected index: ${selectedIndex}`)

      // Step 3 complete, Step 4: Fetching option chain data
      updateStep('3', 'complete', 45)
      updateStep('4', 'loading', 50)

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('token')
        localStorage.removeItem('jwt_token')
        setToast({ message: 'Session expired. Please login again.', type: 'error' })
        setTimeout(() => {
          setToast(null)
          router.push('/login')
        }, 2000)
        return
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(errorData.detail || `Scan failed: ${response.statusText}`)
      }

      const data = await response.json()
      setScanResults(data)

      // Step 4 complete, Step 5: Analyzing data
      updateStep('4', 'complete', 60)
      updateStep('5', 'loading', 70)

      // Get actionable signal from backend (like old frontend does)
      // This returns the analyzed signal with exact strike, price, and calculated targets
      // Map frontend index names to backend symbol format
      const symbolMapping: Record<string, string> = {
        'NIFTY': 'NSE:NIFTY50-INDEX',
        'BANKNIFTY': 'NSE:NIFTYBANK-INDEX',
        'FINNIFTY': 'NSE:FINNIFTY-INDEX',
        'MIDCPNIFTY': 'NSE:MIDCPNIFTY-INDEX',
        'SENSEX': 'BSE:SENSEX-INDEX',
        'BANKEX': 'BSE:BANKEX-INDEX'
      }

      const symbol = symbolMapping[selectedIndex] || `NSE:${selectedIndex}-INDEX`
      const signalUrl = `${apiUrl}/signals/${encodeURIComponent(symbol)}/actionable`

      console.log(`🎯 Fetching actionable signal for ${selectedIndex} -> ${symbol}`)
      console.log(`📡 Signal URL: ${signalUrl}`)

      setLoadingMessage('Analyzing multi-timeframe trends...')

      // Step 5 complete, Step 6: Generating signals
      updateStep('5', 'complete', 80)
      updateStep('6', 'loading', 85)

      const signalResponse = await fetch(signalUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (signalResponse.ok) {
        const backendSignal = await signalResponse.json()

        // Step 6 complete
        updateStep('6', 'complete', 100)
        setLoadingProgress(100)

        // Map backend signal to frontend format
        // Use reversal_probability from setup_details as the numeric confidence (72% etc)
        // backendSignal.confidence is a string like "HIGH", "VERY HIGH" etc
        const numericConfidence = backendSignal.setup_details?.reversal_probability ||
          (backendSignal.confidence === 'VERY HIGH' ? 85 :
            backendSignal.confidence === 'HIGH' ? 72 :
              backendSignal.confidence === 'MODERATE' ? 55 :
                backendSignal.confidence === 'MEDIUM' ? 50 : 35)

        const tradingSignal: TradingSignal = {
          action: backendSignal.action,
          strike: backendSignal.option.strike,
          type: backendSignal.option.type,
          entry_price: backendSignal.entry.price,
          target_1: backendSignal.targets.target_1,
          target_2: backendSignal.targets.target_2,
          stop_loss: backendSignal.targets.stop_loss,
          risk_reward: backendSignal.risk_reward?.ratio_1 ? `1:${typeof backendSignal.risk_reward.ratio_1 === 'number' ? backendSignal.risk_reward.ratio_1.toFixed(1) : backendSignal.risk_reward.ratio_1}` : '1:2',
          confidence: numericConfidence,
          direction: backendSignal.signal_type || 'NEUTRAL',
          trading_symbol: backendSignal.option.symbol
        }

        setTradingSignal(tradingSignal)

        // Show success toast with backend signal info
        const direction = backendSignal.signal_type || 'NEUTRAL'
        const optionType = backendSignal.option.type
        setToast({
          message: `✅ Scan complete! ${direction} - Recommended: ${optionType} @ ${backendSignal.option.strike}`,
          type: 'success'
        })
      } else {
        // Fallback to manual calculation if backend signal fails
        const signal = calculateTradingSignal(data)
        setTradingSignal(signal)

        const direction = data.probability_analysis?.expected_direction || 'NEUTRAL'
        const optionType = data.recommended_option_type || 'N/A'
        setToast({
          message: `✅ Scan complete! ${direction} - Recommended: ${optionType} options`,
          type: 'success'
        })
      }

      setTimeout(() => setToast(null), 5000)

      // Don't redirect - show results on dashboard like old frontend

    } catch (error) {
      console.error('Scan error:', error)
      const errorMessage = error instanceof Error ? error.message : 'Scan failed. Please try again.'
      setToast({ message: errorMessage, type: 'error' })
      setTimeout(() => setToast(null), 4000)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Header
        user={user}
        selectedIndex={selectedIndex}
        onIndexChange={setSelectedIndex}
        onLogout={handleLogout}
      />

      <main className="container mx-auto px-3 md:px-4 py-4 md:py-6 space-y-4 md:space-y-6">
        {/* User Dashboard Header */}
        <Card className="bg-gradient-to-r from-primary/10 to-purple-500/10 border-primary/30">
          <CardContent className="p-4 md:p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 md:w-12 md:h-12 bg-primary rounded-full flex items-center justify-center">
                  <Users className="w-5 h-5 md:w-6 md:h-6 text-primary-foreground" />
                </div>
                <div>
                  <div className="text-xs md:text-sm text-muted-foreground">Your Personal Dashboard</div>
                  <div className="font-semibold text-primary text-sm md:text-base">
                    {user?.email || 'Guest User'}
                  </div>
                </div>
              </div>
              <StatsGrid columns={3} className="w-full md:w-auto">
                <StatCard title="Total Scans" value="24" variant="default" />
                <StatCard title="Active Signals" value="8" variant="bullish" />
                <StatCard title="Accuracy" value="76%" variant="neutral" />
              </StatsGrid>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4">
          <Link href="/screener" className="block">
            <Button variant="outline" className="w-full h-auto py-4 flex flex-col gap-2">
              <BarChart3 className="w-5 h-5 md:w-6 md:h-6" />
              <span className="text-xs md:text-sm">Stock Screener</span>
            </Button>
          </Link>
          <Link href="/options" className="block">
            <Button variant="outline" className="w-full h-auto py-4 flex flex-col gap-2">
              <Target className="w-5 h-5 md:w-6 md:h-6" />
              <span className="text-xs md:text-sm">Options Scanner</span>
            </Button>
          </Link>
          <Link href="/analyzer" className="block">
            <Button variant="outline" className="w-full h-auto py-4 flex flex-col gap-2">
              <TrendingUp className="w-5 h-5 md:w-6 md:h-6" />
              <span className="text-xs md:text-sm">Index Analyzer</span>
            </Button>
          </Link>
          <Button
            variant="default"
            className="w-full h-auto py-4 flex flex-col gap-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
            onClick={handleQuickScan}
            disabled={loading}
          >
            <Zap className="w-5 h-5 md:w-6 md:h-6" />
            <span className="text-xs md:text-sm font-semibold">Scan {selectedIndex}</span>
          </Button>
        </div>

        {/* ============ TRADING SIGNAL CARD - Like Old Dashboard ============ */}
        {tradingSignal && scanResults && (
          <Card className="border-2 border-primary/50 bg-gradient-to-br from-primary/5 to-purple-500/5">
            <CardHeader className="pb-3">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                  🎯 Trading Signal
                  <Badge className={tradingSignal.direction === 'BULLISH' ? 'bg-bullish' : tradingSignal.direction === 'BEARISH' ? 'bg-bearish' : 'bg-neutral'}>
                    {tradingSignal.direction}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {scanResults.data_source === 'live' ? '🟢 Live' : '🟡 Demo'}
                  </Badge>
                </CardTitle>
                <div className="text-xs text-muted-foreground">
                  {scanResults.index} | Expiry: {scanResults.market_data?.expiry_date || scanResults.expiry}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Action & Strike */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-card rounded-lg border">
                  <div className="text-xs text-muted-foreground mb-1">What to Buy</div>
                  <div className={`text-xl md:text-2xl font-bold ${tradingSignal.type === 'CALL' ? 'text-bullish' : 'text-bearish'}`}>
                    {tradingSignal.action}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {tradingSignal.strike} Strike
                  </div>
                </div>
                <div className="p-3 bg-card rounded-lg border">
                  <div className="text-xs text-muted-foreground mb-1">Entry Price</div>
                  <div className="text-xl md:text-2xl font-bold text-primary">
                    ₹{tradingSignal.entry_price.toFixed(2)}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Confidence: {tradingSignal.confidence}%
                  </div>
                </div>
              </div>

              {/* Targets & Stop Loss - Easy to understand */}
              <div className="grid grid-cols-4 gap-2">
                <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/30 text-center">
                  <div className="text-green-500 text-xs font-medium mb-1">🎯 TARGET 1</div>
                  <div className="text-lg font-bold text-green-500">₹{tradingSignal.target_1.toFixed(0)}</div>
                  <div className="text-xs text-green-400">
                    +{Math.round(((tradingSignal.target_1 - tradingSignal.entry_price) / tradingSignal.entry_price) * 100)}%
                  </div>
                </div>
                <div className="p-3 bg-green-600/10 rounded-lg border border-green-600/30 text-center">
                  <div className="text-green-500 text-xs font-medium mb-1">🎯 TARGET 2</div>
                  <div className="text-lg font-bold text-green-500">₹{tradingSignal.target_2.toFixed(0)}</div>
                  <div className="text-xs text-green-400">
                    +{Math.round(((tradingSignal.target_2 - tradingSignal.entry_price) / tradingSignal.entry_price) * 100)}%
                  </div>
                </div>
                <div className="p-3 bg-red-500/10 rounded-lg border border-red-500/30 text-center">
                  <div className="text-red-500 text-xs font-medium mb-1">🛑 STOP LOSS</div>
                  <div className="text-lg font-bold text-red-500">₹{tradingSignal.stop_loss.toFixed(0)}</div>
                  <div className="text-xs text-red-400">
                    -{Math.round(((tradingSignal.entry_price - tradingSignal.stop_loss) / tradingSignal.entry_price) * 100)}%
                  </div>
                </div>
                <div className="p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/30 text-center">
                  <div className="text-yellow-500 text-xs font-medium mb-1">⚖️ RISK:REWARD</div>
                  <div className="text-lg font-bold text-yellow-500">{tradingSignal.risk_reward}</div>
                  <div className="text-xs text-yellow-400">Favorable</div>
                </div>
              </div>

              {/* Trading Symbol & Simple Instructions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/30">
                  <div className="text-xs text-muted-foreground mb-1">Trading Symbol</div>
                  <div className="text-sm font-mono text-blue-400">{tradingSignal.trading_symbol}</div>
                </div>
                <div className="p-3 bg-orange-500/10 rounded-lg border border-orange-500/30">
                  <div className="text-xs text-muted-foreground mb-1">⏰ Day Trading Tip</div>
                  <div className="text-xs text-orange-300">Exit by 3:15 PM • Best entry: 9:30 AM - 2:00 PM</div>
                </div>
              </div>

              {/* Simple Explanation for Traders */}
              <div className="p-3 bg-primary/5 rounded-lg border border-primary/20">
                <div className="text-sm font-medium text-primary mb-1">📋 What This Means:</div>
                <div className="text-xs text-muted-foreground space-y-1">
                  <p>
                    • Based on analyzing {scanResults.probability_analysis?.stocks_scanned || 0} stocks,
                    the market looks <span className={tradingSignal.direction === 'BULLISH' ? 'text-green-500 font-semibold' : 'text-red-500 font-semibold'}>{tradingSignal.direction}</span>
                  </p>
                  <p>
                    • Buy <span className="text-primary font-semibold">{tradingSignal.trading_symbol}</span> at around ₹{tradingSignal.entry_price.toFixed(0)}
                  </p>
                  <p>
                    • Book profit at ₹{tradingSignal.target_1.toFixed(0)} or ₹{tradingSignal.target_2.toFixed(0)} • Exit if price drops to ₹{tradingSignal.stop_loss.toFixed(0)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Market Overview */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
              <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                <TrendingUp className="w-5 h-5 text-primary" />
                {selectedIndex} Overview
              </CardTitle>
              <div className="flex items-center gap-2">
                {scanResults && (
                  <Badge className={`text-xs ${scanResults.probability_analysis?.expected_direction === 'BULLISH' ? 'bg-bullish' :
                      scanResults.probability_analysis?.expected_direction === 'BEARISH' ? 'bg-bearish' : 'bg-neutral'
                    }`}>
                    {scanResults.probability_analysis?.expected_direction || 'N/A'}
                  </Badge>
                )}
                <Badge variant="outline" className="text-xs">
                  <span className="w-2 h-2 bg-bullish rounded-full mr-1 animate-pulse" />
                  Live
                </Badge>
                <span className="text-xs text-muted-foreground">
                  Updated: {mounted ? currentTime : '--:--:--'}
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <StatsGrid columns={4}>
              <StatCard
                title="Spot Price"
                value={scanResults?.market_data?.spot_price ? `₹${scanResults.market_data.spot_price.toLocaleString()}` : scanResults?.spot_price ? `₹${scanResults.spot_price.toLocaleString()}` : '--'}
                trend={scanResults?.probability_analysis?.expected_direction === 'BULLISH' ? 'up' : scanResults?.probability_analysis?.expected_direction === 'BEARISH' ? 'down' : undefined}
                trendValue={scanResults?.probability_analysis?.expected_move_pct ? `${scanResults.probability_analysis.expected_move_pct.toFixed(2)}%` : undefined}
                variant={scanResults?.probability_analysis?.expected_direction === 'BULLISH' ? 'bullish' : scanResults?.probability_analysis?.expected_direction === 'BEARISH' ? 'bearish' : 'default'}
              />
              <StatCard
                title="ATM Strike"
                value={scanResults?.market_data?.atm_strike ? `₹${scanResults.market_data.atm_strike.toLocaleString()}` : '--'}
                subtitle={scanResults?.market_data?.days_to_expiry ? `${scanResults.market_data.days_to_expiry} days to expiry` : ''}
              />
              <StatCard
                title="Stocks Analyzed"
                value={scanResults?.probability_analysis ? `${scanResults.probability_analysis.stocks_scanned}/${scanResults.probability_analysis.total_stocks}` : '--'}
                subtitle={scanResults?.probability_analysis?.market_regime || ''}
              />
              <StatCard
                title="Recommended"
                value={scanResults?.recommended_option_type || '--'}
                variant={scanResults?.recommended_option_type === 'CALL' ? 'bullish' : scanResults?.recommended_option_type === 'PUT' ? 'bearish' : 'default'}
              />
            </StatsGrid>

            <div className="mt-4 md:mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="p-4">
                <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                  📊 Probability Analysis
                  {scanResults?.probability_analysis && (
                    <Badge variant="outline" className="text-xs">
                      {scanResults.probability_analysis.stocks_scanned} stocks
                    </Badge>
                  )}
                </h4>
                <div className="space-y-3">
                  <ProbabilityBar
                    label="📈 Bullish"
                    value={scanResults?.probability_analysis?.probability_up ? scanResults.probability_analysis.probability_up * 100 : 0}
                    color="bullish"
                  />
                  <ProbabilityBar
                    label="📉 Bearish"
                    value={scanResults?.probability_analysis?.probability_down ? scanResults.probability_analysis.probability_down * 100 : 0}
                    color="bearish"
                  />
                </div>
                <div className="mt-3 pt-3 border-t space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Expected Direction</span>
                    <span className={`font-semibold ${scanResults?.probability_analysis?.expected_direction === 'BULLISH' ? 'text-bullish' :
                        scanResults?.probability_analysis?.expected_direction === 'BEARISH' ? 'text-bearish' : 'text-neutral'
                      }`}>
                      {scanResults?.probability_analysis?.expected_direction === 'BULLISH' && '📈 '}
                      {scanResults?.probability_analysis?.expected_direction === 'BEARISH' && '📉 '}
                      {scanResults?.probability_analysis?.expected_direction === 'NEUTRAL' && '➖ '}
                      {scanResults?.probability_analysis?.expected_direction || 'Run scan to analyze'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Expected Move</span>
                    <span className={`font-semibold ${(scanResults?.probability_analysis?.expected_move_pct || 0) > 0 ? 'text-bullish' : 'text-bearish'
                      }`}>
                      {scanResults?.probability_analysis?.expected_move_pct
                        ? `${scanResults.probability_analysis.expected_move_pct > 0 ? '+' : ''}${scanResults.probability_analysis.expected_move_pct.toFixed(2)}%`
                        : '--'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Signal Confidence</span>
                    <span className="font-semibold text-primary">
                      {tradingSignal?.confidence
                        ? `${tradingSignal.confidence}%`
                        : scanResults?.probability_analysis?.confidence
                          ? `${(scanResults.probability_analysis.confidence * 100).toFixed(0)}%`
                          : '--'}
                    </span>
                  </div>
                </div>
              </Card>

              <Card className="p-4">
                <h4 className="text-sm font-medium mb-3">Constituent Sentiment</h4>
                <SentimentGauge
                  bullish={scanResults?.probability_analysis?.bullish_stocks || 0}
                  bearish={scanResults?.probability_analysis?.bearish_stocks || 0}
                />
                <div className="mt-3 text-xs text-muted-foreground text-center">
                  {scanResults?.probability_analysis
                    ? `Based on ${scanResults.probability_analysis.stocks_scanned} ${selectedIndex} stocks`
                    : `Click "Scan ${selectedIndex}" to analyze constituent stocks`}
                </div>
                {scanResults?.probability_analysis && (
                  <div className="mt-3 pt-3 border-t grid grid-cols-3 gap-2 text-center text-xs">
                    <div>
                      <div className="text-bullish font-bold">{scanResults.probability_analysis.bullish_stocks}</div>
                      <div className="text-muted-foreground">Bullish</div>
                    </div>
                    <div>
                      <div className="text-neutral font-bold">{scanResults.probability_analysis.total_stocks - scanResults.probability_analysis.bullish_stocks - scanResults.probability_analysis.bearish_stocks || 0}</div>
                      <div className="text-muted-foreground">Neutral</div>
                    </div>
                    <div>
                      <div className="text-bearish font-bold">{scanResults.probability_analysis.bearish_stocks}</div>
                      <div className="text-muted-foreground">Bearish</div>
                    </div>
                  </div>
                )}
              </Card>
            </div>

            {/* Top Movers Section - Like Old Dashboard */}
            {scanResults?.probability_analysis && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Top Bullish Stocks */}
                <Card className="p-4 border-green-500/20">
                  <h4 className="text-sm font-medium mb-3 flex items-center gap-2 text-green-500">
                    📈 Top Bullish Stocks
                    <Badge variant="outline" className="text-xs text-green-400 border-green-500/30">
                      Likely to go UP
                    </Badge>
                  </h4>
                  <div className="space-y-2">
                    {scanResults.probability_analysis.top_bullish_stocks && scanResults.probability_analysis.top_bullish_stocks.length > 0 ? (
                      scanResults.probability_analysis.top_bullish_stocks.slice(0, 5).map((stock, idx) => (
                        <div key={stock.symbol} className="flex justify-between items-center p-2 bg-green-500/5 rounded border border-green-500/20">
                          <span className="text-sm font-medium text-green-400">{stock.symbol}</span>
                          <div className="text-right">
                            <span className="text-xs text-green-500 font-bold">{(stock.probability * 100).toFixed(0)}%</span>
                            <span className="text-xs text-muted-foreground ml-2">
                              {stock.expected_move > 0 ? '+' : ''}{stock.expected_move.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-xs text-muted-foreground text-center py-4">No strong bullish signals</div>
                    )}
                  </div>
                </Card>

                {/* Top Bearish Stocks */}
                <Card className="p-4 border-red-500/20">
                  <h4 className="text-sm font-medium mb-3 flex items-center gap-2 text-red-500">
                    📉 Top Bearish Stocks
                    <Badge variant="outline" className="text-xs text-red-400 border-red-500/30">
                      Likely to go DOWN
                    </Badge>
                  </h4>
                  <div className="space-y-2">
                    {scanResults.probability_analysis.top_bearish_stocks && scanResults.probability_analysis.top_bearish_stocks.length > 0 ? (
                      scanResults.probability_analysis.top_bearish_stocks.slice(0, 5).map((stock, idx) => (
                        <div key={stock.symbol} className="flex justify-between items-center p-2 bg-red-500/5 rounded border border-red-500/20">
                          <span className="text-sm font-medium text-red-400">{stock.symbol}</span>
                          <div className="text-right">
                            <span className="text-xs text-red-500 font-bold">{(stock.probability * 100).toFixed(0)}%</span>
                            <span className="text-xs text-muted-foreground ml-2">
                              {stock.expected_move > 0 ? '+' : ''}{stock.expected_move.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-xs text-muted-foreground text-center py-4">No strong bearish signals</div>
                    )}
                  </div>
                </Card>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Scan Results - Options */}
        {scanResults?.options && scanResults.options.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <CardTitle className="flex items-center gap-2 flex-wrap text-base md:text-lg">
                  <span>🎯</span>
                  Options Scan Results
                  <Badge className={scanResults.recommended_option_type === 'CALL' ? 'bg-bullish' : 'bg-bearish'}>
                    {scanResults.recommended_option_type} Recommended
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {scanResults.options.length} options found
                  </Badge>
                </CardTitle>
                <div className="text-xs text-muted-foreground">
                  {scanResults.index} | Expiry: {scanResults.expiry}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[300px] md:h-[400px]">
                <div className="space-y-2">
                  {scanResults.options.slice(0, 20).map((option: OptionResult, index: number) => {
                    const optType = option.type === 'CE' ? 'CE' : option.type === 'PE' ? 'PE' : option.type === 'CALL' ? 'CE' : 'PE'
                    const isCall = optType === 'CE' || option.type === 'CALL'
                    const isBoosted = option.probability_boost

                    return (
                      <div
                        key={`${option.symbol || option.strike}-${index}`}
                        className={`p-3 rounded-lg border ${isCall ? 'border-bullish/30 bg-bullish/5' : 'border-bearish/30 bg-bearish/5'
                          } ${isBoosted ? 'ring-2 ring-purple-500/50' : ''}`}
                      >
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                          <div className="flex items-center gap-3">
                            <Badge className={isCall ? 'bg-bullish' : 'bg-bearish'}>
                              {optType}
                            </Badge>
                            <div>
                              <div className="font-semibold text-sm">{option.strike}</div>
                              {option.symbol && <div className="text-xs text-muted-foreground">{option.symbol}</div>}
                            </div>
                            {isBoosted && (
                              <Badge className="bg-purple-600 text-xs">⚡ RECOMMENDED</Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-4 text-sm">
                            <div className="text-right">
                              <div className="font-semibold">₹{option.ltp?.toFixed(2)}</div>
                              {option.change_pct !== undefined && (
                                <div className={`text-xs ${option.change_pct >= 0 ? 'text-bullish' : 'text-bearish'
                                  }`}>
                                  {option.change_pct >= 0 ? '+' : ''}{option.change_pct?.toFixed(2)}%
                                </div>
                              )}
                            </div>
                            <div className="text-right text-xs text-muted-foreground">
                              <div>Vol: {(option.volume / 1000).toFixed(0)}K</div>
                              <div>OI: {(option.oi / 1000).toFixed(0)}K</div>
                            </div>
                            {option.iv && (
                              <div className="text-right text-xs">
                                <div className="text-muted-foreground">IV</div>
                                <div className="font-medium">{option.iv.toFixed(1)}%</div>
                              </div>
                            )}
                            {option.score !== undefined && (
                              <div className="text-right text-xs">
                                <div className="text-muted-foreground">Score</div>
                                <div className={`font-medium ${option.score >= 80 ? 'text-green-500' : option.score >= 60 ? 'text-yellow-500' : 'text-muted-foreground'}`}>
                                  {option.score.toFixed(0)}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </ScrollArea>
              {scanResults.options.length > 20 && (
                <div className="mt-3 text-center">
                  <Link href={`/options?index=${selectedIndex}`}>
                    <Button variant="outline" size="sm">
                      View all {scanResults.options.length} options
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Your Stock Signals */}
        <Card>
          <CardHeader>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
              <CardTitle className="flex items-center gap-2 flex-wrap text-base md:text-lg">
                <span>📊</span>
                Your Stock Signals
                <Badge variant="secondary" className="text-xs">Last 7 Days</Badge>
                <Badge className="text-xs">PERSONAL</Badge>
              </CardTitle>
              <div className="flex gap-2 flex-wrap">
                <select className="h-9 rounded-md border border-input bg-background px-3 text-xs md:text-sm">
                  <option value="all">All Signals</option>
                  <option value="buy">BUY Only</option>
                  <option value="sell">SELL Only</option>
                  <option value="high">High Confidence (≥80%)</option>
                </select>
                <Link href="/screener">
                  <Button size="sm" className="text-xs md:text-sm">New Scan</Button>
                </Link>
                <Button variant="outline" size="sm" className="text-xs md:text-sm">
                  <RefreshCw className="w-4 h-4 mr-1" />
                  Refresh
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {/* Signal Summary Stats */}
            <StatsGrid columns={4} className="mb-4">
              <StatCard title="BUY Signals" value="5" variant="bullish" />
              <StatCard title="SELL Signals" value="3" variant="bearish" />
              <StatCard title="Avg Confidence" value="76%" variant="default" />
              <StatCard title="Unique Stocks" value="8" variant="neutral" />
            </StatsGrid>

            {/* Signal Grid */}
            <SignalGrid signals={signals} compact />
          </CardContent>
        </Card>

        {/* Tabs for different sections */}
        <Tabs defaultValue="chain" className="w-full">
          <TabsList className="w-full md:w-auto overflow-x-auto scrollbar-hide">
            <TabsTrigger value="chain" className="text-xs md:text-sm">Option Chain</TabsTrigger>
            <TabsTrigger value="analysis" className="text-xs md:text-sm">Market Analysis</TabsTrigger>
            <TabsTrigger value="scanner" className="text-xs md:text-sm">Options Scanner</TabsTrigger>
          </TabsList>
          <TabsContent value="chain" className="mt-4">
            <Card>
              <CardContent className="p-4 md:p-6">
                <div className="text-center text-muted-foreground py-8">
                  Option chain data will load here...
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="analysis" className="mt-4">
            <Card>
              <CardContent className="p-4 md:p-6">
                <div className="text-center text-muted-foreground py-8">
                  Market analysis will load here...
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="scanner" className="mt-4">
            <Card>
              <CardContent className="p-4 md:p-6">
                <div className="text-center text-muted-foreground py-8">
                  Options scanner will load here...
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* Loading handled by LoadingModal component below */}

      {/* Toast Notification */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg ${toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'
          } text-white`}>
          {toast.message}
        </div>
      )}

      <LoadingModal
        open={loading}
        title={loadingMessage}
        progress={loadingProgress}
        steps={loadingSteps}
      />
    </div>
  )
}
