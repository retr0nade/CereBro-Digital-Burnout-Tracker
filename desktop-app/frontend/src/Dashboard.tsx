import React, { useEffect, useState } from 'react';
import { ResponsiveLine } from '@nivo/line';
import { ResponsivePie } from '@nivo/pie';
import { ResponsiveBar } from '@nivo/bar';
import { BarChart3, MousePointer, Clock, Timer } from 'lucide-react';
import MetricTile from './ui/MetricTile';
import InsightBanner from './ui/InsightBanner';
import GlassCard from './ui/GlassCard';

interface MetricsData {
  recent_usage: any[];
  recent_idle: any[];
  app_switches: any[];
  focus_score: number;
  burnout_signals: string[];
  metrics_summary: {
    app_switches: number;
    recent_usage: number;
    idle_events: number;
    focus_score: number;
    total_app_time: number;
    total_idle_time: number;
  };
  daily_summary?: {
    total_app_time: number;
    total_idle_time: number;
    focus_sessions: number;
    breaks: number;
  };
}

interface InsightSuggestion {
  id: string;
  type: string;
  severity: 'info' | 'warning' | 'error' | string;
  message: string;
  rule: string;
  timestamp: number;
}

interface InsightsData {
  suggestions: InsightSuggestion[];
  meta?: any;
  generated_at: number;
}

declare global {
  interface Window {
    __TAURI__: {
      invoke: (command: string, args?: any) => Promise<any>;
    };
  }
}

// Helper functions for metric tones
const getFocusScoreTone = (score: number): 'default' | 'ok' | 'warn' | 'danger' => {
  if (score >= 80) return 'ok';
  if (score >= 60) return 'warn';
  return 'danger';
};

const getAppSwitchesTone = (switches: number): 'default' | 'ok' | 'warn' | 'danger' => {
  if (switches <= 50) return 'ok';
  if (switches <= 100) return 'warn';
  return 'danger';
};

const getInsightStatus = (suggestions: InsightSuggestion[]): 'ok' | 'warn' | 'danger' => {
  const hasError = suggestions.some(s => s.severity === 'error');
  const hasWarning = suggestions.some(s => s.severity === 'warning');
  
  if (hasError) return 'danger';
  if (hasWarning) return 'warn';
  return 'ok';
};

export default function Dashboard() {
  const [data, setData] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState(false);
  const [insights, setInsights] = useState<InsightsData | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Try Tauri command first
      if (window.__TAURI__) {
        try {
          const result = await window.__TAURI__.invoke('get_system_metrics');
          setData(result);
          setBackendConnected(true);
          return;
        } catch (tauriError) {
          console.log('Tauri command failed, trying direct HTTP...');
        }
      }

      // Fallback to direct HTTP
      const response = await fetch('http://localhost:5005/api/metrics');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      setData(result);
      setBackendConnected(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch data';
      setError(errorMessage);
      setBackendConnected(false);
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchInsights = async () => {
    try {
      const response = await fetch('http://localhost:5005/api/insights');
      if (!response.ok) return;
      const result = await response.json();
      setInsights(result);
    } catch (e) {
      // Soft-fail insights fetch
      console.debug('Insights fetch failed');
    }
  };

  useEffect(() => {
    fetchData();
    fetchInsights();
    const interval = setInterval(() => {
      fetchData();
      fetchInsights();
    }, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // Prepare chart data
  const prepareScreenTimeData = () => {
    if (!data?.recent_usage) return [];
    
    // Group usage by hour
    const hourlyData: { [key: string]: number } = {};
    data.recent_usage.forEach((usage: any) => {
      const hour = new Date(usage[2] * 1000).getHours();
      const hourKey = `${hour}:00`;
      // usage shape: [app_name, start_time, end_time, duration, category]
      hourlyData[hourKey] = (hourlyData[hourKey] || 0) + (usage[3] || 0);
    });

    return [{
      id: 'Screen Time',
      data: Object.entries(hourlyData).map(([hour, duration]) => ({
        x: hour,
        y: Math.round(duration / 60) // Convert to minutes
      }))
    }];
  };

  const prepareAppUsageData = () => {
    if (!data?.recent_usage) return [];
    
    // Group by app name
    const appData: { [key: string]: number } = {};
    data.recent_usage.forEach((usage: any) => {
      const appName = usage[0] || 'Unknown';
      // usage shape: [app_name, start_time, end_time, duration, category]
      appData[appName] = (appData[appName] || 0) + (usage[3] || 0);
    });

    // Convert to pie chart format
    return Object.entries(appData)
      .map(([app, duration]) => ({
        id: app,
        label: app,
        value: Math.round(duration / 60), // Convert to minutes
        color: `hsl(${Math.random() * 360}, 70%, 50%)`
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8); // Top 8 apps
  };

  const prepareFocusDistractionData = () => {
    if (!data?.recent_usage) return [];
    
    // Simulate focus vs distraction data (in real implementation, this would come from backend)
    const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`);
    const focusData = hours.map(hour => ({
      x: hour,
      y: Math.floor(Math.random() * 60) + 20 // Simulated focus time
    }));
    
    const distractionData = hours.map(hour => ({
      x: hour,
      y: Math.floor(Math.random() * 30) + 5 // Simulated distraction time
    }));

    return [
      {
        id: 'Focus Time',
        data: focusData
      },
      {
        id: 'Distraction Time',
        data: distractionData
      }
    ];
  };

  const prepareIdleBreakData = () => {
    if (!data?.recent_idle) return [];
    
    // Group idle periods by hour
    const hourlyIdle: { [key: string]: number } = {};
    data.recent_idle.forEach((idle: any) => {
      const hour = new Date(idle[1] * 1000).getHours();
      const hourKey = `${hour}:00`;
      hourlyIdle[hourKey] = (hourlyIdle[hourKey] || 0) + 1;
    });

    // Simulate break data (in real implementation, this would come from backend)
    const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`);
    return hours.map(hour => ({
      hour,
      idle: hourlyIdle[hour] || 0,
      breaks: Math.floor(Math.random() * 3) // Simulated break count
    }));
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto mt-4 p-4">
        <div className="card">
          <div className="animate-pulse">
            <div className="h-4 bg-neutral-700 rounded w-1/4 mb-4"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="h-64 bg-neutral-800 rounded"></div>
              <div className="h-64 bg-neutral-800 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto mt-4 p-4">
        <div className="card border border-red-500/40">
          <h2 className="text-xl font-bold text-red-400 mb-2">Connection Error</h2>
          <p className="text-red-300">{error}</p>
          <p className="text-sm text-red-400 mt-2">
            {backendConnected 
              ? 'Make sure the backend server is running on port 5005'
              : 'Backend service is not available'
            }
          </p>
          <button 
            onClick={fetchData}
            className="btn btn-danger mt-4"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-7xl mx-auto mt-4 p-4">
        <div className="card">
          <p className="text-center muted">No data available</p>
        </div>
      </div>
    );
  }

  const screenTimeData = prepareScreenTimeData();
  const appUsageData = prepareAppUsageData();
  const focusDistractionData = prepareFocusDistractionData();
  const idleBreakData = prepareIdleBreakData();

  return (
    <div className="max-w-7xl mx-auto mt-4 p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className={`px-2 py-1 rounded text-xs ${
          backendConnected ? 'bg-green-500/20 text-green-300 border border-green-500/40' : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/40'
        }`}>
          {backendConnected ? 'Connected (Tauri)' : 'Connected via HTTP'}
        </div>
      </div>
      
      {/* AI Insights */}
      {insights?.suggestions && insights.suggestions.length > 0 && (
        <InsightBanner
          title="AI Insights"
          insights={insights.suggestions}
          status={getInsightStatus(insights.suggestions)}
          defaultExpanded={false}
          className="mb-8"
        />
      )}

      {/* KPI Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricTile
          icon={<BarChart3 />}
          label="Focus Score"
          value={`${data.focus_score}%`}
          hint="Percentage of productive time vs total active time"
          tone={getFocusScoreTone(data.focus_score)}
          interactive
        />
        <MetricTile
          icon={<MousePointer />}
          label="App Switches"
          value={data.metrics_summary.app_switches}
          hint="Number of application context switches"
          tone={getAppSwitchesTone(data.metrics_summary.app_switches)}
          interactive
        />
        <MetricTile
          icon={<Clock />}
          label="Idle Events"
          value={data.metrics_summary.idle_events}
          hint="Times you stepped away from the computer"
          tone="default"
          interactive
        />
        <MetricTile
          icon={<Timer />}
          label="Total Minutes"
          value={Math.round((data.metrics_summary.total_app_time || 0) / 60)}
          hint="Total active screen time today"
          tone="default"
          interactive
        />
      </div>

      {/* Burnout Signals */}
      {data.burnout_signals && data.burnout_signals.length > 0 && (
        <InsightBanner
          title="Burnout Signals Detected"
          insights={data.burnout_signals.map((signal, index) => ({
            id: `burnout-${index}`,
            type: 'burnout_signal',
            severity: 'warning',
            message: signal,
            rule: 'burnout_detection',
            timestamp: Date.now() / 1000,
          }))}
          status="warn"
          defaultExpanded={true}
          className="mb-8"
        />
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Screen Time Line Chart */}
        <GlassCard className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-text">Daily Screen Time</h3>
          <div className="h-64">
            {screenTimeData[0].data.length > 0 ? (
              <ResponsiveLine
                data={screenTimeData}
                margin={{ top: 20, right: 20, bottom: 50, left: 60 }}
                xScale={{ type: 'point' }}
                yScale={{ type: 'linear', min: 'auto', max: 'auto' }}
                axisTop={null}
                axisRight={null}
                axisLeft={{
                  tickSize: 5,
                  tickPadding: 5,
                  tickRotation: 0,
                  legend: 'Minutes',
                  legendOffset: -40,
                  legendPosition: 'middle'
                }}
                axisBottom={{
                  tickSize: 5,
                  tickPadding: 5,
                  tickRotation: 0,
                  legend: 'Hour of Day',
                  legendOffset: 36,
                  legendPosition: 'middle'
                }}
                colors={['#22c55e']}
                pointSize={6}
                pointColor={{ theme: 'background' }}
                pointBorderWidth={2}
                pointBorderColor={{ from: 'serieColor' }}
                pointLabelYOffset={-12}
                useMesh={true}
                theme={{
                  axis: {
                    ticks: {
                      text: {
                        fill: '#a3a3a3',
                        fontSize: 12
                      }
                    },
                    legend: {
                      text: {
                        fill: '#a3a3a3',
                        fontSize: 12
                      }
                    }
                  },
                  grid: {
                    line: {
                      stroke: '#27272a',
                      strokeWidth: 1
                    }
                  }
                }}
              />
            ) : (
              <div className="h-full flex items-center justify-center muted">
                <p>No screen time data available</p>
              </div>
            )}
          </div>
        </GlassCard>

        {/* App Usage Pie Chart */}
        <GlassCard className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-text">App Usage Distribution</h3>
          <div className="h-64">
            {appUsageData.length > 0 ? (
              <ResponsivePie
                data={appUsageData}
                margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
                innerRadius={0.5}
                padAngle={0.7}
                cornerRadius={3}
                activeOuterRadiusOffset={8}
                colors={{ scheme: 'nivo' }}
                borderWidth={1}
                borderColor={{ from: 'color', modifiers: [['darker', 0.2]] }}
                arcLinkLabelsSkipAngle={10}
                arcLinkLabelsTextColor="#a3a3a3"
                arcLinkLabelsThickness={2}
                arcLinkLabelsColor={{ from: 'color' }}
                arcLabelsSkipAngle={10}
                arcLabelsTextColor={{ from: 'color', modifiers: [['darker', 2]] }}
                legends={[
                  {
                    anchor: 'bottom',
                    direction: 'row',
                    justify: false,
                    translateX: 0,
                    translateY: 56,
                    itemsSpacing: 0,
                    itemWidth: 100,
                    itemHeight: 18,
                    itemTextColor: '#a3a3a3',
                    itemDirection: 'left-to-right',
                    itemOpacity: 1,
                    symbolSize: 18,
                    symbolShape: 'circle'
                  }
                ]}
              />
            ) : (
              <div className="h-full flex items-center justify-center muted">
                <p>No app usage data available</p>
              </div>
            )}
          </div>
        </GlassCard>

        {/* Focus vs Distraction Trend Line */}
        <GlassCard className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-text">Focus vs Distraction Trend</h3>
          <div className="h-64">
            {focusDistractionData[0].data.length > 0 ? (
              <ResponsiveLine
                data={focusDistractionData}
                margin={{ top: 20, right: 20, bottom: 50, left: 60 }}
                xScale={{ type: 'point' }}
                yScale={{ type: 'linear', min: 'auto', max: 'auto' }}
                axisTop={null}
                axisRight={null}
                axisLeft={{
                  tickSize: 5,
                  tickPadding: 5,
                  tickRotation: 0,
                  legend: 'Minutes',
                  legendOffset: -40,
                  legendPosition: 'middle'
                }}
                axisBottom={{
                  tickSize: 5,
                  tickPadding: 5,
                  tickRotation: 0,
                  legend: 'Hour of Day',
                  legendOffset: 36,
                  legendPosition: 'middle'
                }}
                colors={['#22c55e', '#ef4444']}
                pointSize={6}
                pointColor={{ theme: 'background' }}
                pointBorderWidth={2}
                pointBorderColor={{ from: 'serieColor' }}
                pointLabelYOffset={-12}
                useMesh={true}
                theme={{
                  axis: {
                    ticks: {
                      text: {
                        fill: '#a3a3a3',
                        fontSize: 12
                      }
                    },
                    legend: {
                      text: {
                        fill: '#a3a3a3',
                        fontSize: 12
                      }
                    }
                  },
                  grid: {
                    line: {
                      stroke: '#27272a',
                      strokeWidth: 1
                    }
                  }
                }}
                legends={[
                  {
                    anchor: 'top',
                    direction: 'row',
                    justify: false,
                    translateX: 0,
                    translateY: -30,
                    itemsSpacing: 0,
                    itemDirection: 'left-to-right',
                    itemWidth: 80,
                    itemHeight: 20,
                    itemTextColor: '#a3a3a3',
                    symbolSize: 12,
                    symbolShape: 'circle',
                    effects: [
                      {
                        on: 'hover',
                        style: {
                          itemTextColor: '#FFFFFF'
                        }
                      }
                    ]
                  }
                ]}
              />
            ) : (
              <div className="h-full flex items-center justify-center muted">
                <p>No focus/distraction data available</p>
              </div>
            )}
          </div>
        </GlassCard>

        {/* Idle/Break Frequency Bar Chart */}
        <GlassCard className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-text">Idle & Break Frequency</h3>
          <div className="h-64">
            {idleBreakData.length > 0 ? (
              <ResponsiveBar
                data={idleBreakData}
                keys={['idle', 'breaks']}
                indexBy="hour"
                margin={{ top: 20, right: 20, bottom: 50, left: 60 }}
                padding={0.3}
                groupMode="grouped"
                valueScale={{ type: 'linear' }}
                indexScale={{ type: 'band', round: true }}
                colors={{ scheme: 'nivo' }}
                borderColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
                axisTop={null}
                axisRight={null}
                axisBottom={{
                  tickSize: 5,
                  tickPadding: 5,
                  tickRotation: 0,
                  legend: 'Hour of Day',
                  legendPosition: 'middle',
                  legendOffset: 32,
                }}
                axisLeft={{
                  tickSize: 5,
                  tickPadding: 5,
                  tickRotation: 0,
                  legend: 'Count',
                  legendPosition: 'middle',
                  legendOffset: -40
                }}
                labelSkipWidth={12}
                labelSkipHeight={12}
                labelTextColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
                theme={{
                  axis: {
                    ticks: {
                      text: {
                        fill: '#a3a3a3',
                        fontSize: 12
                      }
                    },
                    legend: {
                      text: {
                        fill: '#a3a3a3',
                        fontSize: 12
                      }
                    }
                  },
                  grid: {
                    line: {
                      stroke: '#27272a',
                      strokeWidth: 1
                    }
                  }
                }}
                legends={[
                  {
                    dataFrom: 'keys',
                    anchor: 'top',
                    direction: 'row',
                    justify: false,
                    translateX: 0,
                    translateY: -30,
                    itemsSpacing: 2,
                    itemWidth: 100,
                    itemHeight: 20,
                    itemDirection: 'left-to-right',
                    itemOpacity: 0.85,
                    symbolSize: 20,
                    effects: [
                      {
                        on: 'hover',
                        style: {
                          itemOpacity: 1
                        }
                      }
                    ]
                  }
                ]}
              />
            ) : (
              <div className="h-full flex items-center justify-center muted">
                <p>No idle/break data available</p>
              </div>
            )}
          </div>
        </GlassCard>
      </div>

      {/* Recent Activity */}
      <GlassCard className="p-6">
        <h3 className="text-lg font-semibold mb-4 text-text">Recent Activity</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {data.recent_usage?.slice(0, 10).map((usage: any, index: number) => (
            <div key={index} className="flex justify-between items-center py-2 border-b border-white/10">
              <span className="text-sm">{usage[0]}</span>
              <span className="text-xs muted">
                {new Date(usage[2] * 1000).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}
