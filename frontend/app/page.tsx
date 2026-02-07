'use client'

import * as React from 'react'
import { useRouter } from 'next/navigation'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { StatCard, StatsGrid } from '@/components/trading/stat-card'
import { SignalCard, SignalGrid, Signal } from '@/components/trading/signal-card'
import { ProbabilityBar, SentimentGauge } from '@/components/trading/probability-bar'
import { LoadingModal } from '@/components/trading/loading-modal'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { RefreshCw, TrendingUp, TrendingDown, BarChart3, Target, Users, Zap, ArrowUp, ArrowDown, Minus, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { getApiUrl, clearAuthData } from '@/lib/api'
import { checkDailySessionReset, signOut } from '@/lib/supabase'
import { BeginnerSignalCard } from '@/components/trading/beginner-signal-card'
import { TokenBalanceWidget } from '@/components/billing/token-balance-widget'
import { ScanConfirmationDialog } from '@/components/trading/scan-confirmation-dialog'
import { OptionScannerResultsWidget } from '@/components/trading/option-scanner-results-widget'
import { ScanOpportunitiesWidget } from '@/components/trading/scan-opportunities-widget'

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
  risk_reward_2?: string
  confidence: number
  direction: string
  trading_symbol: string
  expiry_date?: string
  days_to_expiry?: number
  // Enhanced fields
  discount_zone?: {
    best_entry?: number
    status?: string
    current_price?: number
    max_entry_price?: number
    target_price?: number
    iv_vs_avg_pct?: number
    momentum_direction?: string
    reasoning?: string
    supports_entry?: boolean
  }
  liquidity_score?: number
  liquidity_grade?: string
  execution_quality?: string
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
  // Greeks
  greeks?: {
    delta: number
    gamma: number
    theta: number
    vega: number
    interpretation?: {
      delta_meaning?: string
      theta_meaning?: string
      gamma_meaning?: string
    }
  }
  // ML Analysis
  ml_analysis?: {
    enabled: boolean
    status: string
    direction: string
    confidence: number
    predicted_price?: number
    price_change_pct?: number
    recommendation?: string
    warning?: string
    models?: {
      arima?: string
      momentum?: string
    }
  }
  // Theta/Expiry Analysis
  theta_analysis?: {
    decay_phase: string
    daily_decay_pct: number
    hourly_decay_pct: number
    current_theta: number
    theta_per_hour: number
    risk_level: string
    advice: string
    best_buy_time?: string
    strategy_recommendation?: string
  }
  expiry_analysis?: {
    days_to_expiry: number
    is_expiry_week: boolean
    is_expiry_day: boolean
    theta_decay_rate: string
    best_entry_advice: string
    time_value_warning?: string
  }
  // MTF Analysis
  mtf_analysis?: {
    overall_bias: string
    current_price: number
    timeframes_analyzed: string[]
    confluence_zones?: Array<{
      center: number
      weight: number
      timeframes: string[]
      distance_pct: number
    }>
    trend_reversal?: {
      is_reversal: boolean
      direction: string
      confidence: number
      reason: string
      timeframes_signaling: string[]
    }
  }
  // Probability Analysis
  probability_analysis?: {
    stocks_scanned: number
    expected_direction: string
    expected_move_pct: number
    confidence: number
    probability_up: number
    probability_down: number
    bullish_pct: number
    bearish_pct: number
    market_regime: string
    constituent_recommendation: string
    top_movers?: {
      bullish: Array<{ symbol: string; probability: number }>
      bearish: Array<{ symbol: string; probability: number }>
      volume_surge: Array<{ symbol: string; has_surge: boolean }>
    }
  }
  // Setup Details
  setup_details?: {
    timeframe: string
    fvg_level: number
    fvg_status: string
    reasoning: string
    reversal_direction: string
    reversal_type: string
    reversal_probability: number
    confidence_level: string
    four_hour_fvg?: {
      detected: boolean
      level: number
      type: string
      direction_message: string
      is_active_setup: boolean
    }
  }
  // Market Context
  market_context?: {
    spot_price: number
    future_price: number
    atm_strike: number
    overall_bias: string
    iv_regime: string
    atm_iv: number
    vix: number
    pcr_oi: number
    pcr_volume: number
    max_pain: number
    basis_pct: number
    support_levels: number[]
    resistance_levels: number[]
  }
  // Trade Recommendation
  trade_recommendation?: {
    verdict: string
    risk_level: string
    reasons: string[]
    position_size_advice: string
    summary: string
  }
  // Trading Mode
  trading_mode?: {
    mode: string
    description: string
    targets: string
    max_hold: string
    entry_window: string
  }
  // Entry Session
  entry_session?: {
    session: string
    advice: string
    can_trade: boolean
    risk_level: string
  }
  // Chain Data
  chain_data?: {
    selected_option: {
      ltp: number
      iv: number
      oi: number
      volume: number
      analysis: string
    }
    opposite_side?: {
      type: string
      ltp: number
      iv: number
      oi: number
    }
    strike_position: string
    distance_pct: number
  }
  // Scalp Feasibility Analysis
  scalp_feasibility?: {
    feasible: boolean
    risk_level: string
    risk_score: number
    recommendation: string
    time_window: string
    targets: {
      entry: number
      target_5: number
      target_10: number
      target_15: number
      stop_loss: number
    }
    index_moves_needed: {
      for_5_pts: number
      for_10_pts: number
      for_15_pts: number
    }
    per_lot_pnl: {
      profit_5: number
      profit_10: number
      profit_15: number
      max_loss: number
      lot_size: number
    }
    theta_impact?: {
      per_hour: number
      per_30_min: number
      warning: string
    }
    risk_factors: string[]
    momentum_boost: boolean
  }
  // Expiry Day Gamma Analysis - NEW
  expiry_gamma_analysis?: {
    gamma_score: number
    is_gamma_opportunity: boolean
    risk_reward: number
    potential_gain_50pt: number
    potential_gain_100pt: number
    gamma_multiplier: number
    delta: number
    moneyness_pct: number
    risk_level: string
    entry_reasons: string[]
    market_phase: string
    is_gamma_window: boolean
    time_remaining_minutes: number
    theta_decay_schedule: Array<{
      time: string
      premium: number
      decay: number
      rate: string
    }>
    trading_advice: {
      gamma_play_viable: boolean
      ideal_premium_range: string
      best_time: string
      key_insight: string
    }
  }
  // Enhanced ML Predictions - NEW Feb 2026
  enhanced_ml_prediction?: {
    direction_prediction?: {
      direction: string
      confidence: number
      expected_move_pct: number
      trade_signal: string
      signal_strength: string
      probabilities?: {
        strong_up: number
        up: number
        sideways: number
        down: number
        strong_down: number
      }
    }
    speed_prediction?: {
      category: string  // EXPLOSIVE, FAST, NORMAL, SLOW, CHOPPY
      confidence: number
      expected_move_pct: number
      expected_time_mins: number
      options_action: string
      reasoning: string[]
      factors?: {
        volume_score: number
        time_of_day_score: number
        volatility_squeeze_score: number
        momentum_score: number
      }
    }
    iv_prediction?: {
      direction: string  // SPIKE, EXPAND, STABLE, CONTRACT, CRUSH
      confidence: number
      expected_change_pct: number
      current_iv: number
      predicted_iv: number
      vega_exposure: string
      options_strategy: string
      reasoning: string[]
      regime?: {
        current: string
        percentile: number
      }
    }
    theta_scenarios?: {
      greeks?: {
        delta: number
        gamma: number
        theta: number
        vega: number
        theta_per_hour: number
      }
      scenarios?: Array<{
        time_label: string
        time_mins: number
        theta_decay: number
        break_even_move_pct: number
        expected_premium: number
        pnl_if_right: number
        pnl_if_wrong: number
        recommendation: string
      }>
      optimal_hold_time?: string
      max_recommended_hold_mins?: number
      theta_warning?: string
    }
    simulation?: {
      grade: string
      expected_pnl: number
      expected_pnl_pct: number
      win_probability: number
      should_trade: boolean
      position_size_pct: number
      entry_timing: string
      exit_strategy: string
      stop_loss: number
      take_profit: number
      max_hold_time_mins: number
    }
    combined_recommendation?: {
      action: string
      confidence: number
      reasoning: string[]
      warnings: string[]
    }
    available_modules?: string[]
    timestamp?: string
  }
  // AMD (Accumulation, Manipulation, Distribution) Detection
  amd_detection?: {
    manipulation_found: boolean
    type?: 'bear_trap' | 'bull_trap' | null
    level?: number | null
    confidence: number
    override_signal?: 'bullish' | 'bearish' | null
    description?: string | null
    recovery_pts: number
    time?: string | null
    is_active: boolean
    override_applied?: boolean
  }
}

interface NewsArticle {
  id: string
  title: string
  description?: string
  published_at: string
  source: string
  url?: string
  sentiment?: 'positive' | 'negative' | 'neutral'
  impact_level?: 'high' | 'medium' | 'low'
  affected_indices?: string[]
}

interface ScanResults {
  probability_analysis?: ProbabilityAnalysis
  recommended_option_type?: 'CALL' | 'PUT' | 'STRADDLE'
  options?: OptionResult[]
  index?: string
  expiry?: string
  spot_price?: number
  timestamp?: string
  market_sentiment?: string
  option_chain_available?: boolean
  market_data?: {
    spot_price: number
    atm_strike: number
    vix?: number
    expiry_date: string
    days_to_expiry: number
    option_chain_unavailable?: boolean
    option_chain_error?: string
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

interface ExpiryData {
  weekly: string
  next_weekly: string
  monthly: string
  all_expiries?: string[]
}

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = React.useState<{ email: string } | null>(null)
  const [selectedIndex, setSelectedIndex] = React.useState('NIFTY')
  const [signals, setSignals] = React.useState<Signal[]>([])
  const [loading, setLoading] = React.useState(false)
  const [expiry, setExpiry] = React.useState('weekly')
  const [expiryDates, setExpiryDates] = React.useState<ExpiryData | null>(null)
  const [loadingExpiries, setLoadingExpiries] = React.useState(false)
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
  const [news, setNews] = React.useState<NewsArticle[]>([])
  const [loadingNews, setLoadingNews] = React.useState(false)
  const [analysisMode, setAnalysisMode] = React.useState('auto')
  const [showScanModeDialog, setShowScanModeDialog] = React.useState(false)
  const [selectedScanMode, setSelectedScanMode] = React.useState<'quick' | 'full'>('quick')

  // New state for token balance and scan confirmation
  const [tokenBalance, setTokenBalance] = React.useState<number | null>(null)
  const [loadingBalance, setLoadingBalance] = React.useState(false)
  const [showConfirmDialog, setShowConfirmDialog] = React.useState(false)
  const [scanCostData, setScanCostData] = React.useState<any>(null)

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

    // ✅ Background token refresh - every 50 minutes to prevent expiry
    const tokenRefreshInterval = setInterval(() => {
      const token = localStorage.getItem('refresh_token')
      if (token) {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        fetch(`${apiUrl}/api/auth/refresh?refresh_token=${encodeURIComponent(token)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        }).then(r => r.json())
          .then(data => {
            if (data.access_token) {
              localStorage.setItem('auth_token', data.access_token)
              localStorage.setItem('token', data.access_token)
              localStorage.setItem('jwt_token', data.access_token)
              if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
              if (data.expires_at) localStorage.setItem('token_expires_at', data.expires_at)
              console.log('🔄 Token refreshed automatically in background')
            }
          })
          .catch(err => console.warn('Background token refresh failed:', err))
      }
    }, 50 * 60 * 1000) // Every 50 minutes

    // ✅ Check if daily session reset is needed (7 AM IST)
    if (checkDailySessionReset()) {
      // Time to logout - session expired based on daily 7 AM rule
      signOut()
      clearAuthData()
      setToast({ message: 'Daily session expired. Please login again.', type: 'error' })
      setTimeout(() => router.push('/landing'), 2000)
      return
    }

    // Check for auth token - redirect to landing if not logged in
    // Use helper to check all possible token keys
    const token = typeof window !== 'undefined' ? (
      localStorage.getItem('auth_token') ||
      localStorage.getItem('token') ||
      localStorage.getItem('jwt_token')
    ) : null
    const email = localStorage.getItem('userEmail')
    
    console.log('🔐 Auth check:', { hasToken: !!token, hasEmail: !!email, tokenStart: token?.substring(0, 30) })
    
    if (token && email) {
      setUser({ email })
      // Check Fyers authentication status on page load
      checkFyersAuth(token)
      // Fetch latest scan results and display on dashboard
      fetchLatestScanResults(token)
      // Fetch token balance
      fetchTokenBalance(token)
    } else {
      // Redirect to landing page if not authenticated
      console.log('❌ No auth token or email found, redirecting to landing')
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
          const authToken = localStorage.getItem('auth_token') || localStorage.getItem('token') || localStorage.getItem('jwt_token')
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

  // Fetch recent news on mount
  React.useEffect(() => {
    fetchNews()
  }, [])

  // Fetch expiry dates when index changes
  React.useEffect(() => {
    const fetchExpiries = async () => {
      setLoadingExpiries(true)
      try {
        const apiUrl = getApiUrl()
        const response = await fetch(`${apiUrl}/index/${selectedIndex}/expiries`)

        if (response.ok) {
          const data = await response.json()
          setExpiryDates(data.expiries)

          // Set default to weekly expiry
          if (data.expiries?.weekly) {
            setExpiry('weekly')
          }
        }
      } catch (error) {
        console.error('Failed to fetch expiry dates:', error)
      } finally {
        setLoadingExpiries(false)
      }
    }

    fetchExpiries()
  }, [selectedIndex])

  // Refetch scans when selected index changes
  React.useEffect(() => {
    if (mounted && user) {
      const token = localStorage.getItem('auth_token') || localStorage.getItem('token') || localStorage.getItem('jwt_token')
      if (token) {
        fetchLatestScanResults(token, selectedIndex)
      }
    }
  }, [selectedIndex, mounted, user])

  const fetchNews = async () => {
    setLoadingNews(true)
    try {
      const apiUrl = getApiUrl()
      const response = await fetch(`${apiUrl}/api/news?hours=6&limit=10`)

      if (response.ok) {
        const data = await response.json()
        setNews(data.articles || [])
      }
    } catch (error) {
      console.error('Error fetching news:', error)
    } finally {
      setLoadingNews(false)
    }
  }

  // Check Fyers authentication status
  const checkFyersAuth = async (token: string) => {
    try {
      const apiUrl = getApiUrl()

      // For localhost, use status endpoint that doesn't require user auth
      const statusResponse = await fetch(`${apiUrl}/api/fyers/token/status`)

      if (statusResponse.ok) {
        const statusData = await statusResponse.json()

        if (statusData.has_token && statusData.status === 'valid') {
          console.log('✅ Fyers token valid:', statusData.message)
          return
        } else if (statusData.status === 'expired') {
          console.warn('⏰ Fyers token expired:', statusData.message)
          setToast({
            message: `Token expired. Please reconnect your Fyers account.`,
            type: 'error'
          })
          setTimeout(() => setToast(null), 8000)
        } else {
          console.warn('⚠️ No valid Fyers token:', statusData.message)
          setToast({
            message: statusData.message,
            type: 'error'
          })
          setTimeout(() => setToast(null), 8000)
        }
      } else {
        console.warn('⚠️ Could not check Fyers token status')
      }
    } catch (error) {
      console.error('Error checking Fyers auth:', error)
    }
  }
  // Fetch the latest scan results from database and display on dashboard
  const fetchLatestScanResults = async (token: string, indexFilter?: string) => {
    try {
      const apiUrl = getApiUrl()
      const index = indexFilter || selectedIndex

      // Add index query parameter to filter scans
      const url = `${apiUrl}/screener/latest?index=${index}`

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        if (data.status === 'success') {
          console.log('✅ Loaded latest scan results from database:', data)

          // Set the scan results
          setScanResults(data)

          // Calculate and set the trading signal
          const signal = calculateTradingSignal(data)
          if (signal) {
            setTradingSignal(signal)
          }

          // Update selected index if scan data contains index
          if (data.index && data.index !== selectedIndex) {
            setSelectedIndex(data.index)
          }
        } else if (data.status === 'no_data') {
          console.log('No latest scan results found:', data.message)
          // Clear existing results
          setScanResults(null)
          // Don't show toast on initial load, only when manually changing index
        }
      } else if (response.status === 401) {
        console.error('❌ Token expired or invalid - clearing auth data')
        // Token expired - clear and redirect to login
        localStorage.removeItem('auth_token')
        localStorage.removeItem('token')
        localStorage.removeItem('jwt_token')
        setToast({ message: 'Session expired. Please login again.', type: 'error' })
        setTimeout(() => router.push('/login'), 2000)
      } else if (response.status === 404) {
        console.log('No scan results available yet - user needs to run a scan first')
        setScanResults(null)
      } else {
        console.warn('Could not fetch latest scan results:', response.status)
      }
    } catch (error) {
      console.error('Error fetching latest scan results:', error)
    }
  }

  // Fetch user token balance
  const fetchTokenBalance = async (token: string) => {
    setLoadingBalance(true)
    try {
      const apiUrl = getApiUrl()

      const response = await fetch(`${apiUrl}/api/billing/status`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        console.log('Token balance response:', data)
        setTokenBalance(data.billing_status?.credits_balance ?? data.credits_balance ?? 0)
      } else {
        console.error('Failed to fetch token balance:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('Error fetching token balance:', error)
    } finally {
      setLoadingBalance(false)
    }
  }

  // Calculate option scan cost
  const calculateScanCost = async (token: string, quickScan: boolean, index: string) => {
    try {
      const apiUrl = typeof window !== 'undefined'
        ? (localStorage.getItem('apiUrl') || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
        : 'http://localhost:8000'

      const response = await fetch(`${apiUrl}/api/options/calculate-cost`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          quick_scan: quickScan,
          index: index
        })
      })

      if (response.ok) {
        const data = await response.json()
        return data
      }
      return null
    } catch (error) {
      console.error('Error calculating scan cost:', error)
      return null
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
          const token = localStorage.getItem('auth_token') || localStorage.getItem('token') || localStorage.getItem('jwt_token')
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
    // Use helper to clear all auth data
    clearAuthData()
    localStorage.removeItem('userEmail')
    setUser(null)
    // Redirect to landing page after logout
    router.push('/landing')
  }

  const handleQuickScan = async () => {
    const token = localStorage.getItem('auth_token') || localStorage.getItem('token') || localStorage.getItem('jwt_token')

    // Check if user is logged in
    if (!token) {
      setToast({ message: 'Please login first to scan options', type: 'error' })
      setTimeout(() => {
        setToast(null)
        router.push('/login')
      }, 2000)
      return
    }

    // Show scan mode selection dialog
    setShowScanModeDialog(true)
  }

  // Execute scan with selected mode
  const executeScan = async (mode: 'quick' | 'full') => {
    setSelectedScanMode(mode)
    setShowScanModeDialog(false)

    const token = localStorage.getItem('auth_token') || localStorage.getItem('token') || localStorage.getItem('jwt_token')
    if (!token) return

    // Calculate scan cost and show confirmation dialog
    const costData = await calculateScanCost(token, mode === 'quick', selectedIndex)
    if (costData) {
      setScanCostData(costData)
      setShowConfirmDialog(true)
    } else {
      setToast({ message: 'Failed to calculate scan cost', type: 'error' })
      setTimeout(() => setToast(null), 3000)
    }
  }

  // Actually execute the scan after user confirms
  const confirmedExecuteScan = async () => {
    const token = localStorage.getItem('auth_token') || localStorage.getItem('token') || localStorage.getItem('jwt_token')
    if (!token) return

    // ========== EARLY FYERS AUTH CHECK ==========
    // Verify Fyers is actually authenticated before spending time/credits on scan
    try {
      const apiUrl = getApiUrl()
      const fyersCheck = await fetch(`${apiUrl}/api/fyers/token/status`)
      if (fyersCheck.ok) {
        const fyersStatus = await fyersCheck.json()
        if (!fyersStatus.has_token || fyersStatus.status === 'no_token' || fyersStatus.status === 'expired') {
          console.warn('🔐 Fyers not authenticated, blocking scan')
          setToast({
            message: '🔐 Fyers broker connection required to scan. Connecting now...',
            type: 'error'
          })
          setTimeout(() => {
            setToast(null)
            openFyersAuthPopup()
          }, 1500)
          return
        }
      }
    } catch (fyersCheckErr) {
      console.warn('⚠️ Could not verify Fyers status, proceeding with scan:', fyersCheckErr)
      // Don't block scan if the status check itself fails - let it proceed
    }
    // ========== END FYERS AUTH CHECK ==========

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

      // Use the selected expiry from dropdown
      const selectedExpiry = expiry

      // Step 2 complete, Step 3: Generating option symbols
      updateStep('2', 'complete', 33)
      updateStep('3', 'loading', 40)

      // Use selected scan mode (quick_scan parameter)
      const quickScan = selectedScanMode === 'quick'
      const url = `${apiUrl}/options/scan?index=${selectedIndex}&expiry=${selectedExpiry}&min_volume=1000&min_oi=10000&strategy=all&include_probability=true&quick_scan=${quickScan}`

      console.log(`📡 Fetching scan data from: ${url}`)
      console.log(`📈 Selected index: ${selectedIndex}`)
      console.log(`📅 Selected expiry: ${selectedExpiry}`)

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
        // Check if it's a Fyers auth issue or user session issue
        const errorData = await response.json().catch(() => ({}))

        if (errorData.detail && typeof errorData.detail === 'object') {
          const detail = errorData.detail

          if (detail.error === 'fyers_auth_required' || detail.error === 'fyers_token_expired') {
            // Fyers authentication needed - show alert and redirect
            const message = detail.error === 'fyers_token_expired'
              ? 'Your broker authentication has expired. Please reconnect to continue.'
              : 'You need to connect your broker account to scan options.'

            setToast({ message: message + ' Redirecting...', type: 'error' })
            setTimeout(() => {
              setToast(null)
              if (detail.auth_url) {
                window.location.href = detail.auth_url
              } else {
                // Trigger Fyers auth from dashboard
                openFyersAuthPopup()
              }
            }, 2000)
            return
          }
        }

        // If not Fyers auth, it's a genuine session issue
        clearAuthData()
        setToast({ message: 'Session expired. Please login again.', type: 'error' })
        setTimeout(() => {
          setToast(null)
          router.push('/login')
        }, 2000)
        return
      }

      // Handle Fyers data unavailable error (503)
      if (response.status === 503) {
        const errorData = await response.json().catch(() => ({}))
        const detail = typeof errorData.detail === 'object' ? errorData.detail : { message: errorData.detail || 'Service unavailable' }

        if (detail.error === 'FYERS_DATA_UNAVAILABLE') {
          setToast({
            message: '⚠️ ' + (detail.message || 'Market data unavailable. Please connect your Fyers account.'),
            type: 'error'
          })
          // Show the auth popup to reconnect Fyers
          setTimeout(() => {
            setToast(null)
            openFyersAuthPopup()
          }, 3000)
          return
        }

        throw new Error(detail.message || 'Service unavailable. Please try again.')
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }))
        const errorMessage = typeof errorData.detail === 'object'
          ? errorData.detail.message || JSON.stringify(errorData.detail)
          : errorData.detail || `Scan failed: ${response.statusText}`
        throw new Error(errorMessage)
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
      // Include expiry parameter to ensure correct expiry date is used
      const signalUrl = `${apiUrl}/signals/${encodeURIComponent(symbol)}/actionable?expiry=${encodeURIComponent(expiry)}`

      console.log(`🎯 Fetching actionable signal for ${selectedIndex} -> ${symbol}`)
      console.log(`📡 Signal URL: ${signalUrl}`)
      console.log(`📅 Using expiry: ${expiry}`)

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

      // Handle signal fetch errors (especially Fyers auth issues)
      if (!signalResponse.ok) {
        const signalErrorData = await signalResponse.json().catch(() => ({}))
        const signalDetail = typeof signalErrorData.detail === 'object' 
          ? signalErrorData.detail 
          : { message: signalErrorData.detail || 'Signal generation failed' }

        console.error('❌ Signal fetch failed:', signalResponse.status, signalDetail)

        // Handle Fyers authentication required (503)
        if (signalResponse.status === 503 && signalDetail.error === 'FYERS_AUTH_REQUIRED') {
          setToast({
            message: '🔐 Fyers authentication required. Please connect your broker account.',
            type: 'error'
          })
          updateStep('6', 'error', 85)
          setLoading(false)
          
          // Show Fyers auth popup after a short delay
          setTimeout(() => {
            setToast(null)
            openFyersAuthPopup()
          }, 2000)
          return
        }

        // Handle other 503 errors
        if (signalResponse.status === 503) {
          setToast({
            message: `⚠️ ${signalDetail.message || 'Service unavailable. Please try again.'}`,
            type: 'error'
          })
          updateStep('6', 'error', 85)
          setLoading(false)
          return
        }

        // Handle 500 errors
        if (signalResponse.status === 500) {
          setToast({
            message: `❌ ${signalDetail.message || 'Signal generation failed. Please try again.'}`,
            type: 'error'
          })
          updateStep('6', 'error', 85)
          setLoading(false)
          return
        }

        // For other errors, show message but try fallback
        console.warn('⚠️ Signal fetch failed, will attempt fallback calculation')
      }

      if (signalResponse.ok) {
        const backendSignal = await signalResponse.json()

        // Check if backend returned an error signal
        if (backendSignal.signal === 'ERROR') {
          console.error('❌ Backend returned error signal:', backendSignal.reason)
          setToast({
            message: `⚠️ Signal Error: ${backendSignal.reason || 'Failed to generate signal'}`,
            type: 'error'
          })
          updateStep('6', 'error', 85)
          setLoading(false)
          return
        }

        // Step 6 complete
        updateStep('6', 'complete', 100)
        setLoadingProgress(100)

        // Map backend signal to frontend format
        // Handle both new format (object with score/level) and legacy format (string)
        let numericConfidence: number
        
        if (backendSignal.confidence_breakdown?.total) {
          // NEW: Use confidence_breakdown.total (the actual calculated score)
          numericConfidence = Math.round(backendSignal.confidence_breakdown.total)
        } else if (typeof backendSignal.confidence === 'object' && backendSignal.confidence?.score !== undefined) {
          // NEW FORMAT: confidence is an object { score: 26.5, level: "AVOID" }
          numericConfidence = Math.round(backendSignal.confidence.score)
        } else if (backendSignal.setup_details?.reversal_probability) {
          numericConfidence = backendSignal.setup_details.reversal_probability
        } else if (typeof backendSignal.confidence === 'string') {
          // LEGACY FORMAT: confidence is a string like "HIGH", "VERY HIGH"
          numericConfidence = 
            backendSignal.confidence === 'VERY HIGH' ? 85 :
            backendSignal.confidence === 'HIGH' ? 72 :
            backendSignal.confidence === 'MODERATE' ? 55 :
            backendSignal.confidence === 'MEDIUM' ? 50 : 35
        } else {
          numericConfidence = 35 // Default fallback
        }

        // Get entry price - prefer best_entry_price from discount zone analysis
        const entryPrice = backendSignal.entry.best_entry_price || backendSignal.entry.price

        // CRITICAL FIX: Ensure stop_loss is ALWAYS below entry_price for BUY positions
        // If backend sends invalid stop_loss (>= entry), recalculate it
        let stopLoss = backendSignal.targets.stop_loss
        let stopLossCorrected = false
        if (stopLoss >= entryPrice) {
          console.warn(`⚠️ Invalid stop_loss (${stopLoss}) >= entry (${entryPrice}). Recalculating...`)
          // Calculate 15% below entry price as safety
          stopLoss = Math.round(entryPrice * 0.85 * 100) / 100
          stopLossCorrected = true
          console.log(`   Corrected stop_loss to ${stopLoss}`)
        }

        // Recalculate risk/reward if stop_loss was corrected
        let riskReward = backendSignal.risk_reward?.ratio_1 ? `1:${typeof backendSignal.risk_reward.ratio_1 === 'number' ? backendSignal.risk_reward.ratio_1.toFixed(1) : backendSignal.risk_reward.ratio_1}` : '1:2'
        if (stopLossCorrected) {
          const risk = entryPrice - stopLoss
          const target1 = backendSignal.targets.target_1
          const reward = target1 - entryPrice
          if (risk > 0) {
            riskReward = `1:${(reward / risk).toFixed(1)}`
          }
        }

        const tradingSignal: TradingSignal = {
          action: backendSignal.action,
          strike: backendSignal.option.strike,
          type: backendSignal.option.type,
          entry_price: entryPrice,
          target_1: backendSignal.targets.target_1,
          target_2: backendSignal.targets.target_2,
          stop_loss: stopLoss,
          risk_reward: riskReward,
          risk_reward_2: backendSignal.risk_reward?.ratio_2,
          confidence: numericConfidence,
          direction: backendSignal.mtf_analysis?.overall_bias?.toUpperCase() || backendSignal.signal_type || 'NEUTRAL',
          trading_symbol: backendSignal.option.trading_symbol || backendSignal.option.symbol,
          expiry_date: backendSignal.option.expiry_date,
          days_to_expiry: backendSignal.option.expiry_info?.days_to_expiry,

          // Discount Zone - comprehensive
          discount_zone: {
            best_entry: backendSignal.discount_zone?.best_entry_price,
            status: backendSignal.discount_zone?.status,
            current_price: backendSignal.discount_zone?.current_price,
            max_entry_price: backendSignal.discount_zone?.max_entry_price,
            target_price: backendSignal.discount_zone?.target_price,
            iv_vs_avg_pct: backendSignal.discount_zone?.iv_vs_avg_pct,
            momentum_direction: backendSignal.discount_zone?.momentum_direction,
            reasoning: backendSignal.discount_zone?.reasoning,
            supports_entry: backendSignal.discount_zone?.supports_entry
          },

          // Market Depth/Liquidity
          liquidity_score: backendSignal.market_depth?.liquidity_score,
          liquidity_grade: backendSignal.market_depth?.execution_quality,
          execution_quality: backendSignal.market_depth?.execution_quality,

          // Sentiment (if available)
          sentiment_score: backendSignal.sentiment_analysis?.sentiment_score,
          sentiment_direction: backendSignal.sentiment_analysis?.sentiment_direction,
          market_mood: backendSignal.sentiment_analysis?.market_mood,
          news_articles: backendSignal.sentiment_analysis?.news_articles_retrieved,

          // Reversal Detection
          reversal_detected: backendSignal.mtf_analysis?.trend_reversal?.is_reversal,
          reversal_type: backendSignal.mtf_analysis?.trend_reversal?.direction,
          reversal_description: backendSignal.mtf_analysis?.trend_reversal?.reason,

          // MTF Bias
          mtf_bias: backendSignal.mtf_analysis?.overall_bias,

          // Entry Analysis
          entry_analysis: backendSignal.entry_analysis,
          raw_ltp: backendSignal.pricing?.ltp,

          // Greeks - NEW
          greeks: backendSignal.greeks ? {
            delta: backendSignal.greeks.delta,
            gamma: backendSignal.greeks.gamma,
            theta: backendSignal.greeks.theta,
            vega: backendSignal.greeks.vega,
            interpretation: backendSignal.greeks.interpretation
          } : undefined,

          // ML Analysis - NEW
          ml_analysis: backendSignal.ml_analysis ? {
            enabled: backendSignal.ml_analysis.enabled,
            status: backendSignal.ml_analysis.status,
            direction: backendSignal.ml_analysis.direction,
            confidence: backendSignal.ml_analysis.confidence,
            predicted_price: backendSignal.ml_analysis.predicted_price,
            price_change_pct: backendSignal.ml_analysis.price_change_pct,
            recommendation: backendSignal.ml_analysis.recommendation,
            warning: backendSignal.ml_analysis.warning,
            models: backendSignal.ml_analysis.models
          } : undefined,

          // Theta Analysis - NEW
          theta_analysis: backendSignal.theta_analysis ? {
            decay_phase: backendSignal.theta_analysis.decay_phase,
            daily_decay_pct: backendSignal.theta_analysis.daily_decay_pct,
            hourly_decay_pct: backendSignal.theta_analysis.hourly_decay_pct,
            current_theta: backendSignal.theta_analysis.current_theta,
            theta_per_hour: backendSignal.theta_analysis.theta_per_hour,
            risk_level: backendSignal.theta_analysis.risk_level,
            advice: backendSignal.theta_analysis.advice,
            best_buy_time: backendSignal.theta_analysis.best_buy_time,
            strategy_recommendation: backendSignal.theta_analysis.strategy_recommendation
          } : undefined,

          // Expiry Analysis - NEW
          expiry_analysis: backendSignal.expiry_analysis ? {
            days_to_expiry: backendSignal.expiry_analysis.days_to_expiry,
            is_expiry_week: backendSignal.expiry_analysis.is_expiry_week,
            is_expiry_day: backendSignal.expiry_analysis.is_expiry_day,
            theta_decay_rate: backendSignal.expiry_analysis.theta_decay_rate,
            best_entry_advice: backendSignal.expiry_analysis.best_entry_advice,
            time_value_warning: backendSignal.expiry_analysis.time_value_warning
          } : undefined,

          // MTF Analysis - NEW
          mtf_analysis: backendSignal.mtf_analysis ? {
            overall_bias: backendSignal.mtf_analysis.overall_bias,
            current_price: backendSignal.mtf_analysis.current_price,
            timeframes_analyzed: backendSignal.mtf_analysis.timeframes_analyzed,
            confluence_zones: backendSignal.mtf_analysis.confluence_zones,
            trend_reversal: backendSignal.mtf_analysis.trend_reversal
          } : undefined,

          // Probability Analysis - NEW
          probability_analysis: backendSignal.probability_analysis ? {
            stocks_scanned: backendSignal.probability_analysis.stocks_scanned,
            expected_direction: backendSignal.probability_analysis.expected_direction,
            expected_move_pct: backendSignal.probability_analysis.expected_move_pct,
            confidence: backendSignal.probability_analysis.confidence,
            probability_up: backendSignal.probability_analysis.probability_up,
            probability_down: backendSignal.probability_analysis.probability_down,
            bullish_pct: backendSignal.probability_analysis.bullish_pct,
            bearish_pct: backendSignal.probability_analysis.bearish_pct,
            market_regime: backendSignal.probability_analysis.market_regime,
            constituent_recommendation: backendSignal.probability_analysis.constituent_recommendation,
            top_movers: backendSignal.probability_analysis.top_movers
          } : undefined,

          // Setup Details - NEW
          setup_details: backendSignal.setup_details ? {
            timeframe: backendSignal.setup_details.timeframe,
            fvg_level: backendSignal.setup_details.fvg_level,
            fvg_status: backendSignal.setup_details.fvg_status,
            reasoning: backendSignal.setup_details.reasoning,
            reversal_direction: backendSignal.setup_details.reversal_direction,
            reversal_type: backendSignal.setup_details.reversal_type,
            reversal_probability: backendSignal.setup_details.reversal_probability,
            confidence_level: backendSignal.setup_details.confidence_level,
            four_hour_fvg: backendSignal.setup_details.four_hour_fvg
          } : undefined,

          // Market Context - NEW
          market_context: backendSignal.market_context ? {
            spot_price: backendSignal.market_context.spot_price,
            future_price: backendSignal.market_context.future_price,
            atm_strike: backendSignal.market_context.atm_strike,
            overall_bias: backendSignal.market_context.overall_bias,
            iv_regime: backendSignal.market_context.iv_regime,
            atm_iv: backendSignal.market_context.atm_iv,
            vix: backendSignal.market_context.vix,
            pcr_oi: backendSignal.market_context.pcr_oi,
            pcr_volume: backendSignal.market_context.pcr_volume,
            max_pain: backendSignal.market_context.max_pain,
            basis_pct: backendSignal.market_context.basis_pct,
            support_levels: backendSignal.market_context.support_levels,
            resistance_levels: backendSignal.market_context.resistance_levels
          } : undefined,

          // Trade Recommendation - NEW
          trade_recommendation: backendSignal.trade_recommendation ? {
            verdict: backendSignal.trade_recommendation.verdict,
            risk_level: backendSignal.trade_recommendation.risk_level,
            reasons: backendSignal.trade_recommendation.reasons,
            position_size_advice: backendSignal.trade_recommendation.position_size_advice,
            summary: backendSignal.trade_recommendation.summary
          } : undefined,

          // Trading Mode - NEW
          trading_mode: backendSignal.trading_mode ? {
            mode: backendSignal.trading_mode.mode,
            description: backendSignal.trading_mode.description,
            targets: backendSignal.trading_mode.targets,
            max_hold: backendSignal.trading_mode.max_hold,
            entry_window: backendSignal.trading_mode.entry_window
          } : undefined,

          // Entry Session - NEW
          entry_session: backendSignal.entry?.session_advice ? {
            session: backendSignal.entry.session_advice.session,
            advice: backendSignal.entry.session_advice.advice,
            can_trade: backendSignal.entry.session_advice.can_trade,
            risk_level: backendSignal.entry.session_advice.risk_level
          } : undefined,

          // Chain Data - NEW
          chain_data: backendSignal.option?.chain_data ? {
            selected_option: backendSignal.option.chain_data.selected_option,
            opposite_side: backendSignal.option.chain_data.opposite_side,
            strike_position: backendSignal.option.chain_data.strike_position,
            distance_pct: backendSignal.option.chain_data.distance_pct
          } : undefined,

          // Scalp Feasibility - NEW
          scalp_feasibility: backendSignal.scalp_feasibility ? {
            feasible: backendSignal.scalp_feasibility.feasible,
            risk_level: backendSignal.scalp_feasibility.risk_level,
            risk_score: backendSignal.scalp_feasibility.risk_score,
            recommendation: backendSignal.scalp_feasibility.recommendation,
            time_window: backendSignal.scalp_feasibility.time_window,
            targets: backendSignal.scalp_feasibility.targets,
            index_moves_needed: backendSignal.scalp_feasibility.index_moves_needed,
            per_lot_pnl: backendSignal.scalp_feasibility.per_lot_pnl,
            theta_impact: backendSignal.scalp_feasibility.theta_impact,
            risk_factors: backendSignal.scalp_feasibility.risk_factors,
            momentum_boost: backendSignal.scalp_feasibility.momentum_boost
          } : undefined,

          // Expiry Day Gamma Analysis - NEW
          expiry_gamma_analysis: backendSignal.expiry_gamma_analysis ? {
            gamma_score: backendSignal.expiry_gamma_analysis.gamma_score,
            is_gamma_opportunity: backendSignal.expiry_gamma_analysis.is_gamma_opportunity,
            risk_reward: backendSignal.expiry_gamma_analysis.risk_reward,
            potential_gain_50pt: backendSignal.expiry_gamma_analysis.potential_gain_50pt,
            potential_gain_100pt: backendSignal.expiry_gamma_analysis.potential_gain_100pt,
            gamma_multiplier: backendSignal.expiry_gamma_analysis.gamma_multiplier,
            delta: backendSignal.expiry_gamma_analysis.delta,
            moneyness_pct: backendSignal.expiry_gamma_analysis.moneyness_pct,
            risk_level: backendSignal.expiry_gamma_analysis.risk_level,
            entry_reasons: backendSignal.expiry_gamma_analysis.entry_reasons,
            market_phase: backendSignal.expiry_gamma_analysis.market_phase,
            is_gamma_window: backendSignal.expiry_gamma_analysis.is_gamma_window,
            time_remaining_minutes: backendSignal.expiry_gamma_analysis.time_remaining_minutes,
            theta_decay_schedule: backendSignal.expiry_gamma_analysis.theta_decay_schedule,
            trading_advice: backendSignal.expiry_gamma_analysis.trading_advice
          } : undefined,

          // 🧠 Enhanced ML Prediction - NEW Feb 2026
          enhanced_ml_prediction: backendSignal.enhanced_ml_prediction ? {
            direction_prediction: backendSignal.enhanced_ml_prediction.direction_prediction,
            speed_prediction: backendSignal.enhanced_ml_prediction.speed_prediction,
            iv_prediction: backendSignal.enhanced_ml_prediction.iv_prediction,
            theta_scenarios: backendSignal.enhanced_ml_prediction.theta_scenarios,
            simulation: backendSignal.enhanced_ml_prediction.simulation,
            combined_recommendation: backendSignal.enhanced_ml_prediction.combined_recommendation,
            available_modules: backendSignal.enhanced_ml_prediction.available_modules,
            timestamp: backendSignal.enhanced_ml_prediction.timestamp
          } : undefined,

          // Keep legacy for backward compatibility
          confidence_adjustments: backendSignal.confidence_adjustments,

          // AMD (Manipulation) Detection - NEW Feb 2026
          amd_detection: backendSignal.amd_detection ? {
            manipulation_found: backendSignal.amd_detection.manipulation_found,
            type: backendSignal.amd_detection.type,
            level: backendSignal.amd_detection.level,
            confidence: backendSignal.amd_detection.confidence,
            override_signal: backendSignal.amd_detection.override_signal,
            description: backendSignal.amd_detection.description,
            recovery_pts: backendSignal.amd_detection.recovery_pts,
            time: backendSignal.amd_detection.time,
            is_active: backendSignal.amd_detection.is_active,
            override_applied: backendSignal.amd_detection.override_applied
          } : undefined
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
    <DashboardLayout
      user={user}
      selectedIndex={selectedIndex}
      onIndexChange={setSelectedIndex}
      onLogout={handleLogout}
      showBackButton={false}
      signalData={tradingSignal}
      scanData={scanResults ? {
        symbol: selectedIndex,
        timestamp: scanResults.timestamp,
        results: scanResults,
        probability: scanResults.probability_analysis,
        totalOptions: scanResults.options?.length || 0,
        marketSentiment: scanResults.market_sentiment,
        recommendedOption: scanResults.recommended_option_type
      } : null}
    >
      <div className="container mx-auto px-3 md:px-4 py-4 md:py-6 space-y-4 md:space-y-6">

        {/* Scan Mode Selection Dialog */}
        {showScanModeDialog && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  Choose Scan Mode
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  Select the analysis depth for {selectedIndex} options scanning
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Quick Scan Option */}
                <button
                  onClick={() => executeScan('quick')}
                  className="w-full p-4 border-2 border-border rounded-lg hover:border-primary hover:bg-accent transition-all text-left"
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-1">⚡</div>
                    <div className="flex-1">
                      <div className="font-semibold text-base mb-1">Quick Scan (Recommended)</div>
                      <div className="text-sm text-muted-foreground mb-2">
                        Fast analysis in 90-180 seconds
                      </div>
                      <ul className="text-xs text-muted-foreground space-y-1">
                        <li>✓ Multi-timeframe ICT analysis</li>
                        <li>✓ Option chain analysis</li>
                        <li>✓ ML predictions</li>
                        <li>✓ Greeks & risk metrics</li>
                        <li className="text-yellow-600">⚠ Skips 50-stock constituent analysis</li>
                      </ul>
                      <div className="mt-2 text-xs font-medium text-blue-600">
                        Perfect for: Automated trading, quick decisions
                      </div>
                    </div>
                  </div>
                </button>

                {/* Full Scan Option */}
                <button
                  onClick={() => executeScan('full')}
                  className="w-full p-4 border-2 border-border rounded-lg hover:border-primary hover:bg-accent transition-all text-left"
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-1">🎯</div>
                    <div className="flex-1">
                      <div className="font-semibold text-base mb-1">Full Analysis</div>
                      <div className="text-sm text-muted-foreground mb-2">
                        Deep analysis in 3-5 minutes
                      </div>
                      <ul className="text-xs text-muted-foreground space-y-1">
                        <li>✓ Everything in Quick Scan, PLUS:</li>
                        <li>✓ 50-stock constituent analysis</li>
                        <li>✓ Probability breakdown by stock</li>
                        <li>✓ Market regime detection</li>
                        <li>✓ Higher confidence signals</li>
                      </ul>
                      <div className="mt-2 text-xs font-medium text-purple-600">
                        Perfect for: Manual trading, detailed analysis
                      </div>
                    </div>
                  </div>
                </button>

                {/* Cancel Button */}
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setShowScanModeDialog(false)}
                >
                  Cancel
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

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
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Link href="/screener" className="block">
            <Button variant="outline" className="w-full h-auto py-3 px-4 flex items-center justify-start gap-3 hover:bg-accent">
              <BarChart3 className="w-5 h-5" />
              <span className="text-sm font-medium">Stock Screener</span>
            </Button>
          </Link>
          <Link href="/scans" className="block">
            <Button variant="outline" className="w-full h-auto py-3 px-4 flex items-center justify-start gap-3 hover:bg-accent">
              <Target className="w-5 h-5" />
              <span className="text-sm font-medium">Scan Results</span>
            </Button>
          </Link>
          <Button
            variant="outline"
            className="w-full h-auto py-3 px-4 flex items-center justify-start gap-3 hover:bg-accent"
            onClick={openFyersAuthPopup}
          >
            <span className="text-xl">🔑</span>
            <span className="text-sm font-medium">Connect Broker</span>
          </Button>
          <div className="w-full">
            <Select value={expiry} onValueChange={setExpiry} disabled={loadingExpiries}>
              <SelectTrigger className="w-full h-auto py-3 px-4">
                <SelectValue placeholder={loadingExpiries ? "Loading..." : "Select expiry"} />
              </SelectTrigger>
              <SelectContent>
                {expiryDates?.weekly && (
                  <SelectItem value="weekly">
                    Weekly - {new Date(expiryDates.weekly).toLocaleDateString('en-IN', {
                      day: '2-digit',
                      month: 'short'
                    })}
                  </SelectItem>
                )}
                {expiryDates?.next_weekly && (
                  <SelectItem value="next_weekly">
                    Next Week - {new Date(expiryDates.next_weekly).toLocaleDateString('en-IN', {
                      day: '2-digit',
                      month: 'short'
                    })}
                  </SelectItem>
                )}
                {expiryDates?.monthly && (
                  <SelectItem value="monthly">
                    Monthly - {new Date(expiryDates.monthly).toLocaleDateString('en-IN', {
                      day: '2-digit',
                      month: 'short'
                    })}
                  </SelectItem>
                )}
                {expiryDates?.all_expiries && expiryDates.all_expiries.length > 0 && (
                  <>
                    {expiryDates.all_expiries
                      .filter(date =>
                        date !== expiryDates.weekly &&
                        date !== expiryDates.next_weekly &&
                        date !== expiryDates.monthly
                      )
                      .map((date) => (
                        <SelectItem key={date} value={date}>
                          {new Date(date).toLocaleDateString('en-IN', {
                            day: '2-digit',
                            month: 'short',
                            year: 'numeric'
                          })}
                        </SelectItem>
                      ))
                    }
                  </>
                )}
              </SelectContent>
            </Select>
          </div>
          <div className="w-full">
            <label className="text-xs text-muted-foreground mb-1 block">Analysis Mode</label>
            <Select value={analysisMode} onValueChange={setAnalysisMode}>
              <SelectTrigger className="w-full h-auto py-3 px-4">
                <SelectValue placeholder="Select mode" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">Auto (Intraday during market hours)</SelectItem>
                <SelectItem value="intraday">Intraday (5-min candles)</SelectItem>
                <SelectItem value="longterm">Long Term (Daily candles)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button
            className="w-full h-auto py-3 px-4 flex items-center justify-center gap-2 bg-primary hover:bg-primary/90"
            onClick={handleQuickScan}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Zap className="w-5 h-5" />
            )}
            <span className="text-sm font-semibold">Scan {selectedIndex}</span>
          </Button>

          {/* Token Balance Widget */}
          <TokenBalanceWidget
            balance={tokenBalance}
            loading={loadingBalance}
            onRefresh={() => {
              const token = localStorage.getItem('auth_token') || localStorage.getItem('token') || localStorage.getItem('jwt_token')
              if (token) fetchTokenBalance(token)
            }}
            className="md:col-span-2"
          />
        </div>

        {/* Option Scanner Results Widget */}
        {tradingSignal && (
          <OptionScannerResultsWidget
            index={selectedIndex}
            onIndexChange={setSelectedIndex}
            className="mb-6"
          />
        )}

        {/* ============ NO SCANS MESSAGE ============ */}
        {!loading && !scanResults && !tradingSignal && (
          <Card className="border-dashed border-2">
            <CardContent className="pt-6 text-center py-12">
              <div className="flex flex-col items-center gap-4">
                <div className="text-6xl">📊</div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">No {selectedIndex} Scans Yet</h3>
                  <p className="text-muted-foreground text-sm mb-4">
                    Start scanning {selectedIndex} options to see trading signals and analysis here.
                  </p>
                  <Button
                    onClick={handleQuickScan}
                    className="gap-2"
                  >
                    <Zap className="w-4 h-4" />
                    Scan {selectedIndex} Now
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

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
                  <Badge variant="outline" className="text-xs border-green-500 text-green-500">
                    🟢 Live Data
                  </Badge>
                  {/* Entry Grade Badge */}
                  <Badge
                    variant="outline"
                    className={`text-xs ${(tradingSignal as any).entry_grade === 'A' ? 'border-green-500 text-green-500' :
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
              {/* Option Chain Unavailable Warning */}
              {scanResults.option_chain_available === false && (
                <div className="p-3 bg-yellow-500/20 rounded-lg border border-yellow-500/50">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">⚠️</span>
                    <div>
                      <div className="text-sm font-bold text-yellow-400">Option Chain Data Unavailable</div>
                      <div className="text-xs text-yellow-300/80 mt-1">
                        {scanResults.market_data?.option_chain_error || 'Market may be closed. Signal analysis shown is based on historical index data only.'}
                      </div>
                      <div className="text-xs text-yellow-200/60 mt-1">
                        💡 No specific options are displayed. Re-scan during market hours (9:15 AM - 3:30 PM IST) for option chain data.
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* WAIT/AVOID Warning if applicable */}
              {(tradingSignal.action.includes('WAIT') || tradingSignal.action.includes('AVOID')) && (
                <div className={`p-3 rounded-lg border ${tradingSignal.action.includes('AVOID')
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

              {/* AMD (Manipulation) Detection Alert - NEW Feb 2026 */}
              {tradingSignal.amd_detection?.manipulation_found && (
                <div className={`p-4 rounded-lg border ${
                  tradingSignal.amd_detection.type === 'bear_trap'
                    ? 'bg-green-900/30 border-green-500/50'
                    : 'bg-red-900/30 border-red-500/50'
                }`}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">{tradingSignal.amd_detection.type === 'bear_trap' ? '🐻' : '🐂'}</span>
                    <span className={`font-bold ${
                      tradingSignal.amd_detection.type === 'bear_trap' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {tradingSignal.amd_detection.type === 'bear_trap' ? 'BEAR TRAP DETECTED' : 'BULL TRAP DETECTED'}
                    </span>
                    {tradingSignal.amd_detection.override_applied && (
                      <Badge variant="outline" className="bg-yellow-600/30 text-yellow-300 border-yellow-500">
                        OVERRIDE
                      </Badge>
                    )}
                    {tradingSignal.amd_detection.is_active && (
                      <Badge variant="outline" className="bg-blue-600/30 text-blue-300 border-blue-500 animate-pulse">
                        ACTIVE
                      </Badge>
                    )}
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="bg-muted/50 rounded p-2">
                      <div className="text-xs text-muted-foreground">Trap Level</div>
                      <div className="text-sm font-bold">₹{tradingSignal.amd_detection.level?.toLocaleString()}</div>
                    </div>
                    <div className="bg-muted/50 rounded p-2">
                      <div className="text-xs text-muted-foreground">Recovery</div>
                      <div className="text-sm font-bold text-green-400">+{tradingSignal.amd_detection.recovery_pts}pts</div>
                    </div>
                    <div className="bg-muted/50 rounded p-2">
                      <div className="text-xs text-muted-foreground">Confidence</div>
                      <div className={`text-sm font-bold ${
                        tradingSignal.amd_detection.confidence >= 80 ? 'text-green-400' : 'text-yellow-400'
                      }`}>{tradingSignal.amd_detection.confidence}%</div>
                    </div>
                  </div>
                  {tradingSignal.amd_detection.description && (
                    <div className="text-xs text-muted-foreground bg-muted/30 rounded p-2 mt-2">
                      💡 {tradingSignal.amd_detection.description}
                    </div>
                  )}
                </div>
              )}

              {/* Action & Strike */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-card rounded-lg border">
                  <div className="text-xs text-muted-foreground mb-1">What to Buy</div>
                  <div className={`text-xl md:text-2xl font-bold ${tradingSignal.action.includes('AVOID') ? 'text-red-500' :
                    tradingSignal.action.includes('WAIT') ? 'text-orange-500' :
                      tradingSignal.action.includes('BUY CALL') || (tradingSignal.type === 'CALL' && tradingSignal.action.includes('BUY')) ? 'text-green-500' :
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
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <div className="p-2 sm:p-3 bg-green-500/10 rounded-lg border border-green-500/30 text-center">
                  <div className="text-green-500 text-[10px] sm:text-xs font-medium mb-1">🎯 TARGET 1</div>
                  <div className="text-base sm:text-lg font-bold text-green-500">₹{tradingSignal.target_1.toFixed(0)}</div>
                  <div className="text-[10px] sm:text-xs text-green-400">
                    +{Math.round(((tradingSignal.target_1 - tradingSignal.entry_price) / tradingSignal.entry_price) * 100)}%
                  </div>
                </div>
                <div className="p-2 sm:p-3 bg-green-600/10 rounded-lg border border-green-600/30 text-center">
                  <div className="text-green-500 text-[10px] sm:text-xs font-medium mb-1">🎯 TARGET 2</div>
                  <div className="text-base sm:text-lg font-bold text-green-500">₹{tradingSignal.target_2.toFixed(0)}</div>
                  <div className="text-[10px] sm:text-xs text-green-400">
                    +{Math.round(((tradingSignal.target_2 - tradingSignal.entry_price) / tradingSignal.entry_price) * 100)}%
                  </div>
                </div>
                <div className="p-2 sm:p-3 bg-red-500/10 rounded-lg border border-red-500/30 text-center">
                  <div className="text-red-500 text-[10px] sm:text-xs font-medium mb-1">🛑 STOP LOSS</div>
                  <div className="text-base sm:text-lg font-bold text-red-500">₹{tradingSignal.stop_loss.toFixed(0)}</div>
                  <div className="text-[10px] sm:text-xs text-red-400">
                    -{Math.round(((tradingSignal.entry_price - tradingSignal.stop_loss) / tradingSignal.entry_price) * 100)}%
                  </div>
                </div>
                <div className="p-2 sm:p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/30 text-center">
                  <div className="text-yellow-500 text-[10px] sm:text-xs font-medium mb-1">⚖️ R:R</div>
                  <div className="text-base sm:text-lg font-bold text-yellow-500">{tradingSignal.risk_reward}</div>
                  <div className="text-[10px] sm:text-xs text-yellow-400">Favorable</div>
                </div>
              </div>

              {/* ⚡ Quick Scalp Targets - 5/10/15 Point Zones */}
              {tradingSignal.scalp_feasibility && tradingSignal.greeks?.delta && (
                <div className={`p-3 rounded-lg border ${
                  !tradingSignal.scalp_feasibility.feasible || tradingSignal.scalp_feasibility.risk_level === 'EXTREME'
                    ? 'bg-red-500/10 border-red-500/30'
                    : tradingSignal.scalp_feasibility.risk_level === 'HIGH'
                    ? 'bg-yellow-500/10 border-yellow-500/30'
                    : 'bg-cyan-500/10 border-cyan-500/30'
                }`}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-cyan-400 text-xs font-semibold">⚡ Quick Scalp Targets</span>
                      <Badge variant="outline" className="text-[10px] border-cyan-500 text-cyan-400">
                        INTRADAY
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-muted-foreground">
                        Delta: <span className="text-cyan-300 font-mono">{tradingSignal.greeks.delta.toFixed(3)}</span>
                      </span>
                      <Badge
                        variant="outline"
                        className={`text-[10px] ${
                          !tradingSignal.scalp_feasibility.feasible || tradingSignal.scalp_feasibility.risk_level === 'EXTREME'
                            ? 'border-red-500 text-red-400 bg-red-500/20'
                            : tradingSignal.scalp_feasibility.risk_level === 'HIGH'
                            ? 'border-yellow-500 text-yellow-400 bg-yellow-500/20'
                            : 'border-green-500 text-green-400 bg-green-500/20'
                        }`}
                      >
                        {!tradingSignal.scalp_feasibility.feasible || tradingSignal.scalp_feasibility.risk_level === 'EXTREME'
                          ? '⛔ HIGH RISK'
                          : tradingSignal.scalp_feasibility.risk_level === 'HIGH'
                          ? '⚠️ RISKY'
                          : '✅ VIABLE'
                        }
                      </Badge>
                    </div>
                  </div>

                  {/* Scalp Target Grid */}
                  <div className="grid grid-cols-3 gap-2 mb-2">
                    <div className="p-2 bg-green-900/40 rounded-lg border border-green-500/30 text-center">
                      <div className="text-[10px] text-green-400/70">+5 Points</div>
                      <div className="text-sm font-bold text-green-400">
                        ₹{tradingSignal.scalp_feasibility.targets.target_5.toFixed(1)}
                      </div>
                      <div className="text-[10px] text-gray-400">
                        ~{tradingSignal.scalp_feasibility.index_moves_needed.for_5_pts} idx pts
                      </div>
                    </div>
                    <div className="p-2 bg-green-900/50 rounded-lg border border-green-500/40 text-center">
                      <div className="text-[10px] text-green-400/70">+10 Points</div>
                      <div className="text-sm font-bold text-green-400">
                        ₹{tradingSignal.scalp_feasibility.targets.target_10.toFixed(1)}
                      </div>
                      <div className="text-[10px] text-gray-400">
                        ~{tradingSignal.scalp_feasibility.index_moves_needed.for_10_pts} idx pts
                      </div>
                    </div>
                    <div className="p-2 bg-green-900/60 rounded-lg border border-green-500/50 text-center">
                      <div className="text-[10px] text-green-400/70">+15 Points</div>
                      <div className="text-sm font-bold text-green-400">
                        ₹{tradingSignal.scalp_feasibility.targets.target_15.toFixed(1)}
                      </div>
                      <div className="text-[10px] text-gray-400">
                        ~{tradingSignal.scalp_feasibility.index_moves_needed.for_15_pts} idx pts
                      </div>
                    </div>
                  </div>

                  {/* Stop Loss and Per Lot Info */}
                  <div className="flex justify-between items-center text-xs">
                    <span>
                      SL: <span className="text-red-400">₹{tradingSignal.scalp_feasibility.targets.stop_loss.toFixed(1)}</span>
                    </span>
                    <span>
                      Per Lot: <span className="text-cyan-300">
                        ₹{tradingSignal.scalp_feasibility.per_lot_pnl.profit_5} - ₹{tradingSignal.scalp_feasibility.per_lot_pnl.profit_15}
                      </span>
                      {tradingSignal.scalp_feasibility.theta_impact && tradingSignal.scalp_feasibility.theta_impact.per_hour > 1.5 && (
                        <span className="text-red-400 ml-2">
                          ⏱️ θ: -₹{tradingSignal.scalp_feasibility.theta_impact.per_hour.toFixed(1)}/hr
                        </span>
                      )}
                    </span>
                  </div>

                  {/* Recommendation */}
                  {tradingSignal.scalp_feasibility.recommendation && (
                    <div className="mt-2 text-[10px] text-gray-400 border-t border-gray-700 pt-2">
                      {tradingSignal.scalp_feasibility.recommendation}
                    </div>
                  )}
                </div>
              )}

              {/* 🎯 Expiry Day Gamma Analysis - Shows only on expiry day */}
              {tradingSignal.expiry_gamma_analysis && (
                <div className={`p-3 rounded-lg border ${
                  tradingSignal.expiry_gamma_analysis.is_gamma_opportunity
                    ? 'bg-green-500/10 border-green-500/30'
                    : tradingSignal.expiry_gamma_analysis.gamma_score >= 50
                    ? 'bg-yellow-500/10 border-yellow-500/30'
                    : 'bg-orange-500/10 border-orange-500/30'
                }`}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-orange-400 text-xs font-semibold">🎯 Expiry Day Gamma Analysis</span>
                      <Badge variant="outline" className={`text-[10px] ${
                        tradingSignal.expiry_gamma_analysis.is_gamma_window
                          ? 'border-green-500 text-green-400 bg-green-500/20'
                          : 'border-gray-500 text-gray-400'
                      }`}>
                        {tradingSignal.expiry_gamma_analysis.market_phase.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-muted-foreground">
                        Gamma Score: <span className={`font-mono font-bold ${
                          tradingSignal.expiry_gamma_analysis.gamma_score >= 70 ? 'text-green-400' :
                          tradingSignal.expiry_gamma_analysis.gamma_score >= 50 ? 'text-yellow-400' :
                          'text-orange-400'
                        }`}>{tradingSignal.expiry_gamma_analysis.gamma_score}/100</span>
                      </span>
                      <Badge
                        variant="outline"
                        className={`text-[10px] ${
                          tradingSignal.expiry_gamma_analysis.is_gamma_opportunity
                            ? 'border-green-500 text-green-400 bg-green-500/20'
                            : 'border-orange-500 text-orange-400 bg-orange-500/20'
                        }`}
                      >
                        {tradingSignal.expiry_gamma_analysis.is_gamma_opportunity ? '🚀 GAMMA PLAY' : '⚠️ NOT IDEAL'}
                      </Badge>
                    </div>
                  </div>

                  {/* Gamma Metrics Grid */}
                  <div className="grid grid-cols-4 gap-2 mb-3">
                    <div className="p-2 bg-purple-900/40 rounded-lg border border-purple-500/30 text-center">
                      <div className="text-[10px] text-purple-400/70">R:R Ratio</div>
                      <div className="text-sm font-bold text-purple-400">
                        {tradingSignal.expiry_gamma_analysis.risk_reward.toFixed(1)}:1
                      </div>
                    </div>
                    <div className="p-2 bg-cyan-900/40 rounded-lg border border-cyan-500/30 text-center">
                      <div className="text-[10px] text-cyan-400/70">Gamma 🔥</div>
                      <div className="text-sm font-bold text-cyan-400">
                        {tradingSignal.expiry_gamma_analysis.gamma_multiplier.toFixed(1)}x
                      </div>
                    </div>
                    <div className="p-2 bg-green-900/40 rounded-lg border border-green-500/30 text-center">
                      <div className="text-[10px] text-green-400/70">+50pt Move</div>
                      <div className="text-sm font-bold text-green-400">
                        ₹{tradingSignal.expiry_gamma_analysis.potential_gain_50pt.toFixed(0)}
                      </div>
                    </div>
                    <div className="p-2 bg-green-900/50 rounded-lg border border-green-500/40 text-center">
                      <div className="text-[10px] text-green-400/70">+100pt Move</div>
                      <div className="text-sm font-bold text-green-400">
                        ₹{tradingSignal.expiry_gamma_analysis.potential_gain_100pt.toFixed(0)}
                      </div>
                    </div>
                  </div>

                  {/* Theta Decay Schedule */}
                  {tradingSignal.expiry_gamma_analysis.theta_decay_schedule.length > 0 && (
                    <div className="mb-3">
                      <div className="text-[10px] text-gray-400 mb-2">📉 Theta Decay Schedule (15-min intervals)</div>
                      <div className="grid grid-cols-4 gap-1">
                        {tradingSignal.expiry_gamma_analysis.theta_decay_schedule.map((interval, idx) => (
                          <div key={idx} className={`p-1.5 rounded text-center ${
                            interval.rate === 'EXTREME' ? 'bg-red-900/40 border border-red-500/30' :
                            interval.rate === 'VERY_HIGH' ? 'bg-orange-900/40 border border-orange-500/30' :
                            'bg-yellow-900/40 border border-yellow-500/30'
                          }`}>
                            <div className="text-[9px] text-gray-400">{interval.time}</div>
                            <div className="text-[10px] font-bold text-white">₹{interval.premium.toFixed(0)}</div>
                            <div className={`text-[9px] ${
                              interval.rate === 'EXTREME' ? 'text-red-400' :
                              interval.rate === 'VERY_HIGH' ? 'text-orange-400' :
                              'text-yellow-400'
                            }`}>-₹{interval.decay.toFixed(1)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Trading Advice */}
                  <div className="border-t border-gray-700 pt-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-400">
                        {tradingSignal.expiry_gamma_analysis.trading_advice.gamma_play_viable 
                          ? '✅ Gamma play viable' 
                          : '⚠️ Premium too high for gamma play'}
                      </span>
                      <span className="text-cyan-400">
                        {tradingSignal.expiry_gamma_analysis.trading_advice.ideal_premium_range}
                      </span>
                    </div>
                    <div className="text-[10px] text-gray-500 mt-1">
                      💡 {tradingSignal.expiry_gamma_analysis.trading_advice.key_insight}
                    </div>
                  </div>
                </div>
              )}

              {/* 🧠 Enhanced ML Prediction Panel - NEW Feb 2026 */}
              {tradingSignal.enhanced_ml_prediction && (
                <div className="p-3 rounded-lg border bg-gradient-to-r from-purple-500/10 to-blue-500/10 border-purple-500/30">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-purple-400 text-xs font-semibold">🧠 Enhanced ML Analysis</span>
                      {tradingSignal.enhanced_ml_prediction.simulation && (
                        <Badge variant="outline" className={`text-[10px] ${
                          tradingSignal.enhanced_ml_prediction.simulation.grade === 'A+' || tradingSignal.enhanced_ml_prediction.simulation.grade === 'A'
                            ? 'border-green-500 text-green-400 bg-green-500/20'
                            : tradingSignal.enhanced_ml_prediction.simulation.grade === 'B+' || tradingSignal.enhanced_ml_prediction.simulation.grade === 'B'
                            ? 'border-yellow-500 text-yellow-400 bg-yellow-500/20'
                            : 'border-red-500 text-red-400 bg-red-500/20'
                        }`}>
                          Grade {tradingSignal.enhanced_ml_prediction.simulation.grade}
                        </Badge>
                      )}
                    </div>
                    {tradingSignal.enhanced_ml_prediction.combined_recommendation && (
                      <Badge
                        variant="outline"
                        className={`text-[10px] ${
                          tradingSignal.enhanced_ml_prediction.combined_recommendation.action === 'BUY'
                            ? 'border-green-500 text-green-400 bg-green-500/20'
                            : tradingSignal.enhanced_ml_prediction.combined_recommendation.action === 'BUY_CAUTIOUS'
                            ? 'border-yellow-500 text-yellow-400 bg-yellow-500/20'
                            : 'border-red-500 text-red-400 bg-red-500/20'
                        }`}
                      >
                        {tradingSignal.enhanced_ml_prediction.combined_recommendation.action === 'BUY' ? '✅ BUY' :
                         tradingSignal.enhanced_ml_prediction.combined_recommendation.action === 'BUY_CAUTIOUS' ? '⚠️ CAUTIOUS' :
                         '🚫 AVOID'}
                      </Badge>
                    )}
                  </div>

                  {/* ML Prediction Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
                    {/* Direction Prediction */}
                    {tradingSignal.enhanced_ml_prediction.direction_prediction && (
                      <div className="p-2 bg-blue-900/40 rounded-lg border border-blue-500/30 text-center">
                        <div className="text-[10px] text-blue-400/70">📈 Direction</div>
                        <div className={`text-sm font-bold ${
                          tradingSignal.enhanced_ml_prediction.direction_prediction.direction.includes('UP') ? 'text-green-400' :
                          tradingSignal.enhanced_ml_prediction.direction_prediction.direction.includes('DOWN') ? 'text-red-400' :
                          'text-gray-400'
                        }`}>
                          {tradingSignal.enhanced_ml_prediction.direction_prediction.direction}
                        </div>
                        <div className="text-[9px] text-gray-400">
                          {((tradingSignal.enhanced_ml_prediction.direction_prediction.confidence ?? 0) * 100).toFixed(0)}% conf
                        </div>
                      </div>
                    )}

                    {/* Speed Prediction */}
                    {tradingSignal.enhanced_ml_prediction.speed_prediction && (
                      <div className={`p-2 rounded-lg border text-center ${
                        tradingSignal.enhanced_ml_prediction.speed_prediction.category === 'EXPLOSIVE' ? 'bg-green-900/40 border-green-500/30' :
                        tradingSignal.enhanced_ml_prediction.speed_prediction.category === 'FAST' ? 'bg-green-900/30 border-green-500/20' :
                        tradingSignal.enhanced_ml_prediction.speed_prediction.category === 'SLOW' || tradingSignal.enhanced_ml_prediction.speed_prediction.category === 'CHOPPY' ? 'bg-red-900/40 border-red-500/30' :
                        'bg-yellow-900/40 border-yellow-500/30'
                      }`}>
                        <div className="text-[10px] text-cyan-400/70">⚡ Speed</div>
                        <div className={`text-sm font-bold ${
                          tradingSignal.enhanced_ml_prediction.speed_prediction.category === 'EXPLOSIVE' || tradingSignal.enhanced_ml_prediction.speed_prediction.category === 'FAST' ? 'text-green-400' :
                          tradingSignal.enhanced_ml_prediction.speed_prediction.category === 'SLOW' || tradingSignal.enhanced_ml_prediction.speed_prediction.category === 'CHOPPY' ? 'text-red-400' :
                          'text-yellow-400'
                        }`}>
                          {tradingSignal.enhanced_ml_prediction.speed_prediction.category}
                        </div>
                        <div className="text-[9px] text-gray-400">
                          {tradingSignal.enhanced_ml_prediction.speed_prediction.expected_time_mins ?? 0}min
                        </div>
                      </div>
                    )}

                    {/* IV Prediction */}
                    {tradingSignal.enhanced_ml_prediction.iv_prediction && (
                      <div className={`p-2 rounded-lg border text-center ${
                        tradingSignal.enhanced_ml_prediction.iv_prediction.direction === 'CRUSH' || tradingSignal.enhanced_ml_prediction.iv_prediction.direction === 'CONTRACT' ? 'bg-red-900/40 border-red-500/30' :
                        tradingSignal.enhanced_ml_prediction.iv_prediction.direction === 'SPIKE' || tradingSignal.enhanced_ml_prediction.iv_prediction.direction === 'EXPAND' ? 'bg-green-900/40 border-green-500/30' :
                        'bg-gray-900/40 border-gray-500/30'
                      }`}>
                        <div className="text-[10px] text-orange-400/70">📊 IV</div>
                        <div className={`text-sm font-bold ${
                          tradingSignal.enhanced_ml_prediction.iv_prediction.direction === 'CRUSH' || tradingSignal.enhanced_ml_prediction.iv_prediction.direction === 'CONTRACT' ? 'text-red-400' :
                          tradingSignal.enhanced_ml_prediction.iv_prediction.direction === 'SPIKE' || tradingSignal.enhanced_ml_prediction.iv_prediction.direction === 'EXPAND' ? 'text-green-400' :
                          'text-gray-400'
                        }`}>
                          {tradingSignal.enhanced_ml_prediction.iv_prediction.direction}
                        </div>
                        <div className="text-[9px] text-gray-400">
                          {(tradingSignal.enhanced_ml_prediction.iv_prediction.expected_change_pct ?? 0) > 0 ? '+' : ''}{(tradingSignal.enhanced_ml_prediction.iv_prediction.expected_change_pct ?? 0).toFixed(0)}%
                        </div>
                      </div>
                    )}

                    {/* Simulation Expected P&L */}
                    {tradingSignal.enhanced_ml_prediction.simulation && (
                      <div className={`p-2 rounded-lg border text-center ${
                        (tradingSignal.enhanced_ml_prediction.simulation.expected_pnl_pct ?? 0) > 10 ? 'bg-green-900/40 border-green-500/30' :
                        (tradingSignal.enhanced_ml_prediction.simulation.expected_pnl_pct ?? 0) > 0 ? 'bg-green-900/20 border-green-500/20' :
                        'bg-red-900/40 border-red-500/30'
                      }`}>
                        <div className="text-[10px] text-green-400/70">💰 Expected</div>
                        <div className={`text-sm font-bold ${
                          (tradingSignal.enhanced_ml_prediction.simulation.expected_pnl_pct ?? 0) > 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {(tradingSignal.enhanced_ml_prediction.simulation.expected_pnl_pct ?? 0) > 0 ? '+' : ''}{(tradingSignal.enhanced_ml_prediction.simulation.expected_pnl_pct ?? 0).toFixed(1)}%
                        </div>
                        <div className="text-[9px] text-gray-400">
                          {((tradingSignal.enhanced_ml_prediction.simulation.win_probability ?? 0) * 100).toFixed(0)}% win
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Speed Reasoning & Warnings */}
                  {tradingSignal.enhanced_ml_prediction.speed_prediction?.reasoning && tradingSignal.enhanced_ml_prediction.speed_prediction.reasoning.length > 0 && (
                    <div className="mb-2 text-[10px] text-gray-400">
                      <div className="font-semibold mb-1">Speed Analysis:</div>
                      {tradingSignal.enhanced_ml_prediction.speed_prediction.reasoning.slice(0, 2).map((reason, idx) => (
                        <div key={idx} className="ml-2">• {reason}</div>
                      ))}
                    </div>
                  )}

                  {/* Combined Recommendation Warnings */}
                  {tradingSignal.enhanced_ml_prediction.combined_recommendation?.warnings && tradingSignal.enhanced_ml_prediction.combined_recommendation.warnings.length > 0 && (
                    <div className="border-t border-purple-500/30 pt-2">
                      <div className="text-[10px] text-yellow-400">
                        {tradingSignal.enhanced_ml_prediction.combined_recommendation.warnings.map((warning, idx) => (
                          <div key={idx}>{warning}</div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Simulation Trade Advice */}
                  {tradingSignal.enhanced_ml_prediction.simulation && (
                    <div className="border-t border-purple-500/30 pt-2 mt-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-400">
                          {tradingSignal.enhanced_ml_prediction.simulation.should_trade 
                            ? '✅ Trade viable' 
                            : '🚫 Not recommended'}
                        </span>
                        <span className="text-purple-400">
                          SL: ₹{(tradingSignal.enhanced_ml_prediction.simulation.stop_loss ?? 0).toFixed(0)} | TP: ₹{(tradingSignal.enhanced_ml_prediction.simulation.take_profit ?? 0).toFixed(0)}
                        </span>
                      </div>
                      <div className="text-[10px] text-gray-500 mt-1">
                        ⏱️ Max hold: {tradingSignal.enhanced_ml_prediction.simulation.max_hold_time_mins ?? 0} mins | 📊 Position: {tradingSignal.enhanced_ml_prediction.simulation.position_size_pct ?? 0}% of capital
                      </div>
                    </div>
                  )}
                </div>
              )}

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

              {/* ============ NEW: TRADE RECOMMENDATION VERDICT ============ */}
              {tradingSignal.trade_recommendation && (
                <div className={`p-3 rounded-lg border ${tradingSignal.trade_recommendation.verdict === 'TRADE' ? 'bg-green-500/10 border-green-500/30' :
                  tradingSignal.trade_recommendation.verdict === 'WAIT' ? 'bg-yellow-500/10 border-yellow-500/30' :
                    'bg-red-500/10 border-red-500/30'
                  }`}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm font-medium flex items-center gap-2">
                      {tradingSignal.trade_recommendation.verdict === 'TRADE' ? '✅' : tradingSignal.trade_recommendation.verdict === 'WAIT' ? '⏳' : '⛔'}
                      Trade Verdict: <span className={
                        tradingSignal.trade_recommendation.verdict === 'TRADE' ? 'text-green-400' :
                          tradingSignal.trade_recommendation.verdict === 'WAIT' ? 'text-yellow-400' : 'text-red-400'
                      }>{tradingSignal.trade_recommendation.verdict}</span>
                    </div>
                    <Badge variant="outline" className={`text-xs ${tradingSignal.trade_recommendation.risk_level === 'LOW' ? 'border-green-500 text-green-500' :
                      tradingSignal.trade_recommendation.risk_level === 'MEDIUM' ? 'border-yellow-500 text-yellow-500' :
                        'border-red-500 text-red-500'
                      }`}>
                      Risk: {tradingSignal.trade_recommendation.risk_level}
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground space-y-1">
                    {tradingSignal.trade_recommendation.reasons?.map((reason, idx) => (
                      <p key={idx}>{reason}</p>
                    ))}
                  </div>
                  <div className="mt-2 text-xs font-medium text-slate-300">
                    Position Size: {tradingSignal.trade_recommendation.position_size_advice}
                  </div>
                </div>
              )}

              {/* ============ NEW: GREEKS ANALYSIS ============ */}
              {tradingSignal.greeks && (
                <div className="p-3 bg-violet-500/10 rounded-lg border border-violet-500/30">
                  <div className="text-sm font-medium text-violet-300 mb-3 flex items-center gap-2">
                    📐 Option Greeks
                    <span className="text-xs bg-violet-600/30 px-2 py-0.5 rounded">LIVE</span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 mb-3">
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Delta</div>
                      <div className={`text-lg font-bold ${tradingSignal.greeks.delta < 0 ? 'text-red-400' : 'text-green-400'}`}>
                        {tradingSignal.greeks.delta.toFixed(3)}
                      </div>
                    </div>
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Gamma</div>
                      <div className="text-lg font-bold text-blue-400">
                        {tradingSignal.greeks.gamma.toFixed(4)}
                      </div>
                    </div>
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Theta</div>
                      <div className="text-lg font-bold text-red-400">
                        {tradingSignal.greeks.theta.toFixed(2)}
                      </div>
                    </div>
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Vega</div>
                      <div className="text-lg font-bold text-purple-400">
                        {tradingSignal.greeks.vega.toFixed(2)}
                      </div>
                    </div>
                  </div>
                  {tradingSignal.greeks.interpretation && (
                    <div className="text-xs text-violet-200 space-y-1">
                      <p>📊 {tradingSignal.greeks.interpretation.delta_meaning}</p>
                      <p>⏰ {tradingSignal.greeks.interpretation.theta_meaning}</p>
                    </div>
                  )}
                </div>
              )}

              {/* ============ NEW: ML ANALYSIS ============ */}
              {tradingSignal.ml_analysis && tradingSignal.ml_analysis.enabled && (
                <div className={`p-3 rounded-lg border ${tradingSignal.ml_analysis.direction === 'bullish' ? 'bg-green-500/10 border-green-500/30' :
                  tradingSignal.ml_analysis.direction === 'bearish' ? 'bg-red-500/10 border-red-500/30' :
                    'bg-slate-500/10 border-slate-500/30'
                  }`}>
                  <div className="text-sm font-medium mb-3 flex items-center gap-2">
                    🤖 ML Prediction
                    <Badge variant="outline" className={`text-xs ${tradingSignal.ml_analysis.status === 'ACTIVE' ? 'border-green-500 text-green-500' : 'border-yellow-500 text-yellow-500'
                      }`}>
                      {tradingSignal.ml_analysis.status}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-2 mb-2">
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Direction</div>
                      <div className={`text-base font-bold ${tradingSignal.ml_analysis.direction === 'bullish' ? 'text-green-400' :
                        tradingSignal.ml_analysis.direction === 'bearish' ? 'text-red-400' : 'text-slate-400'
                        }`}>
                        {tradingSignal.ml_analysis.direction?.toUpperCase()}
                      </div>
                    </div>
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Confidence</div>
                      <div className="text-base font-bold text-blue-400">
                        {tradingSignal.ml_analysis.confidence}%
                      </div>
                    </div>
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Predicted</div>
                      <div className="text-base font-bold text-primary">
                        ₹{tradingSignal.ml_analysis.predicted_price?.toFixed(0)}
                      </div>
                    </div>
                  </div>
                  {tradingSignal.ml_analysis.models && (
                    <div className="flex gap-2 mb-2">
                      <Badge variant="outline" className="text-xs">
                        ARIMA: {tradingSignal.ml_analysis.models.arima}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        Momentum: {tradingSignal.ml_analysis.models.momentum}
                      </Badge>
                    </div>
                  )}
                  {tradingSignal.ml_analysis.warning && (
                    <div className="text-xs text-yellow-400">
                      {tradingSignal.ml_analysis.warning}
                    </div>
                  )}
                </div>
              )}

              {/* ============ NEW: THETA/EXPIRY ANALYSIS ============ */}
              {tradingSignal.theta_analysis && (
                <div className={`p-3 rounded-lg border ${tradingSignal.theta_analysis.risk_level === 'LOW' ? 'bg-green-500/10 border-green-500/30' :
                  tradingSignal.theta_analysis.risk_level?.includes('MEDIUM') ? 'bg-yellow-500/10 border-yellow-500/30' :
                    'bg-red-500/10 border-red-500/30'
                  }`}>
                  <div className="text-sm font-medium mb-3 flex items-center gap-2">
                    ⏱️ Time Decay Analysis
                    <Badge variant="outline" className="text-xs">
                      {tradingSignal.theta_analysis.decay_phase}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-2 mb-2">
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Daily Decay</div>
                      <div className="text-base font-bold text-red-400">
                        -{tradingSignal.theta_analysis.daily_decay_pct}%
                      </div>
                    </div>
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Hourly</div>
                      <div className="text-base font-bold text-orange-400">
                        -₹{Math.abs(tradingSignal.theta_analysis.theta_per_hour).toFixed(1)}/hr
                      </div>
                    </div>
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Risk</div>
                      <div className={`text-base font-bold ${tradingSignal.theta_analysis.risk_level === 'LOW' ? 'text-green-400' :
                        tradingSignal.theta_analysis.risk_level?.includes('MEDIUM') ? 'text-yellow-400' : 'text-red-400'
                        }`}>
                        {tradingSignal.theta_analysis.risk_level}
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground space-y-1">
                    <p>💡 {tradingSignal.theta_analysis.advice}</p>
                    <p>📅 {tradingSignal.theta_analysis.strategy_recommendation}</p>
                  </div>
                </div>
              )}

              {/* ============ NEW: MARKET CONTEXT ============ */}
              {tradingSignal.market_context && (
                <div className="p-3 bg-slate-500/10 rounded-lg border border-slate-500/30">
                  <div className="text-sm font-medium text-slate-300 mb-3">📈 Market Context</div>
                  <div className="grid grid-cols-4 gap-2 mb-3">
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Spot</div>
                      <div className="text-sm font-bold">₹{tradingSignal.market_context.spot_price?.toFixed(0)}</div>
                    </div>
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">VIX</div>
                      <div className={`text-sm font-bold ${tradingSignal.market_context.vix > 20 ? 'text-red-400' : 'text-green-400'}`}>
                        {tradingSignal.market_context.vix?.toFixed(1)}
                      </div>
                    </div>
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">PCR (OI)</div>
                      <div className={`text-sm font-bold ${tradingSignal.market_context.pcr_oi > 1 ? 'text-green-400' : 'text-red-400'}`}>
                        {tradingSignal.market_context.pcr_oi?.toFixed(2)}
                      </div>
                    </div>
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Max Pain</div>
                      <div className="text-sm font-bold">₹{tradingSignal.market_context.max_pain}</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="text-xs">
                      <span className="text-muted-foreground">Supports: </span>
                      <span className="text-green-400">
                        {tradingSignal.market_context.support_levels?.slice(0, 3).join(', ')}
                      </span>
                    </div>
                    <div className="text-xs">
                      <span className="text-muted-foreground">Resistances: </span>
                      <span className="text-red-400">
                        {tradingSignal.market_context.resistance_levels?.slice(0, 3).join(', ')}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* ============ NEW: PROBABILITY ANALYSIS WITH TOP MOVERS ============ */}
              {tradingSignal.probability_analysis && (
                <div className="p-3 bg-indigo-500/10 rounded-lg border border-indigo-500/30">
                  <div className="text-sm font-medium text-indigo-300 mb-3 flex items-center justify-between">
                    <span>📊 Constituent Analysis ({tradingSignal.probability_analysis.stocks_scanned} stocks)</span>
                    <Badge variant="outline" className="text-xs">
                      {tradingSignal.probability_analysis.market_regime}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-4 gap-2 mb-3">
                    <div className="p-2 bg-green-500/10 rounded border border-green-500/20 text-center">
                      <div className="text-xs text-muted-foreground">Bullish</div>
                      <div className="text-lg font-bold text-green-400">{tradingSignal.probability_analysis.bullish_pct}%</div>
                    </div>
                    <div className="p-2 bg-red-500/10 rounded border border-red-500/20 text-center">
                      <div className="text-xs text-muted-foreground">Bearish</div>
                      <div className="text-lg font-bold text-red-400">{tradingSignal.probability_analysis.bearish_pct}%</div>
                    </div>
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Expected Move</div>
                      <div className={`text-lg font-bold ${tradingSignal.probability_analysis.expected_move_pct > 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {tradingSignal.probability_analysis.expected_move_pct > 0 ? '+' : ''}{tradingSignal.probability_analysis.expected_move_pct?.toFixed(2)}%
                      </div>
                    </div>
                    <div className="p-2 bg-primary/10 rounded border border-primary/20 text-center">
                      <div className="text-xs text-muted-foreground">Recommended</div>
                      <div className="text-lg font-bold text-primary">{tradingSignal.probability_analysis.constituent_recommendation}</div>
                    </div>
                  </div>
                  {/* Top Movers */}
                  {tradingSignal.probability_analysis.top_movers && (
                    <div className="grid grid-cols-3 gap-2">
                      <div className="p-2 bg-green-500/5 rounded border border-green-500/10">
                        <div className="text-xs text-green-400 mb-1">🐂 Top Bullish</div>
                        {tradingSignal.probability_analysis.top_movers.bullish?.slice(0, 3).map((stock, idx) => (
                          <div key={idx} className="text-xs text-muted-foreground">
                            {stock.symbol}: {stock.probability.toFixed(0)}%
                          </div>
                        ))}
                      </div>
                      <div className="p-2 bg-red-500/5 rounded border border-red-500/10">
                        <div className="text-xs text-red-400 mb-1">🐻 Top Bearish</div>
                        {tradingSignal.probability_analysis.top_movers.bearish?.slice(0, 3).map((stock, idx) => (
                          <div key={idx} className="text-xs text-muted-foreground">
                            {stock.symbol}: {stock.probability.toFixed(0)}%
                          </div>
                        ))}
                      </div>
                      <div className="p-2 bg-yellow-500/5 rounded border border-yellow-500/10">
                        <div className="text-xs text-yellow-400 mb-1">📈 Volume Surge</div>
                        {tradingSignal.probability_analysis.top_movers.volume_surge?.slice(0, 3).map((stock, idx) => (
                          <div key={idx} className="text-xs text-muted-foreground">
                            {stock.symbol}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* ============ DIVERGENCE WARNING ============ */}
                  {/* Show warning when signal direction conflicts with constituent sentiment */}
                  {(() => {
                    const signalAction = tradingSignal.action?.toUpperCase();
                    const constituentRec = tradingSignal.probability_analysis.constituent_recommendation?.toUpperCase();
                    const bullishPct = tradingSignal.probability_analysis.bullish_pct || 0;
                    const bearishPct = tradingSignal.probability_analysis.bearish_pct || 0;
                    
                    // Detect divergence: Signal says one thing, constituents say another
                    const signalIsBullish = signalAction === 'CALL' || signalAction === 'BUY';
                    const signalIsBearish = signalAction === 'PUT' || signalAction === 'SELL';
                    const constituentsBullish = bullishPct > 55; // More than 55% stocks bullish
                    const constituentsBearish = bearishPct > 55; // More than 55% stocks bearish
                    
                    const hasDivergence = (signalIsBullish && constituentsBearish) || (signalIsBearish && constituentsBullish);
                    
                    if (hasDivergence) {
                      const divergenceText = signalIsBearish && constituentsBullish
                        ? `Signal suggests ${signalAction} (bearish), but ${bullishPct.toFixed(0)}% of constituent stocks are bullish`
                        : `Signal suggests ${signalAction} (bullish), but ${bearishPct.toFixed(0)}% of constituent stocks are bearish`;
                      
                      return (
                        <div className="mt-3 p-3 bg-orange-500/20 rounded-lg border-2 border-orange-500/50 animate-pulse">
                          <div className="flex items-center gap-2">
                            <span className="text-2xl">⚠️</span>
                            <div>
                              <div className="text-sm font-bold text-orange-400">SIGNAL ↔ CONSTITUENT DIVERGENCE</div>
                              <div className="text-xs text-orange-300 mt-1">{divergenceText}</div>
                              <div className="text-xs text-orange-200/70 mt-1">
                                💡 This mismatch often indicates a potential trap or low-conviction setup. Consider waiting for alignment.
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  })()}
                </div>
              )}

              {/* ============ NEW: MTF ANALYSIS ============ */}
              {tradingSignal.mtf_analysis && (
                <div className="p-3 bg-cyan-500/10 rounded-lg border border-cyan-500/30">
                  <div className="text-sm font-medium text-cyan-300 mb-3 flex items-center gap-2">
                    📊 Multi-Timeframe Analysis
                    <Badge variant="outline" className={`text-xs ${tradingSignal.mtf_analysis.overall_bias === 'bullish' ? 'border-green-500 text-green-500' :
                      tradingSignal.mtf_analysis.overall_bias === 'bearish' ? 'border-red-500 text-red-500' :
                        'border-yellow-500 text-yellow-500'
                      }`}>
                      {tradingSignal.mtf_analysis.overall_bias?.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-1 mb-2">
                    {tradingSignal.mtf_analysis.timeframes_analyzed?.map((tf, idx) => (
                      <Badge key={idx} variant="outline" className="text-xs">
                        {tf === 'M' ? 'Monthly' : tf === 'W' ? 'Weekly' : tf === 'D' ? 'Daily' : `${tf}m`}
                      </Badge>
                    ))}
                  </div>
                  {/* Trend Reversal */}
                  {tradingSignal.mtf_analysis.trend_reversal?.is_reversal && (
                    <div className={`p-2 rounded border ${tradingSignal.mtf_analysis.trend_reversal.direction.includes('BULLISH') ? 'bg-green-500/10 border-green-500/20' : 'bg-red-500/10 border-red-500/20'
                      }`}>
                      <div className="text-xs font-medium mb-1">
                        🔄 {tradingSignal.mtf_analysis.trend_reversal.direction}
                        <span className="ml-2 text-muted-foreground">
                          ({tradingSignal.mtf_analysis.trend_reversal.confidence}% confidence)
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {tradingSignal.mtf_analysis.trend_reversal.reason}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Signaling TFs: {tradingSignal.mtf_analysis.trend_reversal.timeframes_signaling?.join(', ')}
                      </div>
                    </div>
                  )}
                  {/* Confluence Zones */}
                  {tradingSignal.mtf_analysis.confluence_zones && tradingSignal.mtf_analysis.confluence_zones.length > 0 && (
                    <div className="mt-2">
                      <div className="text-xs text-muted-foreground mb-1">Key Confluence Zones:</div>
                      <div className="space-y-1">
                        {tradingSignal.mtf_analysis.confluence_zones.slice(0, 2).map((zone, idx) => (
                          <div key={idx} className="text-xs flex justify-between">
                            <span>₹{zone.center.toFixed(0)} ({zone.timeframes.join('+')})</span>
                            <span className={zone.distance_pct < 0 ? 'text-green-400' : 'text-red-400'}>
                              {zone.distance_pct > 0 ? '+' : ''}{zone.distance_pct.toFixed(1)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* ============ NEW: FVG SETUP DETAILS ============ */}
              {tradingSignal.setup_details && (
                <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/30">
                  <div className="text-sm font-medium text-amber-300 mb-2 flex items-center gap-2">
                    📍 ICT FVG Setup
                    <Badge variant="outline" className="text-xs">
                      {tradingSignal.setup_details.confidence_level}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-2 mb-2">
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">FVG Level</div>
                      <div className="text-sm font-bold">₹{tradingSignal.setup_details.fvg_level?.toFixed(0)}</div>
                    </div>
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Timeframe</div>
                      <div className="text-sm font-bold">{tradingSignal.setup_details.timeframe}m</div>
                    </div>
                    <div className="p-2 bg-card rounded border text-center">
                      <div className="text-xs text-muted-foreground">Probability</div>
                      <div className="text-sm font-bold text-primary">{tradingSignal.setup_details.reversal_probability}%</div>
                    </div>
                  </div>
                  {tradingSignal.setup_details.four_hour_fvg?.detected && (
                    <div className="text-xs text-amber-200">
                      {tradingSignal.setup_details.four_hour_fvg.direction_message}
                    </div>
                  )}
                  <div className="text-xs text-muted-foreground mt-1">
                    {tradingSignal.setup_details.reasoning}
                  </div>
                </div>
              )}

              {/* Trading Mode & Session */}
              {tradingSignal.trading_mode && (
                <div className="p-3 bg-orange-500/10 rounded-lg border border-orange-500/30">
                  <div className="text-xs text-muted-foreground mb-1">⏰ {tradingSignal.trading_mode.mode} Trading</div>
                  <div className="text-xs text-orange-300 space-y-1">
                    <p>• {tradingSignal.trading_mode.description}</p>
                    <p>• Entry Window: {tradingSignal.trading_mode.entry_window}</p>
                    <p>• Max Hold: {tradingSignal.trading_mode.max_hold}</p>
                    {tradingSignal.entry_session && !tradingSignal.entry_session.can_trade && (
                      <p className="text-yellow-400 font-medium">⚠️ {tradingSignal.entry_session.advice}</p>
                    )}
                  </div>
                </div>
              )}

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
                    <p className={`font-medium ${['A', 'B'].includes((tradingSignal as any).entry_grade) ? 'text-green-500' :
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

              {/* NEW: Option Chart Analysis - Support/Resistance & Pullback */}
              {(tradingSignal as any).entry_analysis?.option_supports && (
                <div className="p-3 bg-indigo-500/10 rounded-lg border border-indigo-500/30">
                  <div className="text-sm font-medium text-indigo-300 mb-3 flex items-center gap-2">
                    📊 Option Chart Analysis
                    <span className="text-xs bg-indigo-600/30 px-2 py-0.5 rounded">NEW</span>
                  </div>

                  {/* Support & Resistance on Option Chart */}
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="p-2 bg-green-500/10 rounded border border-green-500/20">
                      <div className="text-xs text-muted-foreground mb-1">Option Support Levels</div>
                      <div className="space-y-1">
                        {((tradingSignal as any).entry_analysis.option_supports || []).slice(0, 3).map((level: number, idx: number) => (
                          <div key={idx} className="text-sm font-semibold text-green-400">
                            ₹{level.toFixed(0)} {idx === 0 && <span className="text-xs">(Nearest)</span>}
                          </div>
                        ))}
                      </div>
                      <div className="text-xs text-green-300 mt-1">
                        💡 Place SL below these
                      </div>
                    </div>
                    <div className="p-2 bg-red-500/10 rounded border border-red-500/20">
                      <div className="text-xs text-muted-foreground mb-1">Option Resistance Levels</div>
                      <div className="space-y-1">
                        {((tradingSignal as any).entry_analysis.option_resistances || []).slice(0, 3).map((level: number, idx: number) => (
                          <div key={idx} className="text-sm font-semibold text-red-400">
                            ₹{level.toFixed(0)} {idx === 0 && <span className="text-xs">(Target)</span>}
                          </div>
                        ))}
                      </div>
                      <div className="text-xs text-red-300 mt-1">
                        🎯 Book profit near these
                      </div>
                    </div>
                  </div>

                  {/* Chart-based Targets */}
                  {(tradingSignal as any).entry_analysis.option_target_1 && (
                    <div className="grid grid-cols-3 gap-2 mb-3">
                      <div className="p-2 bg-green-600/10 rounded border border-green-600/20 text-center">
                        <div className="text-xs text-muted-foreground">Chart Target 1</div>
                        <div className="text-lg font-bold text-green-400">
                          ₹{(tradingSignal as any).entry_analysis.option_target_1?.toFixed(0)}
                        </div>
                      </div>
                      <div className="p-2 bg-green-700/10 rounded border border-green-700/20 text-center">
                        <div className="text-xs text-muted-foreground">Chart Target 2</div>
                        <div className="text-lg font-bold text-green-400">
                          ₹{(tradingSignal as any).entry_analysis.option_target_2?.toFixed(0)}
                        </div>
                      </div>
                      <div className="p-2 bg-red-600/10 rounded border border-red-600/20 text-center">
                        <div className="text-xs text-muted-foreground">Chart Stop Loss</div>
                        <div className="text-lg font-bold text-red-400">
                          ₹{(tradingSignal as any).entry_analysis.option_stop_loss?.toFixed(0)}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Pullback Analysis */}
                  {(tradingSignal as any).entry_analysis.pullback_probability !== undefined && (
                    <div className={`p-2 rounded border ${(tradingSignal as any).entry_analysis.wait_for_pullback
                      ? 'bg-orange-500/10 border-orange-500/30'
                      : 'bg-green-500/10 border-green-500/30'
                      }`}>
                      <div className="flex justify-between items-center">
                        <div>
                          <div className="text-xs text-muted-foreground">Pullback Analysis</div>
                          <div className={`text-sm font-semibold ${(tradingSignal as any).entry_analysis.wait_for_pullback ? 'text-orange-400' : 'text-green-400'
                            }`}>
                            {(tradingSignal as any).entry_analysis.wait_for_pullback
                              ? `⏳ Wait for pullback (${((tradingSignal as any).entry_analysis.pullback_probability * 100).toFixed(0)}% likely)`
                              : '✅ Good to enter now'
                            }
                          </div>
                        </div>
                        {(tradingSignal as any).entry_analysis.limit_order_price && (tradingSignal as any).entry_analysis.wait_for_pullback && (
                          <div className="text-right">
                            <div className="text-xs text-muted-foreground">Limit Order</div>
                            <div className="text-lg font-bold text-orange-400">
                              ₹{(tradingSignal as any).entry_analysis.limit_order_price?.toFixed(0)}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="mt-2 text-xs text-indigo-300/70">
                    💡 These levels are from option price chart analysis, not spot index
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* ============ SCAN OPPORTUNITIES WIDGET - All Scanned Options ============ */}
        {tradingSignal && (
          <ScanOpportunitiesWidget
            index={selectedIndex}
            apiUrl={getApiUrl()}
            token={localStorage.getItem('auth_token') || localStorage.getItem('token') || ''}
            signalOptionType={tradingSignal.type}
            signalAction={tradingSignal.action}
            onSelectOption={(option) => {
              console.log('Selected alternative option:', option)
              // TODO: Handle option selection to update the signal
            }}
          />
        )}

        {/* Multi-Timeframe Analysis Summary */}
        {(tradingSignal as any)?.mtf_bias && scanResults?.mtf_ict_analysis && (
          <Card className="border-slate-500/30">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                📈 Multi-Timeframe Analysis
                <Badge variant="outline" className={`text-xs ${(tradingSignal as any).mtf_bias === 'bullish' ? 'border-green-500 text-green-500' :
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
                  <div key={tf} className={`p-2 rounded-lg border text-center ${data.bias === 'bullish' ? 'bg-green-500/10 border-green-500/30' :
                    data.bias === 'bearish' ? 'bg-red-500/10 border-red-500/30' :
                      'bg-yellow-500/10 border-yellow-500/30'
                    }`}>
                    <div className="text-xs text-muted-foreground mb-1">{tf}</div>
                    <div className={`text-sm font-bold ${data.bias === 'bullish' ? 'text-green-400' :
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
                <div className="mt-4 text-center">
                  <Link href="/scans">
                    <Button variant="outline" size="sm" className="text-sm">
                      View All {scanResults.options.length} Results
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
              <div className="flex gap-2">
                <select className="h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20">
                  <option value="all">All Signals</option>
                  <option value="buy">BUY Only</option>
                  <option value="sell">SELL Only</option>
                  <option value="high">High Confidence</option>
                </select>
                <Link href="/screener">
                  <Button size="sm" className="text-sm">New Scan</Button>
                </Link>
                <Button variant="outline" size="sm">
                  <RefreshCw className="w-4 h-4" />
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

        {/* Recent Market News */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                <span>📰</span>
                Market News
                <Badge variant="secondary" className="text-xs">Last 6 Hours</Badge>
              </CardTitle>
              <Button variant="outline" size="sm" onClick={fetchNews} disabled={loadingNews}>
                {loadingNews ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loadingNews && news.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Loader2 className="w-8 h-8 mx-auto mb-2 animate-spin" />
                Loading news...
              </div>
            ) : news.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No recent news available
              </div>
            ) : (
              <div className="space-y-3">
                {news.slice(0, 5).map((article) => (
                  <div
                    key={article.id}
                    className="p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors cursor-pointer"
                    onClick={() => article.url && window.open(article.url, '_blank')}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="text-sm font-medium line-clamp-2">{article.title}</h4>
                        </div>
                        {article.description && (
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {article.description}
                          </p>
                        )}
                        <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
                          <span>{article.source}</span>
                          <span>•</span>
                          <span>{new Date(article.published_at).toLocaleString('en-IN', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}</span>
                          {article.affected_indices && article.affected_indices.length > 0 && (
                            <>
                              <span>•</span>
                              <span>{article.affected_indices.join(', ')}</span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        {article.sentiment && (
                          <Badge
                            variant="secondary"
                            className={`text-xs ${article.sentiment === 'positive'
                              ? 'bg-green-500/10 text-green-500 border-green-500/20'
                              : article.sentiment === 'negative'
                                ? 'bg-red-500/10 text-red-500 border-red-500/20'
                                : 'bg-gray-500/10 text-gray-500 border-gray-500/20'
                              }`}
                          >
                            {article.sentiment === 'positive' ? '📈' : article.sentiment === 'negative' ? '📉' : '➖'}
                          </Badge>
                        )}
                        {article.impact_level && (
                          <Badge
                            variant="outline"
                            className={`text-xs ${article.impact_level === 'high'
                              ? 'border-orange-500/50 text-orange-500'
                              : article.impact_level === 'medium'
                                ? 'border-yellow-500/50 text-yellow-500'
                                : 'border-gray-500/50 text-gray-500'
                              }`}
                          >
                            {article.impact_level}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {news.length > 5 && (
                  <div className="text-center pt-2">
                    <Button variant="ghost" size="sm" className="text-xs">
                      View all {news.length} articles
                    </Button>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Market News */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                <span>📰</span>
                Market News
                <Badge variant="secondary" className="text-xs">Last 6 Hours</Badge>
              </CardTitle>
              <Button variant="outline" size="sm" onClick={fetchNews} disabled={loadingNews}>
                {loadingNews ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loadingNews && news.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Loader2 className="w-8 h-8 mx-auto mb-2 animate-spin" />
                Loading news...
              </div>
            ) : news.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No recent news available
              </div>
            ) : (
              <div className="space-y-3">
                {news.slice(0, 5).map((article) => (
                  <div
                    key={article.id}
                    className="p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors cursor-pointer"
                    onClick={() => article.url && window.open(article.url, '_blank')}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 space-y-1">
                        <h4 className="text-sm font-medium line-clamp-2">{article.title}</h4>
                        {article.description && (
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {article.description}
                          </p>
                        )}
                        <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
                          <span>{article.source}</span>
                          <span>•</span>
                          <span>{new Date(article.published_at).toLocaleString('en-IN', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}</span>
                          {article.affected_indices && article.affected_indices.length > 0 && (
                            <>
                              <span>•</span>
                              <span>{article.affected_indices.join(', ')}</span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        {article.sentiment && (
                          <Badge
                            variant="secondary"
                            className={`text-xs ${article.sentiment === 'positive'
                              ? 'bg-green-500/10 text-green-500 border-green-500/20'
                              : article.sentiment === 'negative'
                                ? 'bg-red-500/10 text-red-500 border-red-500/20'
                                : 'bg-gray-500/10 text-gray-500 border-gray-500/20'
                              }`}
                          >
                            {article.sentiment === 'positive' ? '📈' : article.sentiment === 'negative' ? '📉' : '➖'}
                          </Badge>
                        )}
                        {article.impact_level && (
                          <Badge
                            variant="outline"
                            className={`text-xs ${article.impact_level === 'high'
                              ? 'border-orange-500/50 text-orange-500'
                              : article.impact_level === 'medium'
                                ? 'border-yellow-500/50 text-yellow-500'
                                : 'border-gray-500/50 text-gray-500'
                              }`}
                          >
                            {article.impact_level}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {news.length > 5 && (
                  <div className="text-center pt-2">
                    <Button variant="ghost" size="sm" className="text-xs">
                      View all {news.length} articles
                    </Button>
                  </div>
                )}
              </div>
            )}
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
      </div>

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

      {/* Scan Confirmation Dialog */}
      {scanCostData && (
        <ScanConfirmationDialog
          open={showConfirmDialog}
          onOpenChange={setShowConfirmDialog}
          scanMode={selectedScanMode}
          index={selectedIndex}
          costInTokens={scanCostData.cost_tokens}
          costInRupees={scanCostData.cost_rupees}
          currentBalance={scanCostData.current_balance}
          balanceAfter={scanCostData.balance_after}
          sufficientBalance={scanCostData.sufficient_balance}
          scanDescription={scanCostData.scan_description}
          willUseSubscription={scanCostData.will_use_subscription}
          paymentMethod={scanCostData.payment_method}
          onConfirm={() => {
            confirmedExecuteScan()
            // Refresh balance after scan
            const token = localStorage.getItem('auth_token') || localStorage.getItem('token') || localStorage.getItem('jwt_token')
            if (token) setTimeout(() => fetchTokenBalance(token), 1000)
          }}
        />
      )}
    </DashboardLayout>
  )
}
