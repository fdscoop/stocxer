'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  TrendingUp, 
  TrendingDown, 
  Star, 
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Target,
  Activity,
  Zap
} from 'lucide-react'

interface ScanOpportunity {
  id: string
  scan_id: string
  index: string
  strike: number
  option_type: string
  trading_symbol: string
  ltp: number
  volume: number
  oi: number
  iv: number
  delta: number
  theta: number
  score: number
  rank: number
  entry_grade: string
  entry_recommendation: string
  target_1: number
  target_2: number
  stop_loss: number
  is_recommended: boolean
  is_in_discount: boolean
  discount_pct: number
  spot_price: number
  scanned_at: string
}

interface ScanOpportunitiesWidgetProps {
  scanId?: string
  index?: string
  apiUrl: string
  token: string
  onSelectOption?: (option: ScanOpportunity) => void
}

export function ScanOpportunitiesWidget({ 
  scanId, 
  index, 
  apiUrl, 
  token,
  onSelectOption 
}: ScanOpportunitiesWidgetProps) {
  const [opportunities, setOpportunities] = useState<ScanOpportunity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(false)
  const [activeTab, setActiveTab] = useState<'all' | 'calls' | 'puts'>('all')

  useEffect(() => {
    fetchOpportunities()
  }, [scanId, index])

  const fetchOpportunities = async () => {
    try {
      setLoading(true)
      setError(null)

      let url = `${apiUrl}/options/scan-opportunities/latest`
      if (scanId) {
        url = `${apiUrl}/options/scan-opportunities/${scanId}`
      }
      if (index) {
        url += `?index=${index}`
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch opportunities')
      }

      const data = await response.json()
      setOpportunities(data.opportunities || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const getGradeColor = (grade: string) => {
    switch (grade?.toUpperCase()) {
      case 'A': return 'bg-green-500'
      case 'B': return 'bg-blue-500'
      case 'C': return 'bg-yellow-500'
      case 'D': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500'
    if (score >= 60) return 'text-blue-500'
    if (score >= 40) return 'text-yellow-500'
    return 'text-red-500'
  }

  const filteredOpportunities = opportunities.filter(opp => {
    if (activeTab === 'calls') return opp.option_type === 'CE' || opp.option_type === 'CALL'
    if (activeTab === 'puts') return opp.option_type === 'PE' || opp.option_type === 'PUT'
    return true
  })

  const displayOpportunities = expanded ? filteredOpportunities : filteredOpportunities.slice(0, 5)

  if (loading) {
    return (
      <Card className="bg-slate-900 border-slate-700">
        <CardContent className="p-4">
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-slate-700 rounded w-1/3"></div>
            <div className="h-8 bg-slate-700 rounded"></div>
            <div className="h-8 bg-slate-700 rounded"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="bg-slate-900 border-slate-700">
        <CardContent className="p-4">
          <div className="text-red-400 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            {error}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (opportunities.length === 0) {
    return (
      <Card className="bg-slate-900 border-slate-700">
        <CardContent className="p-4">
          <div className="text-slate-400 text-center py-4">
            No scan opportunities found. Run a scan first.
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="bg-slate-900 border-slate-700">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-400" />
              Scan Opportunities
            </CardTitle>
            <CardDescription>
              Top {opportunities.length} options from latest scan
            </CardDescription>
          </div>
          <Badge variant="outline" className="text-blue-400 border-blue-400">
            {opportunities[0]?.index || index}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="pt-2">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'all' | 'calls' | 'puts')}>
          <TabsList className="grid w-full grid-cols-3 bg-slate-800">
            <TabsTrigger value="all">All ({opportunities.length})</TabsTrigger>
            <TabsTrigger value="calls" className="text-green-400">
              Calls ({opportunities.filter(o => o.option_type === 'CE' || o.option_type === 'CALL').length})
            </TabsTrigger>
            <TabsTrigger value="puts" className="text-red-400">
              Puts ({opportunities.filter(o => o.option_type === 'PE' || o.option_type === 'PUT').length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value={activeTab} className="mt-3 space-y-2">
            {displayOpportunities.map((opp, idx) => (
              <div 
                key={opp.id}
                className={`p-3 rounded-lg border transition-all cursor-pointer hover:bg-slate-800/50 ${
                  opp.is_recommended 
                    ? 'border-yellow-500/50 bg-yellow-500/5' 
                    : 'border-slate-700 bg-slate-800/30'
                }`}
                onClick={() => onSelectOption?.(opp)}
              >
                <div className="flex items-center justify-between">
                  {/* Left: Strike & Type */}
                  <div className="flex items-center gap-3">
                    <div className="text-center">
                      <div className="text-xs text-slate-400">#{opp.rank}</div>
                      <div className={`text-lg font-bold ${
                        opp.option_type === 'CE' || opp.option_type === 'CALL' 
                          ? 'text-green-400' 
                          : 'text-red-400'
                      }`}>
                        {opp.strike}
                      </div>
                      <div className="text-xs font-medium">
                        {opp.option_type}
                      </div>
                    </div>
                    
                    {/* Grade Badge */}
                    {opp.entry_grade && (
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm ${getGradeColor(opp.entry_grade)}`}>
                        {opp.entry_grade}
                      </div>
                    )}

                    {/* Recommended Star */}
                    {opp.is_recommended && (
                      <Star className="w-5 h-5 text-yellow-400 fill-yellow-400" />
                    )}
                  </div>

                  {/* Center: Metrics */}
                  <div className="flex gap-4 text-sm">
                    <div className="text-center">
                      <div className="text-slate-400 text-xs">LTP</div>
                      <div className="font-medium">₹{opp.ltp?.toFixed(2)}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-slate-400 text-xs">IV</div>
                      <div className="font-medium">{opp.iv?.toFixed(1)}%</div>
                    </div>
                    <div className="text-center">
                      <div className="text-slate-400 text-xs">Delta</div>
                      <div className="font-medium">{opp.delta?.toFixed(2)}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-slate-400 text-xs">OI</div>
                      <div className="font-medium">{(opp.oi / 1000).toFixed(0)}K</div>
                    </div>
                  </div>

                  {/* Right: Score & Targets */}
                  <div className="text-right">
                    <div className={`text-2xl font-bold ${getScoreColor(opp.score)}`}>
                      {opp.score?.toFixed(0)}
                    </div>
                    <div className="text-xs text-slate-400">Score</div>
                    
                    {/* Discount Badge */}
                    {opp.is_in_discount && (
                      <Badge className="mt-1 bg-green-500/20 text-green-400 text-xs">
                        <Zap className="w-3 h-3 mr-1" />
                        {opp.discount_pct?.toFixed(0)}% discount
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Targets Row */}
                {(opp.target_1 || opp.stop_loss) && (
                  <div className="mt-2 pt-2 border-t border-slate-700 flex items-center gap-4 text-xs">
                    <Target className="w-3 h-3 text-slate-400" />
                    {opp.stop_loss && (
                      <span className="text-red-400">SL: ₹{opp.stop_loss.toFixed(0)}</span>
                    )}
                    {opp.target_1 && (
                      <span className="text-green-400">T1: ₹{opp.target_1.toFixed(0)}</span>
                    )}
                    {opp.target_2 && (
                      <span className="text-blue-400">T2: ₹{opp.target_2.toFixed(0)}</span>
                    )}
                    {opp.entry_recommendation && (
                      <span className="text-slate-300 ml-auto">{opp.entry_recommendation}</span>
                    )}
                  </div>
                )}
              </div>
            ))}

            {/* Expand/Collapse Button */}
            {filteredOpportunities.length > 5 && (
              <Button
                variant="ghost"
                className="w-full text-slate-400 hover:text-white"
                onClick={() => setExpanded(!expanded)}
              >
                {expanded ? (
                  <>
                    <ChevronUp className="w-4 h-4 mr-2" />
                    Show Less
                  </>
                ) : (
                  <>
                    <ChevronDown className="w-4 h-4 mr-2" />
                    Show {filteredOpportunities.length - 5} More
                  </>
                )}
              </Button>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

export default ScanOpportunitiesWidget
