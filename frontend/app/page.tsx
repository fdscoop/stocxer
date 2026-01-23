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
  // Enhanced fields
  discount_zone?: {
    best_entry?: number
    status?: string
    current_price?: number
    iv_comparison?: string
    analysis?: string
  }
  liquidity_score?: number
  liquidity_grade?: string
  sentiment_score?: number
  sentiment_direction?: string
  market_mood?: string
  news_articles?: number
  reversal_detected?: boolean
  reversal_type?: string
  reversal_description?: string
  mtf_bias?: string
  confidence_adjustments?: {
    base_probability?: number
    constituent_boost?: number
    futures_conflict?: number
    ml_neutral_penalty?: number
    final_probability?: number
  }
  entry_analysis?: any
  raw_ltp?: number
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
  mtf_ict_analysis?: {
    overall_bias: string
    timeframes: {
      [key: string]: {
        bias: string
        structure: string
        candles?: number
      }
    }
  }
}

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = React.useState<{ email: string } | null>(null)
  const [selectedIndex, setSelectedIndex] = React.useState('NIFTY')
  const [signals, setSignals] = React.useState<Signal[]>([])
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

  // Calculate trading signal from scan results with improved entry analysis
  const calculateTradingSignal = (data: ScanResults): TradingSignal | null => {
    if (!data.probability_analysis || !data.options || data.options.length === 0) return null

    const prob = data.probability_analysis
    const recommendedType = data.recommended_option_type || 'CALL'

    // Find the BEST option considering entry quality
    // Priority: probability_boost = true AND entry_grade is A or B
    let bestOption = data.options.find(opt => {
      const entryAnalysis = (opt as any).entry_analysis
      const hasGoodEntry = entryAnalysis && ['A', 'B'].includes(entryAnalysis.entry_grade)
      return opt.probability_boost === true && hasGoodEntry
    })

    // Fallback 1: Find any probability_boost option
    if (!bestOption) {
      bestOption = data.options.find(opt => opt.probability_boost === true)
    }

    // Fallback 2: Find the best option matching the recommendation type with good entry
    if (!bestOption) {
      const matchingOptions = data.options.filter(opt => {
        const optType = opt.type === 'CE' ? 'CALL' : opt.type === 'PE' ? 'PUT' : opt.type
        return optType === recommendedType
      })

      // Sort by entry grade first, then by score
      bestOption = matchingOptions.sort((a, b) => {
        const aEntry = (a as any).entry_analysis
        const bEntry = (b as any).entry_analysis
        const aGrade = aEntry?.entry_grade || 'D'
        const bGrade = bEntry?.entry_grade || 'D'
        const gradeOrder = { 'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0 }
        const gradeDiff = (gradeOrder[bGrade as keyof typeof gradeOrder] || 0) - (gradeOrder[aGrade as keyof typeof gradeOrder] || 0)
        if (gradeDiff !== 0) return gradeDiff
        return (b.score || 0) - (a.score || 0)
      })[0] || data.options[0]
    }

    // Get entry analysis data
    const entryAnalysis = (bestOption as any).entry_analysis || {}
    const discountZone = (bestOption as any).discount_zone || {}
    
    // Use RECOMMENDED entry price, not just LTP
    const rawLtp = bestOption.ltp
    const recommendedEntry = entryAnalysis.recommended_entry || rawLtp
    const limitOrderPrice = entryAnalysis.limit_order_price || rawLtp
    const maxAcceptablePrice = entryAnalysis.max_acceptable_price || rawLtp * 1.02
    const entryGrade = entryAnalysis.entry_grade || 'C'
    const entryRecommendation = entryAnalysis.entry_recommendation || 'BUY'
    const shouldWaitForPullback = entryAnalysis.wait_for_pullback || false
    const supportsImmediateEntry = entryAnalysis.supports_immediate_entry !== false
    const entryReasons: string[] = entryAnalysis.reasoning || []
    
    // Use limit order price if waiting for pullback, otherwise use LTP
    const entryPrice = shouldWaitForPullback ? limitOrderPrice : rawLtp
    const optionType = bestOption.type === 'CE' ? 'CALL' : bestOption.type === 'PE' ? 'PUT' : bestOption.type

    // Calculate realistic targets using Greeks-based projections if available
    const delta = bestOption.delta || 0.4
    const dte = data.market_data?.days_to_expiry || 7
    
    // Target calculation based on expected underlying move and delta
    // More sophisticated than arbitrary percentage multipliers
    let target1Points: number
    let target2Points: number
    let stopLossPoints: number
    
    // For intraday, expect 0.5-1% index move = proportional option move via delta
    const expectedIndexMovePct = prob.expected_move_pct || 0.5
    const spotPrice = data.market_data?.spot_price || 24000
    const expectedIndexPoints = spotPrice * expectedIndexMovePct / 100
    
    // Option price change ≈ Delta × Underlying price change
    const expectedOptionMove = Math.abs(delta) * expectedIndexPoints
    
    // Set targets based on expected move
    target1Points = Math.max(expectedOptionMove * 0.6, rawLtp * 0.20) // Min 20% or 60% of expected
    target2Points = Math.max(expectedOptionMove * 1.2, rawLtp * 0.50) // Min 50% or 120% of expected
    stopLossPoints = Math.min(rawLtp * 0.25, expectedOptionMove * 0.5) // Max 25% or 50% of expected
    
    // Adjust for time decay if close to expiry
    if (dte <= 2) {
      // Reduce targets due to theta decay
      target1Points *= 0.8
      target2Points *= 0.7
      // Tighter stop loss to limit time decay damage
      stopLossPoints *= 0.8
    }
    
    const target1 = Math.round((entryPrice + target1Points) * 100) / 100
    const target2 = Math.round((entryPrice + target2Points) * 100) / 100
    const stopLoss = Math.round((entryPrice - stopLossPoints) * 100) / 100

    // Calculate risk-reward ratio
    const risk = entryPrice - stopLoss
    const reward1 = target1 - entryPrice
    const riskReward = risk > 0 ? `1:${(reward1 / risk).toFixed(1)}` : '1:2'

    // Determine action based on entry recommendation
    let action: string
    if (!supportsImmediateEntry || entryRecommendation === 'AVOID') {
      action = `AVOID ${optionType}`
    } else if (shouldWaitForPullback || entryRecommendation === 'WAIT') {
      action = `WAIT ${optionType}`
    } else if (entryRecommendation === 'LIMIT_ORDER') {
      action = `LIMIT ${optionType}`
    } else {
      action = recommendedType === 'CALL' ? 'BUY CALL' : recommendedType === 'PUT' ? 'BUY PUT' : 'STRADDLE'
    }
    
    const direction = prob.expected_direction

    // Calculate confidence - factor in entry grade
    const gradeBonus = { 'A': 15, 'B': 10, 'C': 0, 'D': -10, 'F': -20 }
    let confidence = Math.round(prob.confidence * 100) + (gradeBonus[entryGrade as keyof typeof gradeBonus] || 0)
    confidence = Math.max(0, Math.min(100, confidence))

    // Build trading symbol
    const indexSymbol = data.index || 'NIFTY'
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
      trading_symbol: tradingSymbol,
      // Extended fields for UI
      entry_grade: entryGrade,
      raw_ltp: rawLtp,
      limit_order_price: limitOrderPrice,
      max_acceptable_price: maxAcceptablePrice,
      wait_for_pullback: shouldWaitForPullback,
      entry_reasons: entryReasons,
      time_feasible: entryAnalysis.time_feasible !== false,
      time_remaining_minutes: entryAnalysis.time_remaining_minutes || 0,
      theta_per_hour: entryAnalysis.theta_impact_per_hour || 0,
    } as any
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
      // Check Fyers authentication status on page load
      checkFyersAuth(token)
    } else {
      // Redirect to landing page if not authenticated
      router.push('/landing')
    }

    // Listen for messages from Fyers callback popup
    const handleMessage = (event: MessageEvent) => {
      // Handle auth token requests from popup
      if (event.data.type === 'get_auth_token') {
        const authToken = localStorage.getItem('token') || localStorage.getItem('jwt_token')
        event.source?.postMessage({ 
          type: 'auth_token_response', 
          token: authToken 
        }, event.origin as any)
      }
      
      // Handle Fyers auth completion
      if (event.data.type === 'fyers_auth_complete') {
        if (event.data.success) {
          setToast({ message: '✅ Fyers authentication successful!', type: 'success' })
          setTimeout(() => setToast(null), 3000)
          // Refresh auth status
          const authToken = localStorage.getItem('token') || localStorage.getItem('jwt_token')
          if (authToken) {
            checkFyersAuth(authToken)
          }
        } else {
          setToast({ message: `❌ Fyers auth failed: ${event.data.error}`, type: 'error' })
          setTimeout(() => setToast(null), 5000)
        }
      }
    }
    
    window.addEventListener('message', handleMessage)

    return () => {
      clearInterval(timer)
      window.removeEventListener('message', handleMessage)
    }
  }, [router])

  // Check Fyers authentication status
  const checkFyersAuth = async (token: string) => {
    try {
      const apiUrl = getApiUrl()
      const response = await fetch(`${apiUrl}/api/fyers/token`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        console.log('✅ Fyers token found:', data)
        // Refresh the server's Fyers client with this token
        await fetch(`${apiUrl}/api/fyers/refresh-token`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
      } else {
        console.warn('⚠️ Fyers authentication required for live data')
        // Show a toast notification about Fyers auth
        setToast({ 
          message: 'Fyers authentication required for live market data. Please connect your Fyers account.', 
          type: 'error' 
        })
        setTimeout(() => setToast(null), 5000)
      }
    } catch (error) {
      console.error('Error checking Fyers auth:', error)
    }
  }

  // Open Fyers authentication popup
  const openFyersAuthPopup = async () => {
    try {
      const apiUrl = getApiUrl()
      const response = await fetch(`${apiUrl}/auth/url`)
      const data = await response.json()

      // Open in popup for better UX
      const popup = window.open(
        data.auth_url,
        'fyersAuth',
        'width=600,height=700,scrollbars=yes,resizable=yes'
      )

      // Check for popup completion
      const checkClosed = setInterval(() => {
        if (popup && popup.closed) {
          clearInterval(checkClosed)
          // Refresh auth status after popup closes
          const token = localStorage.getItem('token') || localStorage.getItem('jwt_token')
          if (token) {
            setTimeout(() => {
              checkFyersAuth(token)
              setToast({ message: 'Fyers authentication completed!', type: 'success' })
              setTimeout(() => setToast(null), 3000)
            }, 1000)
          }
        }
      }, 1000)
    } catch (error) {
      console.error('Auth error:', error)
      setToast({ message: 'Failed to start authentication. Please try again.', type: 'error' })
      setTimeout(() => setToast(null), 3000)
    }
  }

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
          trading_symbol: backendSignal.option.symbol,
          // Enhanced fields from backend
          discount_zone: backendSignal.discount_zone || {},
          liquidity_score: backendSignal.liquidity?.liquidity_score,
          liquidity_grade: backendSignal.liquidity?.liquidity_grade,
          sentiment_score: backendSignal.sentiment_analysis?.sentiment_score,
          sentiment_direction: backendSignal.sentiment_analysis?.sentiment_direction,
          market_mood: backendSignal.sentiment_analysis?.market_mood,
          news_articles: backendSignal.sentiment_analysis?.news_articles_retrieved,
          reversal_detected: backendSignal.reversal_detection?.detected,
          reversal_type: backendSignal.reversal_detection?.type,
          reversal_description: backendSignal.reversal_detection?.description,
          mtf_bias: backendSignal.mtf_ict_analysis?.overall_bias,
          confidence_adjustments: backendSignal.confidence_adjustments,
          entry_analysis: backendSignal.entry_analysis,
          raw_ltp: backendSignal.pricing?.ltp
        } as TradingSignal

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
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 md:gap-4">
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
            variant="outline"
            className="w-full h-auto py-4 flex flex-col gap-2 border-orange-500/50 hover:border-orange-500 hover:bg-orange-500/10"
            onClick={openFyersAuthPopup}
          >
            <span className="text-lg">🔑</span>
            <span className="text-xs md:text-sm">Fyers Auth</span>
          </Button>
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
                  {/* Entry Grade Badge */}
                  <Badge 
                    variant="outline" 
                    className={`text-xs ${
                      (tradingSignal as any).entry_grade === 'A' ? 'border-green-500 text-green-500' :
                      (tradingSignal as any).entry_grade === 'B' ? 'border-lime-500 text-lime-500' :
                      (tradingSignal as any).entry_grade === 'C' ? 'border-yellow-500 text-yellow-500' :
                      (tradingSignal as any).entry_grade === 'D' ? 'border-orange-500 text-orange-500' :
                      'border-red-500 text-red-500'
                    }`}
                  >
                    Entry: {(tradingSignal as any).entry_grade || 'C'}
                  </Badge>
                </CardTitle>
                <div className="text-xs text-muted-foreground">
                  {scanResults.index} | Expiry: {scanResults.market_data?.expiry_date || scanResults.expiry}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* WAIT/AVOID Warning if applicable */}
              {(tradingSignal.action.includes('WAIT') || tradingSignal.action.includes('AVOID')) && (
                <div className={`p-3 rounded-lg border ${
                  tradingSignal.action.includes('AVOID') 
                    ? 'bg-red-500/10 border-red-500/30' 
                    : 'bg-orange-500/10 border-orange-500/30'
                }`}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xl">{tradingSignal.action.includes('AVOID') ? '⛔' : '⏳'}</span>
                    <span className={`font-semibold ${tradingSignal.action.includes('AVOID') ? 'text-red-500' : 'text-orange-500'}`}>
                      {tradingSignal.action.includes('AVOID') ? 'Avoid Entry - Poor Conditions' : 'Wait for Better Entry'}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground space-y-1">
                    {((tradingSignal as any).entry_reasons || []).slice(0, 3).map((reason: string, idx: number) => (
                      <p key={idx}>{reason}</p>
                    ))}
                    {(tradingSignal as any).wait_for_pullback && (
                      <p className="text-orange-400 font-medium">
                        💡 Wait for pullback to ₹{(tradingSignal as any).limit_order_price?.toFixed(0) || tradingSignal.entry_price.toFixed(0)}
                      </p>
                    )}
                  </div>
                </div>
              )}
              
              {/* Action & Strike */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-card rounded-lg border">
                  <div className="text-xs text-muted-foreground mb-1">What to Buy</div>
                  <div className={`text-xl md:text-2xl font-bold ${
                    tradingSignal.action.includes('AVOID') ? 'text-red-500' :
                    tradingSignal.action.includes('WAIT') ? 'text-orange-500' :
                    tradingSignal.type === 'CALL' ? 'text-bullish' : 'text-bearish'
                  }`}>
                    {tradingSignal.action}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {tradingSignal.strike} Strike
                  </div>
                </div>
                <div className="p-3 bg-card rounded-lg border">
                  <div className="text-xs text-muted-foreground mb-1">
                    {(tradingSignal as any).wait_for_pullback ? 'Limit Order Price' : 'Entry Price'}
                  </div>
                  <div className="text-xl md:text-2xl font-bold text-primary">
                    ₹{tradingSignal.entry_price.toFixed(2)}
                  </div>
                  {/* Show current LTP if different from entry */}
                  {(tradingSignal as any).raw_ltp && Math.abs((tradingSignal as any).raw_ltp - tradingSignal.entry_price) > 0.5 && (
                    <div className="text-xs text-muted-foreground">
                      Current LTP: ₹{(tradingSignal as any).raw_ltp?.toFixed(2)}
                    </div>
                  )}
                  <div className="text-sm text-muted-foreground">
                    Confidence: {tradingSignal.confidence}%
                  </div>
                </div>
              </div>

              {/* Time & Theta Warning for Intraday */}
              {((tradingSignal as any).time_remaining_minutes < 120 || (tradingSignal as any).theta_per_hour > 2) && (
                <div className="grid grid-cols-2 gap-2">
                  {(tradingSignal as any).time_remaining_minutes < 120 && (
                    <div className="p-2 bg-yellow-500/10 rounded-lg border border-yellow-500/30 text-center">
                      <div className="text-yellow-500 text-xs font-medium">⏰ Time Left</div>
                      <div className="text-sm font-bold text-yellow-500">
                        {Math.floor((tradingSignal as any).time_remaining_minutes / 60)}h {(tradingSignal as any).time_remaining_minutes % 60}m
                      </div>
                    </div>
                  )}
                  {(tradingSignal as any).theta_per_hour > 2 && (
                    <div className="p-2 bg-red-500/10 rounded-lg border border-red-500/30 text-center">
                      <div className="text-red-500 text-xs font-medium">📉 Theta Decay</div>
                      <div className="text-sm font-bold text-red-500">
                        -₹{(tradingSignal as any).theta_per_hour?.toFixed(1)}/hr
                      </div>
                    </div>
                  )}
                </div>
              )}

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

              {/* Enhanced Entry Analysis & Liquidity */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/30">
                  <div className="text-xs text-muted-foreground mb-1">Trading Symbol</div>
                  <div className="text-sm font-mono text-blue-400">{tradingSignal.trading_symbol}</div>
                </div>
                
                {/* Best Entry Price from Discount Zone */}
                {(tradingSignal as any).discount_zone?.best_entry && (
                  <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/30">
                    <div className="text-xs text-muted-foreground mb-1">💎 Best Entry Price</div>
                    <div className="text-lg font-bold text-green-400">
                      ₹{(tradingSignal as any).discount_zone.best_entry.toFixed(2)}
                    </div>
                    <div className="text-xs text-green-300">
                      {(tradingSignal as any).discount_zone.status || 'OPTIMAL'}
                    </div>
                  </div>
                )}
                
                {/* Liquidity Score */}
                {(tradingSignal as any).liquidity_score !== undefined && (
                  <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/30">
                    <div className="text-xs text-muted-foreground mb-1">💧 Liquidity</div>
                    <div className="text-lg font-bold text-purple-400">
                      {(tradingSignal as any).liquidity_score}/100
                    </div>
                    <div className="text-xs text-purple-300">
                      {(tradingSignal as any).liquidity_grade || 'EXCELLENT'}
                    </div>
                  </div>
                )}
              </div>

              {/* Sentiment & Reversal Detection */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* Sentiment Analysis */}
                {(tradingSignal as any).sentiment_score !== undefined && (
                  <div className="p-3 bg-cyan-500/10 rounded-lg border border-cyan-500/30">
                    <div className="text-xs text-muted-foreground mb-1 flex items-center gap-2">
                      📰 Market Sentiment
                      {(tradingSignal as any).news_articles && (
                        <span className="text-xs bg-cyan-600/30 px-1 rounded">
                          {(tradingSignal as any).news_articles} articles
                        </span>
                      )}
                    </div>
                    <div className="text-sm font-semibold text-cyan-400">
                      {(tradingSignal as any).sentiment_direction?.toUpperCase() || 'NEUTRAL'}
                    </div>
                    <div className="text-xs text-cyan-300 mt-1">
                      {(tradingSignal as any).market_mood || 'Analyzing market mood...'}
                    </div>
                  </div>
                )}
                
                {/* Reversal Detection */}
                {(tradingSignal as any).reversal_detected && (
                  <div className="p-3 bg-orange-500/10 rounded-lg border border-orange-500/30">
                    <div className="text-xs text-muted-foreground mb-1">🔄 Reversal Signal</div>
                    <div className="text-sm font-semibold text-orange-400">
                      {(tradingSignal as any).reversal_type?.replace('_', ' ') || 'DETECTED'}
                    </div>
                    <div className="text-xs text-orange-300 mt-1 line-clamp-2">
                      {(tradingSignal as any).reversal_description || 'Potential trend reversal'}
                    </div>
                  </div>
                )}
              </div>
              
              {/* Day Trading Tips */}
              <div className="p-3 bg-orange-500/10 rounded-lg border border-orange-500/30">
                <div className="text-xs text-muted-foreground mb-1">⏰ Day Trading Tips</div>
                <div className="text-xs text-orange-300 space-y-1">
                  <p>• Exit by 3:15 PM • Best entry: 9:30 AM - 2:00 PM</p>
                  {(tradingSignal as any).discount_zone?.analysis && (
                    <p>• {(tradingSignal as any).discount_zone.analysis}</p>
                  )}
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
                    • {(tradingSignal as any).wait_for_pullback 
                      ? <>Place limit order for <span className="text-primary font-semibold">{tradingSignal.trading_symbol}</span> at ₹{tradingSignal.entry_price.toFixed(0)} (current: ₹{(tradingSignal as any).raw_ltp?.toFixed(0)})</>
                      : <>Buy <span className="text-primary font-semibold">{tradingSignal.trading_symbol}</span> at around ₹{tradingSignal.entry_price.toFixed(0)}</>
                    }
                  </p>
                  <p>
                    • Book profit at ₹{tradingSignal.target_1.toFixed(0)} or ₹{tradingSignal.target_2.toFixed(0)} • Exit if price drops to ₹{tradingSignal.stop_loss.toFixed(0)}
                  </p>
                  {/* Entry Quality Note */}
                  {(tradingSignal as any).entry_grade && (
                    <p className={`font-medium ${
                      ['A', 'B'].includes((tradingSignal as any).entry_grade) ? 'text-green-500' :
                      (tradingSignal as any).entry_grade === 'C' ? 'text-yellow-500' : 'text-red-500'
                    }`}>
                      • Entry Quality: Grade {(tradingSignal as any).entry_grade} 
                      {['A', 'B'].includes((tradingSignal as any).entry_grade) ? ' - Good conditions for entry' : 
                       (tradingSignal as any).entry_grade === 'C' ? ' - Average, proceed with caution' : ' - Consider waiting'}
                    </p>
                  )}
                </div>
              </div>
              
              {/* Confidence Breakdown - Show how probability was calculated */}
              {(tradingSignal as any).confidence_adjustments && (
                <div className="p-3 bg-slate-500/10 rounded-lg border border-slate-500/30">
                  <div className="text-sm font-medium text-slate-300 mb-2">📊 Confidence Breakdown</div>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-muted-foreground">Base Probability:</span>
                      <span className="font-semibold text-slate-300">
                        {(tradingSignal as any).confidence_adjustments.base_probability?.toFixed(1)}%
                      </span>
                    </div>
                    {(tradingSignal as any).confidence_adjustments.constituent_boost !== 0 && (
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-muted-foreground">Constituent Alignment:</span>
                        <span className={`font-semibold ${(tradingSignal as any).confidence_adjustments.constituent_boost > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {(tradingSignal as any).confidence_adjustments.constituent_boost > 0 ? '+' : ''}
                          {(tradingSignal as any).confidence_adjustments.constituent_boost?.toFixed(1)}%
                        </span>
                      </div>
                    )}
                    {(tradingSignal as any).confidence_adjustments.futures_conflict !== 0 && (
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-muted-foreground">Futures Analysis:</span>
                        <span className={`font-semibold ${(tradingSignal as any).confidence_adjustments.futures_conflict > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {(tradingSignal as any).confidence_adjustments.futures_conflict > 0 ? '+' : ''}
                          {(tradingSignal as any).confidence_adjustments.futures_conflict?.toFixed(1)}%
                        </span>
                      </div>
                    )}
                    {(tradingSignal as any).confidence_adjustments.ml_neutral_penalty !== 0 && (
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-muted-foreground">ML Adjustment:</span>
                        <span className={`font-semibold ${(tradingSignal as any).confidence_adjustments.ml_neutral_penalty > 0 ? 'text-green-400' : 'text-orange-400'}`}>
                          {(tradingSignal as any).confidence_adjustments.ml_neutral_penalty > 0 ? '+' : ''}
                          {(tradingSignal as any).confidence_adjustments.ml_neutral_penalty?.toFixed(1)}%
                        </span>
                      </div>
                    )}
                    <div className="h-px bg-slate-500/30 my-2"></div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-300 font-semibold">Final Confidence:</span>
                      <span className="font-bold text-primary text-base">
                        {(tradingSignal as any).confidence_adjustments.final_probability?.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
        
        {/* Multi-Timeframe Analysis Summary */}
        {(tradingSignal as any)?.mtf_bias && scanResults?.mtf_ict_analysis && (
          <Card className="border-slate-500/30">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                📈 Multi-Timeframe Analysis
                <Badge variant="outline" className={`text-xs ${
                  (tradingSignal as any).mtf_bias === 'bullish' ? 'border-green-500 text-green-500' :
                  (tradingSignal as any).mtf_bias === 'bearish' ? 'border-red-500 text-red-500' :
                  'border-yellow-500 text-yellow-500'
                }`}>
                  Overall: {(tradingSignal as any).mtf_bias?.toUpperCase()}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
                {Object.entries(scanResults.mtf_ict_analysis.timeframes || {}).map(([tf, data]: [string, any]) => (
                  <div key={tf} className={`p-2 rounded-lg border text-center ${
                    data.bias === 'bullish' ? 'bg-green-500/10 border-green-500/30' :
                    data.bias === 'bearish' ? 'bg-red-500/10 border-red-500/30' :
                    'bg-yellow-500/10 border-yellow-500/30'
                  }`}>
                    <div className="text-xs text-muted-foreground mb-1">{tf}</div>
                    <div className={`text-sm font-bold ${
                      data.bias === 'bullish' ? 'text-green-400' :
                      data.bias === 'bearish' ? 'text-red-400' :
                      'text-yellow-400'
                    }`}>
                      {data.bias === 'bullish' ? '📈' : data.bias === 'bearish' ? '📉' : '➡️'}
                    </div>
                    <div className="text-xs text-muted-foreground capitalize">{data.structure}</div>
                  </div>
                ))}
              </div>
              <div className="mt-3 text-xs text-muted-foreground text-center">
                💡 MTF analysis shows trend alignment across {Object.keys(scanResults.mtf_ict_analysis.timeframes || {}).length} timeframes
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
