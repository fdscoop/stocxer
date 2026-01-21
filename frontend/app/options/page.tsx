'use client'

import * as React from 'react'
import Link from 'next/link'
import { Header } from '@/components/layout/header'
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
import { Target, ArrowLeft, Search, Loader2, TrendingUp, TrendingDown } from 'lucide-react'

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

export default function OptionsPage() {
  const [user, setUser] = React.useState<{ email: string } | null>(null)
  const [selectedIndex, setSelectedIndex] = React.useState('NIFTY')
  const [loading, setLoading] = React.useState(false)
  const [results, setResults] = React.useState<OptionResult[]>([])

  // Scan parameters
  const [expiry, setExpiry] = React.useState('weekly')
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
    const token = localStorage.getItem('token')
    const email = localStorage.getItem('userEmail')
    if (token && email) {
      setUser({ email })
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
    setUser(null)
  }

  const scanOptions = async () => {
    setLoading(true)
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2000))
    
    // Mock results
    setResults([
      { strike: 22400, type: 'CE', ltp: 145.50, volume: 45000, oi: 125000, iv: 14.2, delta: 0.52, theta: -8.5, recommendation: 'BUY' },
      { strike: 22500, type: 'CE', ltp: 98.25, volume: 62000, oi: 180000, iv: 13.8, delta: 0.45, theta: -7.2, recommendation: 'BUY' },
      { strike: 22300, type: 'PE', ltp: 112.00, volume: 38000, oi: 95000, iv: 15.1, delta: -0.48, theta: -6.8, recommendation: 'SELL' },
      { strike: 22200, type: 'PE', ltp: 165.75, volume: 28000, oi: 78000, iv: 15.8, delta: -0.55, theta: -8.1, recommendation: 'HOLD' },
    ])
    
    setLoading(false)
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
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2">
              <Target className="w-6 h-6 text-purple-500" />
              Options Scanner
            </h1>
            <p className="text-xs md:text-sm text-muted-foreground">
              Find high-probability option trades with constituent analysis
            </p>
          </div>
          <Link href="/">
            <Button variant="outline" size="sm">
              <ArrowLeft className="w-4 h-4 mr-1" />
              Dashboard
            </Button>
          </Link>
        </div>

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
                <Select value={expiry} onValueChange={setExpiry}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
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
      </main>
    </div>
  )
}
