import React, { useEffect, useState } from 'react';
import { BarChart3, MousePointer, Clock, Timer } from 'lucide-react';
import MetricTile from './ui/MetricTile';
import InsightBanner from './ui/InsightBanner';
import GlassCard from './ui/GlassCard';
import SectionHeader from './ui/SectionHeader';
import { EmptyStateBox } from './ui/InfoBox';
import { FocusVsDistractionLine, IdleBreakBar, DonutAppUsage } from './charts';

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

    // Convert to DonutAppUsage format
    return Object.entries(appData)
      .map(([app, duration]) => ({
        id: app.toLowerCase().replace(/\s+/g, '-'),
        label: app,
        value: Math.round(duration / 60), // Convert to minutes
      }))
      .sort((a, b) => b.value - a.value);
  };

  const prepareFocusDistractionData = () => {
    if (!data?.recent_usage) return [];
    
    // Simulate focus vs distraction data (in real implementation, this would come from backend)
    const hours = Array.from({ length: 24 }, (_, i) => i);
    return hours.map(hour => ({
      hour,
      focus: Math.floor(Math.random() * 60) + 20, // Simulated focus time in minutes
      distraction: Math.floor(Math.random() * 30) + 5 // Simulated distraction time in minutes
    }));
  };

  const prepareIdleBreakData = () => {
    if (!data?.recent_idle) return [];
    
    // Group idle periods by hour and convert to minutes
    const hourlyIdle: { [key: number]: number } = {};
    data.recent_idle.forEach((idle: any) => {
      const hour = new Date(idle[1] * 1000).getHours();
      // Convert idle count to estimated minutes (assuming each idle event = ~5 minutes)
      hourlyIdle[hour] = (hourlyIdle[hour] || 0) + 5;
    });

    // Generate data for all 24 hours
    const hours = Array.from({ length: 24 }, (_, i) => i);
    return hours.map(hour => ({
      hour,
      idle: hourlyIdle[hour] || 0,
      breaks: Math.floor(Math.random() * 15) + 2 // Simulated break minutes
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
    <div className="dashboard-content max-w-7xl mx-auto mt-4 p-4 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className={`px-3 py-1.5 rounded text-dashboard-sm ${
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
      <SectionHeader
        title="Key Performance Indicators"
        subtitle="Real-time metrics showing your productivity and focus patterns"
        tooltip="These metrics help track your mental burnout risk by monitoring focus levels, task switching behavior, and active time patterns."
      />
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
      <SectionHeader
        title="Detailed Analytics"
        subtitle="Deep dive into your usage patterns and productivity trends"
        tooltip="These charts provide detailed insights into when and how you use your computer, helping identify patterns that may contribute to burnout."
      />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Screen Time Line Chart */}
        <GlassCard className="card-spacing">
          <SectionHeader
            title="Daily Screen Time"
            subtitle="Hourly breakdown of active computer usage"
            tooltip="Shows your screen time distribution throughout the day. Peak hours may indicate periods of high focus or potential overwork."
            className="mb-4"
          />
          <div className="h-64">
            {screenTimeData[0]?.data.length > 0 ? (
              <div className="text-dashboard-sm text-text-muted">
                Screen time chart will be implemented with hour-by-hour data
              </div>
            ) : (
              <div className="h-full flex items-center justify-center">
                <EmptyStateBox
                  title="No Screen Time Data"
                  description="We haven't collected enough data yet. Keep using your computer and check back in a few minutes for insights."
                  icon="clock"
                />
              </div>
            )}
          </div>
        </GlassCard>

        {/* App Usage Pie Chart */}
        <GlassCard className="card-spacing">
          <SectionHeader
            title="App Usage Distribution"
            subtitle="Top applications by time spent"
            tooltip="Visual breakdown of which applications consume most of your time. This helps identify productivity apps vs potential distractions."
            className="mb-4"
          />
          <div className="h-64">
            {appUsageData.length > 0 ? (
              <DonutAppUsage data={appUsageData} height={320} />
            ) : (
              <div className="h-full flex items-center justify-center">
                <EmptyStateBox
                  title="No Application Data"
                  description="Start using applications on your computer to see a breakdown of where you spend your time."
                  icon="activity"
                />
              </div>
            )}
          </div>
        </GlassCard>

        {/* Focus vs Distraction Trend Line */}
        <GlassCard className="card-spacing">
          <SectionHeader
            title="Focus vs Distraction Trend"
            subtitle="Productive vs non-productive time throughout the day"
            tooltip="Compares time spent in productive applications versus potentially distracting ones. Helps identify when you're most focused and when distractions peak."
            className="mb-4"
          />
          <div className="h-64">
            {focusDistractionData.length > 0 ? (
              <FocusVsDistractionLine data={focusDistractionData} height={320} />
            ) : (
              <div className="h-full flex items-center justify-center">
                <EmptyStateBox
                  title="No Focus Data Available"
                  description="We're learning about your productivity patterns. Use your computer normally and we'll start showing focus vs distraction trends."
                  icon="trending"
                />
              </div>
            )}
          </div>
        </GlassCard>

        {/* Idle/Break Frequency Bar Chart */}
        <GlassCard className="card-spacing">
          <SectionHeader
            title="Idle & Break Frequency"
            subtitle="When you step away from your computer"
            tooltip="Shows patterns of breaks and idle time. Regular breaks are healthy, but irregular patterns might indicate stress or distraction."
            className="mb-4"
          />
          <div className="h-64">
            {idleBreakData.length > 0 ? (
              <IdleBreakBar data={idleBreakData} height={320} />
            ) : (
              <div className="h-full flex items-center justify-center">
                <EmptyStateBox
                  title="No Break Pattern Data"
                  description="Take some breaks and step away from your computer! We'll track your break patterns to help optimize your work-rest balance."
                  icon="clock"
                />
              </div>
            )}
          </div>
        </GlassCard>
      </div>

      {/* Recent Activity */}
      <SectionHeader
        title="Recent Activity"
        subtitle="Latest application usage events"
        tooltip="Real-time feed of your recent computer activity. Useful for reviewing what you've been working on and identifying patterns."
      />
      <GlassCard className="card-spacing">
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {data.recent_usage && data.recent_usage.length > 0 ? (
            data.recent_usage.slice(0, 10).map((usage: any, index: number) => (
              <div key={index} className="flex justify-between items-center py-2 border-b border-white/10">
                <span className="text-sm">{usage[0]}</span>
                <span className="text-dashboard-sm muted">
                  {new Date(usage[2] * 1000).toLocaleTimeString()}
                </span>
              </div>
            ))
          ) : (
            <div className="h-32 flex items-center justify-center">
              <EmptyStateBox
                title="No Recent Activity"
                description="Your recent application usage will appear here once you start using your computer."
                icon="database"
              />
            </div>
          )}
        </div>
      </GlassCard>
    </div>
  );
}
