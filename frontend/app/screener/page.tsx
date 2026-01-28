'use client'

import * as React from 'react'
import Link from 'next/link'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { StatCard, StatsGrid } from '@/components/trading/stat-card'
import { SignalGrid, Signal } from '@/components/trading/signal-card'
import { LoadingModal } from '@/components/trading/loading-modal'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Search, RefreshCw, Loader2, X, ChevronDown, ChevronUp } from 'lucide-react'
import { getApiUrl } from '@/lib/api'

interface StockOption {
  symbol: string
  name: string
  short_name: string
}

export default function ScreenerPage() {
  const [user, setUser] = React.useState<{ email: string } | null>(null)
  const [loading, setLoading] = React.useState(false)
  const [progress, setProgress] = React.useState(0)
  const [signals, setSignals] = React.useState<Signal[]>([])
  const [scanned, setScanned] = React.useState(0)

  // Scan parameters
  const [limit, setLimit] = React.useState('50')
  const [confidence, setConfidence] = React.useState('70')
  const [action, setAction] = React.useState('BUY')
  
  // Stock selection
  const [availableStocks, setAvailableStocks] = React.useState<StockOption[]>([])
  const [searchQuery, setSearchQuery] = React.useState('')
  const [selectedStocks, setSelectedStocks] = React.useState<string[]>([])
  const [showStockPicker, setShowStockPicker] = React.useState(false)
  const [loadingStocks, setLoadingStocks] = React.useState(false)
  const [scanMode, setScanMode] = React.useState<'random' | 'custom'>('random')
  const [scanStatus, setScanStatus] = React.useState<string>('')
  const [scanError, setScanError] = React.useState<string | null>(null)

  React.useEffect(() => {
    const token = localStorage.getItem('auth_token') || localStorage.getItem('token')
    const email = localStorage.getItem('userEmail')
    if (token && email) {
      setUser({ email })
    }
  }, [])

  // Fetch available stocks for selection
  const fetchStocks = async () => {
    if (availableStocks.length > 0) return // Already loaded
    
    setLoadingStocks(true)
    try {
      const apiUrl = getApiUrl()
      const response = await fetch(`${apiUrl}/screener/stocks/list`)
      if (response.ok) {
        const data = await response.json()
        setAvailableStocks(data.stocks || [])
      }
    } catch (error) {
      console.error('Failed to fetch stocks:', error)
    } finally {
      setLoadingStocks(false)
    }
  }

  // Toggle stock selection
  const toggleStock = (symbol: string) => {
    setSelectedStocks(prev =>
      prev.includes(symbol)
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    )
  }

  // Filter stocks based on search query
  const filteredStocks = React.useMemo(() => {
    if (!searchQuery) return availableStocks.slice(0, 50) // Show top 50 when no search
    
    const query = searchQuery.toLowerCase()
    return availableStocks.filter(stock =>
      stock.short_name.toLowerCase().includes(query) ||
      stock.name.toLowerCase().includes(query) ||
      stock.symbol.toLowerCase().includes(query)
    ).slice(0, 100) // Limit to 100 results
  }, [searchQuery, availableStocks])

  // Quick select presets
  const selectNifty50 = () => {
    const nifty50Symbols = [
      'NSE:RELIANCE-EQ', 'NSE:TCS-EQ', 'NSE:HDFCBANK-EQ', 'NSE:INFY-EQ', 'NSE:ICICIBANK-EQ',
      'NSE:HINDUNILVR-EQ', 'NSE:ITC-EQ', 'NSE:SBIN-EQ', 'NSE:BHARTIARTL-EQ', 'NSE:KOTAKBANK-EQ',
      'NSE:LT-EQ', 'NSE:AXISBANK-EQ', 'NSE:ASIANPAINT-EQ', 'NSE:MARUTI-EQ', 'NSE:SUNPHARMA-EQ',
      'NSE:TITAN-EQ', 'NSE:ULTRACEMCO-EQ', 'NSE:BAJFINANCE-EQ', 'NSE:NESTLEIND-EQ', 'NSE:HCLTECH-EQ',
      'NSE:WIPRO-EQ', 'NSE:M&M-EQ', 'NSE:NTPC-EQ', 'NSE:TMPV-EQ', 'NSE:TATASTEEL-EQ',
      'NSE:POWERGRID-EQ', 'NSE:ONGC-EQ', 'NSE:ADANIPORTS-EQ', 'NSE:COALINDIA-EQ', 'NSE:BAJAJFINSV-EQ',
      'NSE:TECHM-EQ', 'NSE:INDUSINDBK-EQ', 'NSE:HINDALCO-EQ', 'NSE:DIVISLAB-EQ', 'NSE:HEROMOTOCO-EQ',
      'NSE:DRREDDY-EQ', 'NSE:CIPLA-EQ', 'NSE:EICHERMOT-EQ', 'NSE:GRASIM-EQ', 'NSE:JSWSTEEL-EQ',
      'NSE:BRITANNIA-EQ', 'NSE:APOLLOHOSP-EQ', 'NSE:BPCL-EQ', 'NSE:TATACONSUM-EQ', 'NSE:UPL-EQ',
      'NSE:ADANIENT-EQ', 'NSE:SHREECEM-EQ', 'NSE:SBILIFE-EQ', 'NSE:BAJAJ-AUTO-EQ', 'NSE:HDFCLIFE-EQ',
    ]
    setSelectedStocks(nifty50Symbols)
  }

  const selectBankNifty = () => {
    const bankSymbols = [
      'NSE:HDFCBANK-EQ', 'NSE:ICICIBANK-EQ', 'NSE:SBIN-EQ', 'NSE:KOTAKBANK-EQ', 'NSE:AXISBANK-EQ',
      'NSE:INDUSINDBK-EQ', 'NSE:PNB-EQ', 'NSE:BANKBARODA-EQ', 'NSE:CANBK-EQ', 'NSE:IDFCFIRSTB-EQ',
      'NSE:FEDERALBNK-EQ', 'NSE:BANDHANBNK-EQ', 'NSE:RBLBANK-EQ', 'NSE:AUBANK-EQ'
    ]
    setSelectedStocks(bankSymbols)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('auth_token')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('user')
    setUser(null)
    window.location.href = '/login'
  }

  const runScan = async () => {
    // First, calculate the cost
    await calculateAndConfirmCost()
  }

  const calculateAndConfirmCost = async () => {
    const apiUrl = getApiUrl()
    const token = localStorage.getItem('token') || localStorage.getItem('auth_token')
    
    if (!token) {
      setScanError('Please login to scan stocks')
      return
    }

    try {
      // Build request body for cost calculation
      const requestBody: any = {
        min_confidence: parseInt(confidence),
        action,
      }
      
      if (scanMode === 'custom' && selectedStocks.length > 0) {
        requestBody.symbols = selectedStocks.join(',')
        requestBody.limit = selectedStocks.length
      } else {
        requestBody.limit = parseInt(limit)
      }

      // Calculate cost
      const costResponse = await fetch(`${apiUrl}/api/screener/calculate-cost`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      })

      if (!costResponse.ok) {
        throw new Error('Failed to calculate scan cost')
      }

      const costData = await costResponse.json()
      console.log('[Screener] Cost calculation:', costData)

      // Show confirmation dialog
      let message = ''
      if (costData.will_use_subscription) {
        message = `You are about to scan ${costData.stock_count} stock${costData.stock_count !== 1 ? 's' : ''}.\n\n`
        message += `✅ This scan will use your ${costData.subscription_info.plan_type} subscription.\n`
        message += `📊 Scans remaining today: ${costData.subscription_info.scans_remaining} of ${costData.subscription_info.daily_limit}\n\n`
        
        // Add note about individual scanning for custom selections
        if (scanMode === 'custom' && costData.stock_count > 1) {
          message += `💡 Tip: You can also scan these stocks individually from the "Options Scanner" tab if you prefer to analyze one at a time.\n\n`
        }
        
        message += 'Click OK to proceed with bulk scan.'
      } else {
        message = `You are about to scan ${costData.stock_count} stock${costData.stock_count !== 1 ? 's' : ''}.\n\n`
        message += `💰 Total cost: ₹${costData.total_cost.toFixed(2)} (₹${costData.per_stock_cost} per stock)\n`
        message += `💳 Your wallet balance: ₹${costData.wallet_balance.toFixed(2)}\n\n`
        
        if (!costData.sufficient_balance) {
          message += '❌ Insufficient balance. Please add credits to your wallet or subscribe to a plan.'
          alert(message)
          return
        }
        
        message += '✅ Amount will be deducted from your wallet.\n\n'
        
        // Add note about individual scanning for custom selections
        if (scanMode === 'custom' && costData.stock_count > 1) {
          message += `💡 Alternative: You can scan these ${costData.stock_count} stocks individually from the "Options Scanner" tab.\n`
          message += `   • Bulk scan: ₹${costData.total_cost.toFixed(2)} now\n`
          message += `   • Individual scans: ₹${costData.per_stock_cost} per stock (pay as you go)\n\n`
        }
        
        message += 'Click OK to proceed with bulk scan.'
      }

      if (!confirm(message)) {
        return
      }

      // User confirmed, proceed with scan
      await performScan(requestBody)

    } catch (error) {
      console.error('[Screener] Cost calculation error:', error)
      setScanError('Failed to calculate scan cost. Please try again.')
    }
  }

  const performScan = async (requestBody: any) => {
    setLoading(true)
    setProgress(0)
    setSignals([])
    setScanError(null)
    
    // Set initial status message
    const stockCount = scanMode === 'custom' ? selectedStocks.length : parseInt(limit)
    setScanStatus(`Scanning ${stockCount} stock${stockCount !== 1 ? 's' : ''}...`)

    try {
      // Progress simulation with status updates
      let progressStep = 0
      const progressInterval = setInterval(() => {
        progressStep++
        const newProgress = Math.min(progressStep * 10, 90)
        setProgress(newProgress)
        
        // Update status message based on progress
        if (newProgress < 30) {
          setScanStatus(`Fetching market data for ${stockCount} stocks...`)
        } else if (newProgress < 60) {
          setScanStatus('Running technical analysis...')
        } else if (newProgress < 90) {
          setScanStatus('Generating trading signals...')
        }
      }, 500)

      const apiUrl = getApiUrl()
      const token = localStorage.getItem('token') || localStorage.getItem('auth_token')
      
      // Build request body
      const requestBody: any = {
        min_confidence: parseInt(confidence),
        action,
      }
      
      // If custom mode with selected stocks, send those
      if (scanMode === 'custom' && selectedStocks.length > 0) {
        requestBody.symbols = selectedStocks.join(',')
        requestBody.limit = selectedStocks.length
        requestBody.randomize = false  // Don't randomize custom selections
        console.log(`[Screener] Custom scan: ${selectedStocks.length} stocks`, selectedStocks)
      } else {
        // Random mode - use limit
        requestBody.limit = parseInt(limit)
        requestBody.randomize = true
        console.log(`[Screener] Random scan: ${limit} stocks`)
      }
      
      console.log('[Screener] Request body:', requestBody)
      
      const response = await fetch(`${apiUrl}/api/screener/scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify(requestBody),
      })

      clearInterval(progressInterval)
      setProgress(100)
      
      console.log('[Screener] Response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('[Screener] Response data:', data)
        
        const stocksScannedCount = data.stocks_scanned || selectedStocks.length || parseInt(limit)
        setScanned(stocksScannedCount)
        
        const mappedSignals = (data.signals || []).map((s: any) => ({
          id: s.id || Math.random().toString(),
          symbol: s.symbol,
          action: s.action,
          price: s.price || s.entry_price,
          target: s.target || s.target_price,
          stopLoss: s.stop_loss,
          confidence: s.confidence,
          timestamp: s.timestamp || new Date().toISOString(),
          reasons: s.reasons || [],
        }))
        
        setSignals(mappedSignals)
        
        // Set success status message
        if (mappedSignals.length > 0) {
          setScanStatus(`✅ Scan complete! Found ${mappedSignals.length} signal${mappedSignals.length !== 1 ? 's' : ''} from ${stocksScannedCount} stocks.`)
        } else {
          setScanStatus(`✅ Scan complete. No signals found matching your criteria from ${stocksScannedCount} stocks.`)
        }
      } else if (response.status === 401) {
        // Handle 401 - check if it's Fyers auth or session issue
        const errorData = await response.json().catch(() => ({}))
        
        if (errorData.detail && typeof errorData.detail === 'object') {
          const detail = errorData.detail
          
          if (detail.error === 'fyers_auth_required' || detail.error === 'fyers_token_expired') {
            // Fyers authentication needed - show alert and redirect
            const message = detail.error === 'fyers_token_expired' 
              ? 'Your broker authentication has expired. Please reconnect to continue scanning.'
              : 'You need to connect your broker account to use the scanner. You will be redirected to authorize.'
            
            if (confirm(message + '\n\nClick OK to authenticate now.')) {
              // Redirect to Fyers auth
              if (detail.auth_url) {
                window.location.href = detail.auth_url
              } else {
                // Fallback: go to dashboard which has auth flow
                window.location.href = '/'
              }
            }
            return
          }
        }
        
        // If not Fyers auth, it's a session issue
        alert('Your session has expired. Please login again.')
        window.location.href = '/login'
      } else if (response.status === 402) {
        // Payment Required - insufficient credits or subscription limit reached
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = errorData.detail || 'Insufficient credits or subscription limit reached'
        
        alert(`❌ Payment Required\n\n${errorMessage}\n\nPlease:\n• Subscribe to a plan, or\n• Add credits to your PAYG wallet`)
        setScanError(errorMessage)
        setScanStatus('❌ Payment required to complete scan.')
      } else {
        const errorText = await response.text().catch(() => response.statusText)
        console.error('[Screener] Scan failed:', response.status, errorText)
        setScanError(`Scan failed: ${response.statusText}`)
        setScanStatus('❌ Scan failed. Please try again.')
      }
    } catch (error: any) {
      console.error('[Screener] Scan error:', error)
      
      // Check if it's a Fyers auth error
      if (error.isFyersAuth) {
        const message = error.code === 'fyers_token_expired'
          ? 'Your broker authentication has expired. Please reconnect to continue scanning.'
          : 'You need to connect your broker account to use the scanner.'
        
        setScanError(message)
        setScanStatus('❌ Authentication required')
        
        if (confirm(message + '\n\nClick OK to authenticate now.')) {
          if (error.auth_url) {
            window.location.href = error.auth_url
          } else {
            window.location.href = '/'
          }
        }
      } else {
        setScanError(error.message || 'An error occurred while scanning')
        setScanStatus('❌ Scan error. Please try again.')
      }
    } finally {
      setLoading(false)
      setProgress(0)
    }
  }

  const buyCount = signals.filter((s) => s.action === 'BUY').length
  const sellCount = signals.filter((s) => s.action === 'SELL').length
  const avgConfidence =
    signals.length > 0
      ? (signals.reduce((sum, s) => sum + s.confidence, 0) / signals.length).toFixed(0)
      : '--'

  return (
    <DashboardLayout
      user={user}
      onLogout={handleLogout}
      showIndexSelector={false}
      pageTitle="Stock Screener"
    >
      <div className="container mx-auto px-3 md:px-4 py-4 md:py-6 space-y-4 md:space-y-6">
        {/* User Banner */}
        {user && (
          <Card className="bg-gradient-to-r from-cyan-900/30 to-blue-900/30 border-cyan-500/30">
            <CardContent className="p-3 md:p-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">👤</span>
                  <span className="text-sm text-cyan-400">Your Personal Scanner</span>
                  <span className="text-xs text-muted-foreground">{user.email}</span>
                </div>
                <div className="text-xs text-muted-foreground">
                  Results are saved to your account
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Scan Controls */}
        <Card>
          <CardContent className="p-4 md:p-6">
            {/* Scan Mode Toggle */}
            <div className="mb-6 flex gap-3 p-1 bg-muted rounded-lg">
              <Button
                variant={scanMode === 'random' ? 'default' : 'ghost'}
                size="lg"
                className={`flex-1 text-base font-semibold ${
                  scanMode === 'random' ? 'shadow-md' : 'hover:bg-accent'
                }`}
                onClick={() => setScanMode('random')}
              >
                🎲 Random Scan
              </Button>
              <Button
                variant={scanMode === 'custom' ? 'default' : 'ghost'}
                size="lg"
                className={`flex-1 text-base font-semibold ${
                  scanMode === 'custom' ? 'shadow-md' : 'hover:bg-accent'
                }`}
                onClick={() => {
                  setScanMode('custom')
                  if (availableStocks.length === 0) fetchStocks()
                }}
              >
                🎯 Select Stocks
              </Button>
            </div>

            {scanMode === 'random' ? (
              // Random mode - existing controls
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
                  <div className="space-y-2">
                    <Label className="text-xs md:text-sm">Stocks to Scan</Label>
                    <Select value={limit} onValueChange={setLimit}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="25">25 - Quick</SelectItem>
                        <SelectItem value="50">50 - Balanced</SelectItem>
                        <SelectItem value="100">100 - Deep</SelectItem>
                        <SelectItem value="200">200 - Full</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs md:text-sm">Min Confidence</Label>
                    <Select value={confidence} onValueChange={setConfidence}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="60">60%</SelectItem>
                        <SelectItem value="70">70%</SelectItem>
                        <SelectItem value="80">80%</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs md:text-sm">Action</Label>
                    <Select value={action} onValueChange={setAction}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All</SelectItem>
                        <SelectItem value="BUY">BUY Only</SelectItem>
                        <SelectItem value="SELL">SELL Only</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-end col-span-2 md:col-span-1">
                    <Button className="w-full" onClick={runScan} disabled={loading}>
                      {loading ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Search className="w-4 h-4 mr-2" />
                      )}
                      Scan Stocks
                    </Button>
                  </div>
                </div>
                <p className="mt-2 text-xs text-muted-foreground hidden md:block">
                  💡 Each scan analyzes a random selection from 500+ NSE stocks for broader coverage.
                </p>
              </>
            ) : (
              // Custom mode - stock picker
              <>
                <div className="space-y-3">
                  {/* Quick Select Buttons */}
                  <div className="flex flex-wrap gap-3 items-center p-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20 rounded-lg border-2 border-blue-200 dark:border-blue-800">
                    <Label className="text-sm font-semibold text-blue-700 dark:text-blue-300">Quick Select:</Label>
                    <Button variant="outline" size="default" className="font-semibold bg-white dark:bg-gray-900" onClick={selectNifty50}>
                      📊 NIFTY 50
                    </Button>
                    <Button variant="outline" size="default" className="font-semibold bg-white dark:bg-gray-900" onClick={selectBankNifty}>
                      🏦 Bank Nifty
                    </Button>
                    {selectedStocks.length > 0 && (
                      <Button
                        variant="destructive"
                        size="default"
                        className="font-semibold"
                        onClick={() => setSelectedStocks([])}
                      >
                        <X className="w-4 h-4 mr-2" />
                        Clear All ({selectedStocks.length})
                      </Button>
                    )}
                    <div className="ml-auto px-4 py-2 bg-blue-600 text-white rounded-md font-bold text-base shadow-md">
                      {selectedStocks.length} Selected
                    </div>
                  </div>

                  {/* Search Box */}
                  <div className="relative">
                    <Label className="text-sm font-semibold mb-2 block text-gray-700 dark:text-gray-300">🔍 Search Stocks:</Label>
                    <div className="relative">
                      <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-primary" />
                      <Input
                        placeholder="Type stock name or symbol (e.g., RELIANCE, TCS, HDFC)..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onFocus={() => {
                          setShowStockPicker(true)
                          if (availableStocks.length === 0) fetchStocks()
                        }}
                        className="pl-12 h-12 text-base border-2 border-primary/50 focus:border-primary shadow-sm"
                      />
                    </div>
                  </div>

                  {/* Selected Stocks Display */}
                  {selectedStocks.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-sm font-bold text-green-700 dark:text-green-400">✓ Selected Stocks:</Label>
                      <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto p-4 border-2 border-green-300 dark:border-green-700 rounded-lg bg-green-50 dark:bg-green-950/20">
                        {selectedStocks.map((symbol) => {
                          const stock = availableStocks.find(s => s.symbol === symbol)
                          return (
                            <Badge 
                              key={symbol} 
                              variant="secondary" 
                              className="px-4 py-2 text-base font-semibold bg-white dark:bg-gray-800 border-2 border-green-500 hover:border-green-600 transition-all shadow-sm"
                            >
                              {stock?.short_name || symbol}
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  toggleStock(symbol)
                                }}
                                className="ml-2 hover:text-destructive hover:scale-110 transition-all"
                                aria-label={`Remove ${stock?.short_name || symbol}`}
                              >
                                <X className="w-5 h-5 font-bold" />
                              </button>
                            </Badge>
                          )
                        })}
                      </div>
                    </div>
                  )}

                  {/* Stock Picker Dropdown */}
                  {showStockPicker && (
                    <div className="relative">
                      <Card className="absolute z-50 w-full max-h-96 overflow-y-auto border-2 border-primary shadow-2xl">
                        <CardContent className="p-3">
                          {loadingStocks ? (
                            <div className="text-center py-8">
                              <Loader2 className="w-6 h-6 animate-spin mx-auto text-primary" />
                              <p className="text-sm text-muted-foreground mt-2">Loading stocks...</p>
                            </div>
                          ) : filteredStocks.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground">
                              No stocks found
                            </div>
                          ) : (
                            <div className="space-y-1">
                              {filteredStocks.map((stock) => (
                                <div
                                  key={stock.symbol}
                                  className="flex items-center gap-3 p-3 hover:bg-primary/10 rounded-lg cursor-pointer border border-transparent hover:border-primary/30 transition-all"
                                  onClick={() => toggleStock(stock.symbol)}
                                >
                                  <Checkbox
                                    checked={selectedStocks.includes(stock.symbol)}
                                    onCheckedChange={() => toggleStock(stock.symbol)}
                                    className="h-5 w-5"
                                  />
                                  <div className="flex-1">
                                    <div className="font-bold text-base">{stock.short_name}</div>
                                    <div className="text-sm text-muted-foreground">{stock.name}</div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {/* Action Controls */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="space-y-2">
                      <Label className="text-xs md:text-sm">Min Confidence</Label>
                      <Select value={confidence} onValueChange={setConfidence}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="60">60%</SelectItem>
                          <SelectItem value="70">70%</SelectItem>
                          <SelectItem value="80">80%</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs md:text-sm">Action</Label>
                      <Select value={action} onValueChange={setAction}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All</SelectItem>
                          <SelectItem value="BUY">BUY Only</SelectItem>
                          <SelectItem value="SELL">SELL Only</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex items-end">
                      <Button 
                        className="w-full h-12 text-base font-bold shadow-lg" 
                        onClick={runScan} 
                        disabled={loading || selectedStocks.length === 0}
                        size="lg"
                      >
                        {loading ? (
                          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        ) : (
                          <Search className="w-5 h-5 mr-2" />
                        )}
                        🚀 Scan {selectedStocks.length} Stock{selectedStocks.length !== 1 ? 's' : ''}
                      </Button>
                    </div>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Close stock picker when clicking outside */}
        {showStockPicker && (
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowStockPicker(false)}
          />
        )}

        {/* Scan Status Feedback */}
        {(scanStatus || scanError) && !loading && (
          <Card className={`${scanError ? 'border-red-500 bg-red-50 dark:bg-red-950/20' : 'border-green-500 bg-green-50 dark:bg-green-950/20'}`}>
            <CardContent className="p-3 md:p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{scanError ? '⚠️' : '📊'}</span>
                  <span className={`font-medium ${scanError ? 'text-red-700 dark:text-red-400' : 'text-green-700 dark:text-green-400'}`}>
                    {scanStatus}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setScanStatus('')
                    setScanError(null)
                  }}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
              {scanError && (
                <p className="mt-2 text-sm text-red-600 dark:text-red-400">{scanError}</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Status Bar */}
        {signals.length > 0 && (
          <Card>
            <CardContent className="p-3 md:p-4">
              <StatsGrid columns={4}>
                <StatCard title="Scanned" value={scanned} />
                <StatCard title="Total Signals" value={signals.length} variant="default" />
                <StatCard title="BUY" value={buyCount} variant="bullish" />
                <StatCard title="SELL" value={sellCount} variant="bearish" />
              </StatsGrid>
              <div className="mt-3 text-right text-xs text-muted-foreground">
                Avg Confidence: <span className="font-semibold text-primary">{avgConfidence}%</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base md:text-lg flex items-center gap-2">
                🎯 Scan Results
                {signals.length > 0 && (
                  <Badge variant="secondary">{signals.length} signals</Badge>
                )}
              </CardTitle>
              {signals.length > 0 && (
                <Button variant="outline" size="sm" onClick={runScan}>
                  <RefreshCw className="w-4 h-4 mr-1" />
                  Rescan
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {signals.length === 0 ? (
              <div className="text-center py-8 md:py-12">
                <Search className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Ready to Scan</h3>
                <p className="text-muted-foreground text-sm mb-4">
                  Click "Scan Stocks" to find trading opportunities
                </p>
              </div>
            ) : (
              <SignalGrid signals={signals} />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Loading Modal */}
      <LoadingModal
        open={loading}
        title={scanMode === 'custom' 
          ? `Scanning ${selectedStocks.length} Selected Stock${selectedStocks.length !== 1 ? 's' : ''}...` 
          : `Scanning ${limit} Stocks...`}
        progress={progress}
        steps={[
          {
            id: '1',
            label: scanMode === 'custom' 
              ? `Fetching data for ${selectedStocks.length} stocks...`
              : 'Fetching stock data...',
            status: progress < 30 ? 'loading' : 'complete',
          },
          {
            id: '2',
            label: 'Running technical analysis...',
            status: progress < 30 ? 'pending' : progress < 70 ? 'loading' : 'complete',
          },
          {
            id: '3',
            label: 'Generating trading signals...',
            status: progress < 70 ? 'pending' : progress < 100 ? 'loading' : 'complete',
          },
        ]}
      />
    </DashboardLayout>
  )
}
