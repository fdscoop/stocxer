/**
 * Paper Trading Dashboard
 * 
 * Automated paper trading system with:
 * - Configuration management
 * - Real-time position monitoring
 * - Performance analytics
 * - Activity logging
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  PlayCircle,
  PauseCircle,
  Settings,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  Target,
  AlertCircle,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface PaperTradingConfig {
  enabled: boolean;
  indices: string[];
  scan_interval_minutes: number;
  max_positions: number;
  capital_per_trade: number;
  min_confidence: number;
  trading_mode: string;
}

interface Position {
  id: string;
  index: string;
  option_symbol: string;
  strike: number;
  option_type: string;
  quantity: number;
  entry_price: number;
  exit_price?: number;
  entry_time: string;
  exit_time?: string;
  exit_reason?: string;
  status: string;
  pnl?: number;
  pnl_pct?: number;
  current_ltp?: number;
  current_pnl?: number;
  target_1: number;
  target_2: number;
  stop_loss: number;
}

interface Performance {
  date: string;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_win: number;
  avg_loss: number;
  profit_factor?: number;
}

interface Activity {
  id: string;
  activity_type: string;
  details: any;
  timestamp: string;
}

export default function PaperTradingDashboard() {
  const [config, setConfig] = useState<PaperTradingConfig>({
    enabled: false,
    indices: ['NIFTY'],
    scan_interval_minutes: 5,
    max_positions: 3,
    capital_per_trade: 10000,
    min_confidence: 65,
    trading_mode: 'intraday'
  });

  const [positions, setPositions] = useState<Position[]>([]);
  const [performance, setPerformance] = useState<Performance[]>([]);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [marketOpen, setMarketOpen] = useState(false);

  // Load data on mount
  useEffect(() => {
    loadStatus();
    loadConfig();
    loadPositions();
    loadPerformance();
    loadActivity();

    // Refresh positions every 30 seconds
    const interval = setInterval(() => {
      if (isRunning) {
        loadPositions();
        loadStatus();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [isRunning]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const loadStatus = async () => {
    try {
      const response = await fetch('/api/paper-trading/status', {
        headers: getAuthHeaders()
      });
      const data = await response.json();
      setIsRunning(data.is_running);
      setMarketOpen(data.market_open);
    } catch (error) {
      console.error('Error loading status:', error);
    }
  };

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/paper-trading/config', {
        headers: getAuthHeaders()
      });
      const data = await response.json();
      console.log('📋 Config loaded from backend:', data);
      if (data) {
        setConfig({
          enabled: data.enabled || false,
          indices: data.indices || ['NIFTY'],
          scan_interval_minutes: data.scan_interval_minutes || 5,
          max_positions: data.max_positions || 3,
          capital_per_trade: data.capital_per_trade || 10000,
          min_confidence: data.min_confidence || 65,
          trading_mode: data.trading_mode || 'intraday'
        });
      }
    } catch (error) {
      console.error('Error loading config:', error);
    }
  };

  const loadPositions = async () => {
    try {
      const response = await fetch('/api/paper-trading/positions?status=ALL', {
        headers: getAuthHeaders()
      });
      const data = await response.json();
      setPositions(data.positions || []);
    } catch (error) {
      console.error('Error loading positions:', error);
    }
  };

  const loadPerformance = async () => {
    try {
      const response = await fetch('/api/paper-trading/performance?days=7', {
        headers: getAuthHeaders()
      });
      const data = await response.json();
      setPerformance(data.performance || []);
    } catch (error) {
      console.error('Error loading performance:', error);
    }
  };

  const loadActivity = async () => {
    try {
      const response = await fetch('/api/paper-trading/activity?limit=50', {
        headers: getAuthHeaders()
      });
      const data = await response.json();
      setActivity(data.activity || []);
    } catch (error) {
      console.error('Error loading activity:', error);
    }
  };

  const saveConfig = async () => {
    setLoading(true);
    try {
      await fetch('/api/paper-trading/config', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(config)
      });
      alert('Configuration saved successfully!');
    } catch (error) {
      console.error('Error saving config:', error);
      alert('Failed to save configuration');
    } finally {
      setLoading(false);
    }
  };

  const toggleTrading = async () => {
    setLoading(true);
    try {
      // If starting, first enable the config
      if (!isRunning && !config.enabled) {
        console.log('🔧 Enabling paper trading config before start...');
        const enableConfig = { ...config, enabled: true };
        await fetch('/api/paper-trading/config', {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify(enableConfig)
        });
        setConfig(enableConfig);
      }

      const endpoint = isRunning
        ? '/api/paper-trading/stop'
        : '/api/paper-trading/start';

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: getAuthHeaders()
      });

      const data = await response.json();

      if (data.status === 'success') {
        setIsRunning(!isRunning);
        alert(data.message);
      } else {
        alert(`Error: ${data.message}`);
      }
    } catch (error) {
      console.error('Error toggling trading:', error);
      alert('Failed to toggle trading');
    } finally {
      setLoading(false);
    }
  };

  const closePosition = async (positionId: string) => {
    if (!confirm('Are you sure you want to close this position?')) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/paper-trading/positions/${positionId}/close`, {
        method: 'POST',
        headers: getAuthHeaders()
      });

      const data = await response.json();

      if (data.status === 'success') {
        alert(`Position closed at ₹${data.exit_price}`);
        loadPositions();
        loadPerformance();
      } else {
        alert(`Error: ${data.message}`);
      }
    } catch (error) {
      console.error('Error closing position:', error);
      alert('Failed to close position');
    } finally {
      setLoading(false);
    }
  };

  // Calculate aggregated performance
  const aggregatedPerformance = performance.reduce(
    (acc, day) => ({
      totalTrades: acc.totalTrades + day.total_trades,
      winningTrades: acc.winningTrades + day.winning_trades,
      totalPnl: acc.totalPnl + day.total_pnl
    }),
    { totalTrades: 0, winningTrades: 0, totalPnl: 0 }
  );

  const winRate = aggregatedPerformance.totalTrades > 0
    ? (aggregatedPerformance.winningTrades / aggregatedPerformance.totalTrades * 100).toFixed(1)
    : '0.0';

  const openPositions = positions.filter(p => p.status === 'OPEN');

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">📊 Automated Paper Trading</h1>
          <p className="text-gray-500 mt-1">
            Test strategies with ₹0 balance - orders will be rejected but tracked
          </p>
        </div>

        <div className="flex items-center gap-4">
          <Badge variant={marketOpen ? "default" : "secondary"}>
            {marketOpen ? "Market Open" : "Market Closed"}
          </Badge>

          <Button
            onClick={toggleTrading}
            disabled={loading}
            variant={isRunning ? "destructive" : "default"}
            size="lg"
          >
            {isRunning ? (
              <>
                <PauseCircle className="mr-2 h-5 w-5" />
                Stop Trading
              </>
            ) : (
              <>
                <PlayCircle className="mr-2 h-5 w-5" />
                Start Trading
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Performance Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Total Trades
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{aggregatedPerformance.totalTrades}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Win Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${parseFloat(winRate) >= 60 ? 'text-green-600' : 'text-red-600'}`}>
              {winRate}%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Total P&L
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${aggregatedPerformance.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ₹{aggregatedPerformance.totalPnl.toFixed(2)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Open Positions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{openPositions.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="positions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="positions">Positions</TabsTrigger>
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="activity">Activity Log</TabsTrigger>
        </TabsList>

        {/* Positions Tab */}
        <TabsContent value="positions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Trading Positions</CardTitle>
              <CardDescription>
                All paper trading positions - orders are rejected due to ₹0 balance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {positions.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">
                    No positions yet. Start trading to see positions here.
                  </p>
                ) : (
                  positions.map(position => (
                    <Card key={position.id} className="border">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start">
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">{position.index}</Badge>
                              <span className="font-semibold">
                                {position.strike} {position.option_type}
                              </span>
                              <Badge variant={position.status === 'OPEN' ? 'default' : 'secondary'}>
                                {position.status}
                              </Badge>
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                              <div>
                                <div className="text-gray-500">Entry</div>
                                <div className="font-medium">₹{position.entry_price.toFixed(2)}</div>
                              </div>

                              {position.status === 'OPEN' && position.current_ltp && (
                                <div>
                                  <div className="text-gray-500">Current</div>
                                  <div className="font-medium">₹{position.current_ltp.toFixed(2)}</div>
                                </div>
                              )}

                              {position.exit_price && (
                                <div>
                                  <div className="text-gray-500">Exit</div>
                                  <div className="font-medium">₹{position.exit_price.toFixed(2)}</div>
                                </div>
                              )}

                              <div>
                                <div className="text-gray-500">Quantity</div>
                                <div className="font-medium">{position.quantity}</div>
                              </div>

                              {position.status === 'OPEN' && position.current_pnl !== undefined && (
                                <div>
                                  <div className="text-gray-500">Current P&L</div>
                                  <div className={`font-medium ${position.current_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                    ₹{position.current_pnl.toFixed(2)}
                                  </div>
                                </div>
                              )}

                              {position.pnl !== undefined && (
                                <div>
                                  <div className="text-gray-500">Realized P&L</div>
                                  <div className={`font-medium ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                    ₹{position.pnl.toFixed(2)} ({position.pnl_pct?.toFixed(2)}%)
                                  </div>
                                </div>
                              )}
                            </div>

                            <div className="flex gap-4 text-xs text-gray-500">
                              <div className="flex items-center gap-1">
                                <Target className="h-3 w-3" />
                                T1: ₹{position.target_1.toFixed(2)}
                              </div>
                              <div className="flex items-center gap-1">
                                <Target className="h-3 w-3" />
                                T2: ₹{position.target_2.toFixed(2)}
                              </div>
                              <div className="flex items-center gap-1">
                                <AlertCircle className="h-3 w-3" />
                                SL: ₹{position.stop_loss.toFixed(2)}
                              </div>
                            </div>

                            {position.exit_reason && (
                              <Badge variant="outline" className="text-xs">
                                Exit: {position.exit_reason}
                              </Badge>
                            )}
                          </div>

                          {position.status === 'OPEN' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => closePosition(position.id)}
                              disabled={loading}
                            >
                              Close Position
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Configuration Tab */}
        <TabsContent value="config" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Trading Configuration</CardTitle>
              <CardDescription>
                Configure automated paper trading settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Indices to Trade</label>
                  <select
                    multiple
                    className="w-full border rounded p-2 bg-white text-gray-900"
                    value={config.indices}
                    onChange={(e) => {
                      const selected = Array.from(e.target.selectedOptions, option => option.value);
                      setConfig({ ...config, indices: selected });
                    }}
                  >
                    <option value="NIFTY">NIFTY</option>
                    <option value="BANKNIFTY">BANKNIFTY</option>
                    <option value="FINNIFTY">FINNIFTY</option>
                  </select>
                  <p className="text-xs text-gray-500">Hold Ctrl/Cmd to select multiple</p>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Scan Interval (minutes)</label>
                  <input
                    type="number"
                    className="w-full border rounded p-2 bg-white text-gray-900"
                    value={config.scan_interval_minutes}
                    onChange={(e) => setConfig({ ...config, scan_interval_minutes: parseInt(e.target.value) })}
                    min="1"
                    max="60"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Max Positions</label>
                  <input
                    type="number"
                    className="w-full border rounded p-2 bg-white text-gray-900"
                    value={config.max_positions}
                    onChange={(e) => setConfig({ ...config, max_positions: parseInt(e.target.value) })}
                    min="1"
                    max="10"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Capital Per Trade (₹)</label>
                  <input
                    type="number"
                    className="w-full border rounded p-2 bg-white text-gray-900"
                    value={config.capital_per_trade}
                    onChange={(e) => setConfig({ ...config, capital_per_trade: parseInt(e.target.value) })}
                    min="5000"
                    step="1000"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Min Confidence (%)</label>
                  <input
                    type="number"
                    className="w-full border rounded p-2 bg-white text-gray-900"
                    value={config.min_confidence}
                    onChange={(e) => setConfig({ ...config, min_confidence: parseInt(e.target.value) })}
                    min="50"
                    max="100"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Trading Mode</label>
                  <select
                    className="w-full border rounded p-2 bg-white text-gray-900"
                    value={config.trading_mode}
                    onChange={(e) => setConfig({ ...config, trading_mode: e.target.value })}
                  >
                    <option value="intraday">Intraday</option>
                    <option value="swing">Swing</option>
                  </select>
                </div>
              </div>

              <Button onClick={saveConfig} disabled={loading} className="w-full">
                <Settings className="mr-2 h-4 w-4" />
                Save Configuration
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Daily Performance</CardTitle>
              <CardDescription>Last 7 days of trading performance</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {performance.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">
                    No performance data yet. Start trading to see performance metrics.
                  </p>
                ) : (
                  performance.map(day => (
                    <Card key={day.date} className="border">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-center">
                          <div>
                            <div className="font-semibold">
                              {new Date(day.date).toLocaleDateString()}
                            </div>
                            <div className="text-sm text-gray-500">
                              {day.total_trades} trades • {day.win_rate.toFixed(1)}% win rate
                            </div>
                          </div>
                          <div className="text-right">
                            <div className={`text-lg font-bold ${day.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              ₹{day.total_pnl.toFixed(2)}
                            </div>
                            <div className="text-sm text-gray-500">
                              {day.winning_trades}W / {day.losing_trades}L
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Activity Tab */}
        <TabsContent value="activity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Activity Log</CardTitle>
              <CardDescription>Recent trading activity and events</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {activity.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">
                    No activity yet. Start trading to see activity logs.
                  </p>
                ) : (
                  activity.map(log => {
                    const getActivityIcon = (type: string) => {
                      switch (type) {
                        case 'POSITION_OPENED':
                          return <CheckCircle className="h-4 w-4 text-green-600" />;
                        case 'POSITION_CLOSED':
                          return <XCircle className="h-4 w-4 text-blue-600" />;
                        case 'ORDER_PLACED':
                          return <Activity className="h-4 w-4 text-yellow-600" />;
                        case 'ERROR':
                          return <AlertCircle className="h-4 w-4 text-red-600" />;
                        default:
                          return <Clock className="h-4 w-4 text-gray-600" />;
                      }
                    };

                    return (
                      <div key={log.id} className="flex items-start gap-3 p-3 border rounded">
                        {getActivityIcon(log.activity_type)}
                        <div className="flex-1">
                          <div className="font-medium">{log.activity_type.replace(/_/g, ' ')}</div>
                          <div className="text-sm text-gray-500">
                            {new Date(log.timestamp).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
