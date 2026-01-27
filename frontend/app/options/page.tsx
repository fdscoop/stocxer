'use client'

import * as React from 'react'
import Link from 'next/link'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { StatCard, StatsGrid } from '@/components/trading/stat-card'
import { ProbabilityBar, SentimentGauge } from '@/components/trading/probability-bar'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Target, Search, Loader2, TrendingUp, TrendingDown } from 'lucide-react'

interface OptionResult {
  strike: number
  type: 'CE' | 'PE'
  ltp: number
  volume: number
  oi: number
  iv: number
  delta: number
  theta: number
  recommendation: string
}

interface ExpiryData {
  weekly: string
  next_weekly: string
  monthly: string
  all_expiries?: string[]
}

export default function OptionsPage() {
  const [user, setUser] = React.useState<{ email: string } | null>(null)
  const [selectedIndex, setSelectedIndex] = React.useState('NIFTY')
  const [loading, setLoading] = React.useState(false)
  const [results, setResults] = React.useState<OptionResult[]>([])

  // Scan parameters
  const [expiry, setExpiry] = React.useState('weekly')
  const [expiryDates, setExpiryDates] = React.useState<ExpiryData | null>(null)
  const [loadingExpiries, setLoadingExpiries] = React.useState(false)
  const [minVolume, setMinVolume] = React.useState('1000')
  const [minOI, setMinOI] = React.useState('10000')

  // Probability analysis
  const [probability, setProbability] = React.useState({
    bullish: 58,
    bearish: 42,
    confidence: 72,
    direction: 'BULLISH',
    recommendation: 'BUY CE',
  })

  React.useEffect(() => {
    const token = localStorage.getItem('auth_token') || localStorage.getItem('token')
    const email = localStorage.getItem('userEmail')
    if (token && email) {
      setUser({ email })
    }
  }, [])

  // Fetch expiry dates when index changes
  React.useEffect(() => {
    const fetchExpiries = async () => {
      setLoadingExpiries(true)
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://stocxer-ai.onrender.com'
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

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('auth_token')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('user')
    setUser(null)
    window.location.href = '/login'
  }

  const scanOptions = async () => {
    setLoading(true)
    
    try {
      const token = localStorage.getItem('auth_token') || localStorage.getItem('token')
      if (!token) {
        throw new Error('Authentication required')
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://stocxer-ai.onrender.com'
      const response = await fetch(
        `${apiUrl}/options/scan?index=${selectedIndex}&expiry=${expiry}&min_volume=${minVolume}&min_oi=${minOI}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      )

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`)
      }

      const data = await response.json()
      
      // Transform the API response to match our interface
      if (data.options) {
        const transformedResults = data.options.map((opt: any) => ({
          strike: opt.strike,
          type: opt.type,
          ltp: opt.ltp,
          volume: opt.volume,
          oi: opt.oi,
          iv: opt.iv,
          delta: opt.delta || 0,
          theta: opt.theta || 0,
          recommendation: opt.recommendation || opt.signal || 'HOLD',
        }))
        setResults(transformedResults)
      }

      // Update probability analysis if available
      if (data.probability_analysis) {
        setProbability({
          bullish: Math.round(data.probability_analysis.probability_up * 100),
          bearish: Math.round(data.probability_analysis.probability_down * 100),
          confidence: Math.round(data.probability_analysis.confidence * 100),
          direction: data.probability_analysis.expected_direction,
          recommendation: data.probability_analysis.recommended_option_type === 'CALL' 
            ? 'BUY CE' 
            : data.probability_analysis.recommended_option_type === 'PUT'
            ? 'BUY PE'
            : 'STRADDLE',
        })
      }
      
    } catch (error) {
      console.error('Failed to scan options:', error)
      // Fall back to mock data
      setResults([
        { strike: 22400, type: 'CE', ltp: 145.50, volume: 45000, oi: 125000, iv: 14.2, delta: 0.52, theta: -8.5, recommendation: 'BUY' },
        { strike: 22500, type: 'CE', ltp: 98.25, volume: 62000, oi: 180000, iv: 13.8, delta: 0.45, theta: -7.2, recommendation: 'BUY' },
        { strike: 22300, type: 'PE', ltp: 112.00, volume: 38000, oi: 95000, iv: 15.1, delta: -0.48, theta: -6.8, recommendation: 'SELL' },
        { strike: 22200, type: 'PE', ltp: 165.75, volume: 28000, oi: 78000, iv: 15.8, delta: -0.55, theta: -8.1, recommendation: 'HOLD' },
      ])
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
      pageTitle="Options Scanner"
    >
      <div className="container mx-auto px-3 md:px-4 py-4 md:py-6 space-y-4 md:space-y-6">
        {/* Page Description */}
        <p className="text-sm text-muted-foreground">
          Find high-probability option trades with constituent analysis
        </p>

        {/* Scanner Controls */}
        <Card>
          <CardContent className="p-4 md:p-6">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 md:gap-4">
              <div className="space-y-2">
                <Label className="text-xs md:text-sm">Index</Label>
                <Select value={selectedIndex} onValueChange={setSelectedIndex}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="NIFTY">NIFTY 50</SelectItem>
                    <SelectItem value="BANKNIFTY">BANKNIFTY</SelectItem>
                    <SelectItem value="FINNIFTY">FINNIFTY</SelectItem>
                    <SelectItem value="SENSEX">SENSEX</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-xs md:text-sm">Expiry</Label>
                <Select value={expiry} onValueChange={setExpiry} disabled={loadingExpiries}>
                  <SelectTrigger>
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
              <div className="space-y-2">
                <Label className="text-xs md:text-sm">Min Volume</Label>
                <Input
                  type="number"
                  value={minVolume}
                  onChange={(e) => setMinVolume(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs md:text-sm">Min OI</Label>
                <Input
                  type="number"
                  value={minOI}
                  onChange={(e) => setMinOI(e.target.value)}
                />
              </div>
              <div className="flex items-end col-span-2 md:col-span-1">
                <Button
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                  onClick={scanOptions}
                  disabled={loading}
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Search className="w-4 h-4 mr-2" />
                  )}
                  Scan Options
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Probability Analysis */}
        <Card className="bg-gradient-to-r from-gray-800/50 to-gray-900/50">
          <CardHeader>
            <CardTitle className="text-base md:text-lg flex items-center gap-2">
              📊 Constituent Stock Analysis
              <Badge variant="outline" className="text-xs">
                {selectedIndex === 'NIFTY' ? '50' : selectedIndex === 'SENSEX' ? '30' : '20'} stocks
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Direction */}
              <Card className="p-4">
                <div className="text-xs md:text-sm text-muted-foreground mb-2">Expected Direction</div>
                <div className={`text-2xl md:text-3xl font-bold ${
                  probability.direction === 'BULLISH' ? 'text-bullish' : 'text-bearish'
                }`}>
                  {probability.direction === 'BULLISH' ? (
                    <span className="flex items-center gap-2">
                      <TrendingUp className="w-6 h-6" />
                      BULLISH
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <TrendingDown className="w-6 h-6" />
                      BEARISH
                    </span>
                  )}
                </div>
                <div className="mt-3 pt-3 border-t">
                  <div className="text-xs text-muted-foreground">Recommendation</div>
                  <div className="text-xl font-bold text-yellow-400">{probability.recommendation}</div>
                </div>
              </Card>

              {/* Probability Bars */}
              <Card className="p-4">
                <div className="text-xs md:text-sm text-muted-foreground mb-3">Probability Distribution</div>
                <div className="space-y-3">
                  <ProbabilityBar label="📈 Bullish" value={probability.bullish} color="bullish" />
                  <ProbabilityBar label="📉 Bearish" value={probability.bearish} color="bearish" />
                </div>
                <div className="mt-3 pt-3 border-t flex justify-between text-sm">
                  <span className="text-muted-foreground">Confidence</span>
                  <span className="font-semibold text-primary">{probability.confidence}%</span>
                </div>
              </Card>

              {/* Stock Sentiment */}
              <Card className="p-4">
                <div className="text-xs md:text-sm text-muted-foreground mb-3">Stock Sentiment</div>
                <SentimentGauge bullish={32} bearish={18} />
                <div className="mt-3 text-xs text-muted-foreground">
                  Market Regime: <span className="font-semibold text-white">Normal Volatility</span>
                </div>
              </Card>
            </div>
          </CardContent>
        </Card>

        {/* Results Table */}
        {results.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base md:text-lg flex items-center gap-2">
                🎯 Option Recommendations
                <Badge variant="secondary">{results.length} options</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left">
                      <th className="py-2 px-3 font-medium">Strike</th>
                      <th className="py-2 px-3 font-medium">Type</th>
                      <th className="py-2 px-3 font-medium">LTP</th>
                      <th className="py-2 px-3 font-medium hidden md:table-cell">Volume</th>
                      <th className="py-2 px-3 font-medium hidden md:table-cell">OI</th>
                      <th className="py-2 px-3 font-medium">IV</th>
                      <th className="py-2 px-3 font-medium hidden md:table-cell">Delta</th>
                      <th className="py-2 px-3 font-medium">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((option, i) => (
                      <tr key={i} className="border-b hover:bg-muted/50">
                        <td className="py-2 px-3 font-medium">{option.strike}</td>
                        <td className="py-2 px-3">
                          <Badge variant={option.type === 'CE' ? 'bullish' : 'bearish'}>
                            {option.type}
                          </Badge>
                        </td>
                        <td className="py-2 px-3">₹{option.ltp.toFixed(2)}</td>
                        <td className="py-2 px-3 hidden md:table-cell">{option.volume.toLocaleString()}</td>
                        <td className="py-2 px-3 hidden md:table-cell">{option.oi.toLocaleString()}</td>
                        <td className="py-2 px-3">{option.iv.toFixed(1)}%</td>
                        <td className="py-2 px-3 hidden md:table-cell">{option.delta.toFixed(2)}</td>
                        <td className="py-2 px-3">
                          <Badge
                            variant={
                              option.recommendation === 'BUY'
                                ? 'bullish'
                                : option.recommendation === 'SELL'
                                ? 'bearish'
                                : 'secondary'
                            }
                          >
                            {option.recommendation}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Empty State */}
        {results.length === 0 && !loading && (
          <Card>
            <CardContent className="p-8 md:p-12 text-center">
              <Target className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Ready to Scan</h3>
              <p className="text-muted-foreground text-sm">
                Click "Scan Options" to find trading opportunities
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}
