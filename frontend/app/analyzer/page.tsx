'use client'

import * as React from 'react'
import Link from 'next/link'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { StatCard, StatsGrid } from '@/components/trading/stat-card'
import { ProbabilityBar } from '@/components/trading/probability-bar'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area'
import {
  BarChart3,
  ArrowLeft,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Activity,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface OptionChainRow {
  strike: number
  callOI: number
  callOIChange: number
  callVolume: number
  callLTP: number
  callIV: number
  putOI: number
  putOIChange: number
  putVolume: number
  putLTP: number
  putIV: number
  isATM: boolean
}

export default function AnalyzerPage() {
  const [user, setUser] = React.useState<{ email: string } | null>(null)
  const [selectedIndex, setSelectedIndex] = React.useState('NIFTY')
  const [loading, setLoading] = React.useState(false)
  const [spotPrice, setSpotPrice] = React.useState(22456.50)
  const [change, setChange] = React.useState(189.75)
  const [changePercent, setChangePercent] = React.useState(0.85)

  // Mock option chain data
  const [optionChain, setOptionChain] = React.useState<OptionChainRow[]>([
    { strike: 22200, callOI: 125000, callOIChange: 15000, callVolume: 45000, callLTP: 285.50, callIV: 14.2, putOI: 85000, putOIChange: -8000, putVolume: 32000, putLTP: 32.25, putIV: 13.8, isATM: false },
    { strike: 22300, callOI: 180000, callOIChange: 22000, callVolume: 62000, callLTP: 195.00, callIV: 13.5, putOI: 95000, putOIChange: 5000, putVolume: 28000, putLTP: 48.50, putIV: 14.1, isATM: false },
    { strike: 22400, callOI: 220000, callOIChange: 35000, callVolume: 85000, callLTP: 125.75, callIV: 12.8, putOI: 145000, putOIChange: 18000, putVolume: 45000, putLTP: 78.25, putIV: 14.5, isATM: false },
    { strike: 22450, callOI: 185000, callOIChange: 28000, callVolume: 72000, callLTP: 95.50, callIV: 12.2, putOI: 165000, putOIChange: 22000, putVolume: 58000, putLTP: 98.75, putIV: 14.8, isATM: true },
    { strike: 22500, callOI: 250000, callOIChange: 45000, callVolume: 98000, callLTP: 68.25, callIV: 11.8, putOI: 198000, putOIChange: 32000, putVolume: 68000, putLTP: 125.50, putIV: 15.2, isATM: false },
    { strike: 22600, callOI: 195000, callOIChange: 18000, callVolume: 55000, callLTP: 38.50, callIV: 11.2, putOI: 175000, putOIChange: 28000, putVolume: 48000, putLTP: 185.25, putIV: 15.8, isATM: false },
    { strike: 22700, callOI: 145000, callOIChange: 12000, callVolume: 38000, callLTP: 22.75, callIV: 10.8, putOI: 125000, putOIChange: 15000, putVolume: 35000, putLTP: 265.00, putIV: 16.2, isATM: false },
  ])

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

  const totalCallOI = optionChain.reduce((sum, row) => sum + row.callOI, 0)
  const totalPutOI = optionChain.reduce((sum, row) => sum + row.putOI, 0)
  const pcr = (totalPutOI / totalCallOI).toFixed(2)

  const maxCallOI = Math.max(...optionChain.map((r) => r.callOI))
  const maxPutOI = Math.max(...optionChain.map((r) => r.putOI))
  const maxCallStrike = optionChain.find((r) => r.callOI === maxCallOI)?.strike
  const maxPutStrike = optionChain.find((r) => r.putOI === maxPutOI)?.strike

  return (
    <DashboardLayout
      user={user}
      selectedIndex={selectedIndex}
      onIndexChange={setSelectedIndex}
      onLogout={handleLogout}
      pageTitle="Index Analyzer"
    >
      <div className="container mx-auto px-3 md:px-4 py-4 md:py-6 space-y-4 md:space-y-6">
        {/* Page Description */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Deep analysis of {selectedIndex} option chain
          </p>
          <Button variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-1" />
            Refresh
          </Button>
        </div>

        {/* Market Summary */}
        <Card>
          <CardContent className="p-4 md:p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
              <div className="flex items-center gap-4">
                <div>
                  <div className="text-xs text-muted-foreground">{selectedIndex} Spot</div>
                  <div className="text-2xl md:text-3xl font-bold">{spotPrice.toLocaleString('en-IN')}</div>
                </div>
                <div className={cn('flex items-center gap-1', change >= 0 ? 'text-bullish' : 'text-bearish')}>
                  {change >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                  <span className="text-lg font-semibold">
                    {change >= 0 ? '+' : ''}{change.toFixed(2)} ({changePercent.toFixed(2)}%)
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  <Activity className="w-3 h-3 mr-1" />
                  Live
                </Badge>
              </div>
            </div>

            <StatsGrid columns={4}>
              <StatCard title="Total Call OI" value={(totalCallOI / 100000).toFixed(1) + ' L'} />
              <StatCard title="Total Put OI" value={(totalPutOI / 100000).toFixed(1) + ' L'} />
              <StatCard
                title="PCR"
                value={pcr}
                variant={parseFloat(pcr) > 1 ? 'bullish' : 'bearish'}
              />
              <StatCard title="ATM IV" value="12.5%" />
            </StatsGrid>
          </CardContent>
        </Card>

        {/* Key Levels */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-4">
            <div className="text-xs text-muted-foreground mb-2">Max Pain</div>
            <div className="text-2xl font-bold text-primary">22,450</div>
            <div className="text-xs text-muted-foreground mt-1">
              Distance: <span className="text-bullish">+6 pts</span>
            </div>
          </Card>
          <Card className="p-4 border-bearish/30">
            <div className="text-xs text-muted-foreground mb-2">Max Call OI (Resistance)</div>
            <div className="text-2xl font-bold text-bearish">{maxCallStrike}</div>
            <div className="text-xs text-muted-foreground mt-1">
              OI: {(maxCallOI / 100000).toFixed(1)} L
            </div>
          </Card>
          <Card className="p-4 border-bullish/30">
            <div className="text-xs text-muted-foreground mb-2">Max Put OI (Support)</div>
            <div className="text-2xl font-bold text-bullish">{maxPutStrike}</div>
            <div className="text-xs text-muted-foreground mt-1">
              OI: {(maxPutOI / 100000).toFixed(1)} L
            </div>
          </Card>
        </div>

        {/* Option Chain */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base md:text-lg">Option Chain</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="w-full whitespace-nowrap">
              <div className="min-w-[800px]">
                <table className="w-full text-xs md:text-sm">
                  <thead>
                    <tr className="border-b">
                      <th colSpan={5} className="py-2 px-2 text-center bg-bullish/10 text-bullish">CALLS</th>
                      <th className="py-2 px-2 text-center bg-muted">Strike</th>
                      <th colSpan={5} className="py-2 px-2 text-center bg-bearish/10 text-bearish">PUTS</th>
                    </tr>
                    <tr className="border-b text-muted-foreground">
                      <th className="py-2 px-2 text-right">OI</th>
                      <th className="py-2 px-2 text-right">Chg</th>
                      <th className="py-2 px-2 text-right">Vol</th>
                      <th className="py-2 px-2 text-right">LTP</th>
                      <th className="py-2 px-2 text-right">IV</th>
                      <th className="py-2 px-2 text-center font-bold"></th>
                      <th className="py-2 px-2 text-left">IV</th>
                      <th className="py-2 px-2 text-left">LTP</th>
                      <th className="py-2 px-2 text-left">Vol</th>
                      <th className="py-2 px-2 text-left">Chg</th>
                      <th className="py-2 px-2 text-left">OI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {optionChain.map((row, i) => (
                      <tr
                        key={row.strike}
                        className={cn(
                          'border-b hover:bg-muted/50 transition-colors',
                          row.isATM && 'bg-primary/10 border-l-2 border-l-primary'
                        )}
                      >
                        <td className="py-2 px-2 text-right">{(row.callOI / 1000).toFixed(0)}K</td>
                        <td className={cn('py-2 px-2 text-right', row.callOIChange >= 0 ? 'text-bullish' : 'text-bearish')}>
                          {row.callOIChange >= 0 ? '+' : ''}{(row.callOIChange / 1000).toFixed(0)}K
                        </td>
                        <td className="py-2 px-2 text-right">{(row.callVolume / 1000).toFixed(0)}K</td>
                        <td className="py-2 px-2 text-right font-medium">{row.callLTP.toFixed(2)}</td>
                        <td className="py-2 px-2 text-right text-muted-foreground">{row.callIV.toFixed(1)}%</td>
                        <td className={cn('py-2 px-2 text-center font-bold', row.isATM && 'text-primary')}>
                          {row.strike}
                          {row.isATM && <span className="ml-1 text-xs">ATM</span>}
                        </td>
                        <td className="py-2 px-2 text-left text-muted-foreground">{row.putIV.toFixed(1)}%</td>
                        <td className="py-2 px-2 text-left font-medium">{row.putLTP.toFixed(2)}</td>
                        <td className="py-2 px-2 text-left">{(row.putVolume / 1000).toFixed(0)}K</td>
                        <td className={cn('py-2 px-2 text-left', row.putOIChange >= 0 ? 'text-bullish' : 'text-bearish')}>
                          {row.putOIChange >= 0 ? '+' : ''}{(row.putOIChange / 1000).toFixed(0)}K
                        </td>
                        <td className="py-2 px-2 text-left">{(row.putOI / 1000).toFixed(0)}K</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <ScrollBar orientation="horizontal" />
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Analysis Tabs */}
        <Tabs defaultValue="oi" className="w-full">
          <TabsList className="w-full md:w-auto overflow-x-auto scrollbar-hide">
            <TabsTrigger value="oi" className="text-xs md:text-sm">OI Analysis</TabsTrigger>
            <TabsTrigger value="iv" className="text-xs md:text-sm">IV Analysis</TabsTrigger>
            <TabsTrigger value="greeks" className="text-xs md:text-sm">Greeks</TabsTrigger>
          </TabsList>
          <TabsContent value="oi" className="mt-4">
            <Card>
              <CardContent className="p-4 md:p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium mb-3">Call OI Distribution</h4>
                    <div className="space-y-2">
                      {optionChain.slice(0, 4).map((row) => (
                        <ProbabilityBar
                          key={`call-${row.strike}`}
                          label={row.strike.toString()}
                          value={(row.callOI / maxCallOI) * 100}
                          color="bearish"
                          showValue={false}
                        />
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium mb-3">Put OI Distribution</h4>
                    <div className="space-y-2">
                      {optionChain.slice(0, 4).map((row) => (
                        <ProbabilityBar
                          key={`put-${row.strike}`}
                          label={row.strike.toString()}
                          value={(row.putOI / maxPutOI) * 100}
                          color="bullish"
                          showValue={false}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="iv" className="mt-4">
            <Card>
              <CardContent className="p-4 md:p-6 text-center text-muted-foreground py-8">
                IV analysis charts will be displayed here...
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="greeks" className="mt-4">
            <Card>
              <CardContent className="p-4 md:p-6 text-center text-muted-foreground py-8">
                Greeks analysis will be displayed here...
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  )
}
