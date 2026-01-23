'use client'

import * as React from 'react'
import Link from 'next/link'
import { Header } from '@/components/layout/header'
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
import { Search, ArrowLeft, RefreshCw, Loader2 } from 'lucide-react'
import { getApiUrl } from '@/lib/api'

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

  React.useEffect(() => {
    const token = localStorage.getItem('auth_token') || localStorage.getItem('token')
    const email = localStorage.getItem('userEmail')
    if (token && email) {
      setUser({ email })
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('auth_token')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('user')
    setUser(null)
    window.location.href = '/login'
  }

  const runScan = async () => {
    setLoading(true)
    setProgress(0)
    setSignals([])

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 10, 90))
      }, 500)

      const apiUrl = getApiUrl()
      const token = localStorage.getItem('token') || localStorage.getItem('auth_token')
      const response = await fetch(`${apiUrl}/api/screener/scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          limit: parseInt(limit),
          min_confidence: parseInt(confidence),
          action,
        }),
      })

      clearInterval(progressInterval)
      setProgress(100)

      if (response.ok) {
        const data = await response.json()
        setScanned(data.stocks_scanned || parseInt(limit))
        setSignals(
          (data.signals || []).map((s: any) => ({
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
        )
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
      } else {
        console.error('Scan failed:', response.statusText)
        alert('Scan failed. Please try again.')
      }
    } catch (error: any) {
      console.error('Scan error:', error)
      
      // Check if it's a Fyers auth error
      if (error.isFyersAuth) {
        const message = error.code === 'fyers_token_expired'
          ? 'Your broker authentication has expired. Please reconnect to continue scanning.'
          : 'You need to connect your broker account to use the scanner.'
        
        if (confirm(message + '\n\nClick OK to authenticate now.')) {
          if (error.auth_url) {
            window.location.href = error.auth_url
          } else {
            window.location.href = '/'
          }
        }
      } else {
        alert('An error occurred while scanning. Please try again.')
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
    <div className="min-h-screen bg-background">
      <div className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur">
        <div className="container mx-auto px-4 py-3">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2">
                <span>📊</span>
                Stock Screener
              </h1>
              <p className="text-xs md:text-sm text-muted-foreground">
                High-confidence signals for your portfolio
              </p>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {user && (
                <div className="flex items-center gap-2">
                  <span className="text-xs md:text-sm text-primary">{user.email}</span>
                  <Button variant="destructive" size="sm" onClick={handleLogout}>
                    Logout
                  </Button>
                </div>
              )}
              {!user && (
                <Link href="/login">
                  <Button size="sm">Login</Button>
                </Link>
              )}
              <Link href="/">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-1" />
                  Dashboard
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      <main className="container mx-auto px-3 md:px-4 py-4 md:py-6 space-y-4 md:space-y-6">
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
          <CardContent className="p-3 md:p-4">
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
          </CardContent>
        </Card>

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
      </main>

      {/* Loading Modal */}
      <LoadingModal
        open={loading}
        title="Scanning Stocks..."
        progress={progress}
        steps={[
          {
            id: '1',
            label: 'Fetching stock data...',
            status: progress < 30 ? 'loading' : 'complete',
          },
          {
            id: '2',
            label: 'Running technical analysis...',
            status: progress < 30 ? 'pending' : progress < 70 ? 'loading' : 'complete',
          },
          {
            id: '3',
            label: 'Generating signals...',
            status: progress < 70 ? 'pending' : progress < 100 ? 'loading' : 'complete',
          },
        ]}
      />
    </div>
  )
}
