'use client'

import * as React from 'react'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Calendar as CalendarIcon, TrendingUp, TrendingDown, Target, Search, RefreshCw, Loader2 } from 'lucide-react'
import { getApiUrl } from '@/lib/api'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { format, parseISO } from 'date-fns'

interface OptionScanResult {
  id: string
  index: string
  symbol: string
  signal: string
  action: string
  confidence: number
  confidence_level: string
  strike: number
  option_type: string
  trading_symbol: string
  expiry_date: string
  days_to_expiry: number
  entry_price: number
  ltp: number
  target_1: number
  target_2: number
  stop_loss: number
  risk_reward_ratio_1: number
  risk_reward_ratio_2: number
  spot_price: number
  vix: number
  timestamp: string
}

interface ScreenerResult {
  id: string
  symbol: string
  name: string
  current_price: number
  action: string
  confidence: number
  target_1: number
  target_2: number
  stop_loss: number
  rsi: number
  sma_5: number
  sma_15: number
  momentum_5d: number
  volume: number
  volume_surge: boolean
  change_pct: number
  scanned_at: string
  reasons?: string[]
}

export default function ScansPage() {
  const [user, setUser] = React.useState<{ email: string } | null>(null)
  const [loading, setLoading] = React.useState(false)
  const [optionResults, setOptionResults] = React.useState<OptionScanResult[]>([])
  const [screenerResults, setScreenerResults] = React.useState<ScreenerResult[]>([])
  const [dateFilter, setDateFilter] = React.useState<'today' | 'yesterday' | 'week' | 'custom'>('today')
  const [actionFilter, setActionFilter] = React.useState<'all' | 'BUY' | 'SELL'>('all')
  const [selectedDate, setSelectedDate] = React.useState<Date | undefined>(undefined)
  const [availableDates, setAvailableDates] = React.useState<string[]>([])
  const [dateCounts, setDateCounts] = React.useState<{ [key: string]: number }>({})
  const [calendarOpen, setCalendarOpen] = React.useState(false)

  React.useEffect(() => {
    const token = localStorage.getItem('auth_token') || localStorage.getItem('token')
    const email = localStorage.getItem('userEmail')
    if (token && email) {
      setUser({ email })
      fetchAvailableDates()
      fetchResults()
    }
  }, [dateFilter, selectedDate])

  const fetchAvailableDates = async () => {
    try {
      const apiUrl = getApiUrl()
      const token = localStorage.getItem('auth_token') || localStorage.getItem('token')
      
      const response = await fetch(`${apiUrl}/screener/available-dates?days_back=90`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        setAvailableDates(data.all_dates || [])
        
        // Create a count map for better visualization
        const counts: { [key: string]: number } = {}
        data.all_dates?.forEach((date: string) => {
          counts[date] = (counts[date] || 0) + 1
        })
        setDateCounts(counts)
      }
    } catch (error) {
      console.error('Failed to fetch available dates:', error)
    }
  }

  const fetchResults = async () => {
    setLoading(true)
    try {
      const apiUrl = getApiUrl()
      const token = localStorage.getItem('auth_token') || localStorage.getItem('token')

      // Calculate hours or use selected date
      let params = ''
      if (dateFilter === 'custom' && selectedDate) {
        // For custom date, fetch results from that specific day
        const dateStr = format(selectedDate, 'yyyy-MM-dd')
        // Get 24 hours from selected date
        params = `hours=24&date=${dateStr}`
      } else {
        let hours = 24
        if (dateFilter === 'yesterday') hours = 48
        if (dateFilter === 'week') hours = 168
        params = `hours=${hours}`
      }

      // Fetch option scanner results
      const optionResponse = await fetch(`${apiUrl}/screener/option-scanner-results?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (optionResponse.ok) {
        const data = await optionResponse.json()
        setOptionResults(data.results || [])
      }

      // Fetch screener results
      const screenerResponse = await fetch(`${apiUrl}/screener/recent-scans?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (screenerResponse.ok) {
        const data = await screenerResponse.json()
        setScreenerResults(data.signals || [])
      }

    } catch (error) {
      console.error('Failed to fetch scan results:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDateSelect = (date: Date | undefined) => {
    setSelectedDate(date)
    setDateFilter('custom')
    setCalendarOpen(false)
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
    setUser(null)
  }

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatNumber = (value: any, decimals: number = 2): string => {
    if (value === null || value === undefined) return '--'
    const num = typeof value === 'string' ? parseFloat(value) : value
    if (isNaN(num)) return '--'
    return num.toFixed(decimals)
  }

  return (
    <DashboardLayout
      user={user}
      onLogout={handleLogout}
      showIndexSelector={false}
      pageTitle="Scan Results"
    >
      <div className="container mx-auto px-3 md:px-4 py-4 md:py-6 space-y-4 md:space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Your Scan History</h1>
            <p className="text-sm text-muted-foreground">View all your option and stock scan results</p>
          </div>
          <Button variant="outline" size="sm" onClick={fetchResults} disabled={loading}>
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          </Button>
        </div>

        {/* Date Filters */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          <Button
            variant={dateFilter === 'today' ? 'default' : 'outline'}
            size="sm"
            onClick={() => {
              setDateFilter('today')
              setSelectedDate(undefined)
            }}
          >
            <CalendarIcon className="w-4 h-4 mr-1" />
            Today
          </Button>
          <Button
            variant={dateFilter === 'yesterday' ? 'default' : 'outline'}
            size="sm"
            onClick={() => {
              setDateFilter('yesterday')
              setSelectedDate(undefined)
            }}
          >
            Yesterday
          </Button>
          <Button
            variant={dateFilter === 'week' ? 'default' : 'outline'}
            size="sm"
            onClick={() => {
              setDateFilter('week')
              setSelectedDate(undefined)
            }}
          >
            Last 7 Days
          </Button>
          
          {/* Calendar Picker - Shows last 3 months */}
          <Popover open={calendarOpen} onOpenChange={setCalendarOpen}>
            <PopoverTrigger asChild>
              <Button
                variant={dateFilter === 'custom' ? 'default' : 'outline'}
                size="sm"
                className="relative"
              >
                <CalendarIcon className="w-4 h-4 mr-1" />
                {selectedDate ? format(selectedDate, 'MMM d, yyyy') : 'Pick Date'}
                {availableDates.length > 0 && (
                  <span className="ml-1 text-xs text-green-500">({availableDates.length})</span>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0 max-w-2xl" align="start" sideOffset={5}>
              <div className="p-3 border-b bg-muted/50">
                <p className="text-sm font-medium mb-1">Select a Scan Date</p>
                <p className="text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                    <strong>{availableDates.length}</strong> days with scan results in the last 90 days
                  </span>
                </p>
              </div>
              <Calendar
                mode="single"
                selected={selectedDate}
                onSelect={handleDateSelect}
                disabled={(date) => date > new Date() || date < new Date('2024-01-01')}
                numberOfMonths={2}
                defaultMonth={selectedDate || (() => {
                  // Show most recent available date's month by default
                  if (availableDates.length > 0) {
                    return parseISO(availableDates[0])
                  }
                  return new Date()
                })()}
                modifiers={{
                  available: (date) => {
                    const dateStr = format(date, 'yyyy-MM-dd')
                    return availableDates.includes(dateStr)
                  }
                }}
                modifiersClassNames={{
                  available: 'bg-green-100 dark:bg-green-900/30 font-bold text-green-700 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-800/50 relative after:absolute after:bottom-1 after:left-1/2 after:-translate-x-1/2 after:w-2 after:h-2 after:bg-green-500 after:rounded-full after:shadow-lg'
                }}
                className="border-0"
                initialFocus
              />
              <div className="p-3 border-t bg-muted/30 max-h-32 overflow-y-auto">
                <p className="text-xs font-medium text-muted-foreground mb-2">Recent Scans:</p>
                <div className="flex flex-wrap gap-1">
                  {availableDates.slice(0, 10).map((date) => (
                    <button
                      key={date}
                      onClick={() => {
                        setSelectedDate(parseISO(date))
                        setDateFilter('custom')
                        setCalendarOpen(false)
                      }}
                      className="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded hover:bg-green-200 dark:hover:bg-green-800/50 transition-colors"
                    >
                      {format(parseISO(date), 'MMM d')}
                    </button>
                  ))}
                  {availableDates.length > 10 && (
                    <span className="px-2 py-1 text-xs text-muted-foreground">
                      +{availableDates.length - 10} more
                    </span>
                  )}
                </div>
              </div>
            </PopoverContent>
          </Popover>
        </div>

        {/* Action Filters */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          <span className="text-sm text-muted-foreground flex items-center mr-2">Filter:</span>
          <Button
            variant={actionFilter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActionFilter('all')}
          >
            All
          </Button>
          <Button
            variant={actionFilter === 'BUY' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActionFilter('BUY')}
          >
            <TrendingUp className="w-4 h-4 mr-1" />
            BUY Only
          </Button>
          <Button
            variant={actionFilter === 'SELL' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActionFilter('SELL')}
          >
            <TrendingDown className="w-4 h-4 mr-1" />
            SELL Only
          </Button>
        </div>

        {/* Results Tabs */}
        <Tabs defaultValue="options" className="w-full">
          <TabsList className="w-full md:w-auto">
            <TabsTrigger value="options" className="flex-1 md:flex-none">
              <Target className="w-4 h-4 mr-1" />
              Option Scanner ({optionResults.length})
            </TabsTrigger>
            <TabsTrigger value="screener" className="flex-1 md:flex-none">
              <Search className="w-4 h-4 mr-1" />
              Stock Screener ({screenerResults.length})
            </TabsTrigger>
          </TabsList>

          {/* Option Scanner Results */}
          <TabsContent value="options" className="mt-4">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : optionResults.length === 0 ? (
              <Card>
                <CardContent className="p-12 text-center">
                  <Target className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Option Scans Found</h3>
                  <p className="text-sm text-muted-foreground">
                    No option scanner results for the selected date range.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {optionResults.map((result) => (
                  <Card key={result.id}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="outline">{result.index}</Badge>
                            <Badge className={
                              result.action === 'BUY' ? 'bg-green-600' :
                              result.action === 'SELL' ? 'bg-red-600' : 'bg-gray-600'
                            }>
                              {result.action}
                            </Badge>
                            <Badge variant="secondary">{result.confidence}%</Badge>
                          </div>
                          <h3 className="font-semibold text-lg">{result.trading_symbol}</h3>
                          <p className="text-xs text-muted-foreground">
                            {result.strike} {result.option_type} • Expires in {result.days_to_expiry} days
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-muted-foreground">{formatDate(result.timestamp)}</div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                        <div>
                          <div className="text-xs text-muted-foreground">Entry</div>
                          <div className="font-semibold">₹{formatNumber(result.entry_price)}</div>
                        </div>
                        <div>
                          <div className="text-xs text-muted-foreground">Target 1</div>
                          <div className="font-semibold text-green-600">₹{formatNumber(result.target_1)}</div>
                        </div>
                        <div>
                          <div className="text-xs text-muted-foreground">Target 2</div>
                          <div className="font-semibold text-green-600">₹{formatNumber(result.target_2)}</div>
                        </div>
                        <div>
                          <div className="text-xs text-muted-foreground">Stop Loss</div>
                          <div className="font-semibold text-red-600">₹{formatNumber(result.stop_loss)}</div>
                        </div>
                      </div>

                      <div className="mt-3 pt-3 border-t flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">
                          Spot: ₹{formatNumber(result.spot_price)} • VIX: {formatNumber(result.vix)}
                        </span>
                        <span className="text-muted-foreground">
                          R:R {result.risk_reward_ratio_1 || '--'}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Screener Results */}
          <TabsContent value="screener" className="mt-4">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : screenerResults.length === 0 ? (
              <Card>
                <CardContent className="p-12 text-center">
                  <Search className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Stock Scans Found</h3>
                  <p className="text-sm text-muted-foreground">
                    No stock screener results for the selected date range.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {screenerResults
                  .filter(result => actionFilter === 'all' || result.action === actionFilter)
                  .map((result) => (
                  <Card key={result.id}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <Badge className={
                              result.action === 'BUY' ? 'bg-green-600' :
                              result.action === 'SELL' ? 'bg-red-600' : 'bg-gray-600'
                            }>
                              {result.action}
                            </Badge>
                            <Badge variant="secondary">{result.confidence}%</Badge>
                            {result.volume_surge && (
                              <Badge variant="outline" className="text-xs">🔥 Volume Surge</Badge>
                            )}
                          </div>
                          <h3 className="font-semibold text-lg">{result.symbol}</h3>
                          <p className="text-xs text-muted-foreground">{result.name}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-semibold">₹{formatNumber(result.current_price)}</div>
                          <div className="text-xs text-muted-foreground">{formatDate(result.scanned_at)}</div>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-3 text-sm mb-3">
                        <div>
                          <div className="text-xs text-muted-foreground">Target 1</div>
                          <div className="font-semibold text-green-600">₹{formatNumber(result.target_1)}</div>
                        </div>
                        <div>
                          <div className="text-xs text-muted-foreground">Target 2</div>
                          <div className="font-semibold text-green-600">₹{formatNumber(result.target_2)}</div>
                        </div>
                        <div>
                          <div className="text-xs text-muted-foreground">Stop Loss</div>
                          <div className="font-semibold text-red-600">₹{formatNumber(result.stop_loss)}</div>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-3 text-xs pt-2 border-t">
                        {result.rsi !== null && result.rsi !== undefined && (
                          <div>
                            <div className="text-muted-foreground">RSI</div>
                            <div className="font-semibold">{formatNumber(result.rsi, 1)}</div>
                          </div>
                        )}
                        {result.sma_5 !== null && result.sma_5 !== undefined && (
                          <div>
                            <div className="text-muted-foreground">SMA 5</div>
                            <div className="font-semibold">₹{formatNumber(result.sma_5)}</div>
                          </div>
                        )}
                        {result.sma_15 !== null && result.sma_15 !== undefined && (
                          <div>
                            <div className="text-muted-foreground">SMA 15</div>
                            <div className="font-semibold">₹{formatNumber(result.sma_15)}</div>
                          </div>
                        )}
                      </div>

                      <div className="grid grid-cols-3 gap-3 text-xs pt-2">
                        {result.momentum_5d !== null && result.momentum_5d !== undefined && (
                          <div>
                            <div className="text-muted-foreground">5D Momentum</div>
                            <div className={`font-semibold ${result.momentum_5d > 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {formatNumber(result.momentum_5d, 2)}%
                            </div>
                          </div>
                        )}
                        {result.volume !== null && result.volume !== undefined && (
                          <div>
                            <div className="text-muted-foreground">Volume</div>
                            <div className="font-semibold">{(result.volume / 1000000).toFixed(2)}M</div>
                          </div>
                        )}
                        {result.change_pct !== null && result.change_pct !== undefined && (
                          <div>
                            <div className="text-muted-foreground">Change</div>
                            <div className={`font-semibold ${result.change_pct > 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {formatNumber(result.change_pct, 2)}%
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {result.reasons && result.reasons.length > 0 && (
                        <div className="mt-3 pt-3 border-t">
                          <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">Analysis:</div>
                          <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                            {result.reasons.map((reason, idx) => (
                              <li key={idx}>{reason}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  )
}
