import React, { useEffect, useState, useMemo } from 'react';
import { BarChart3, MousePointer, Clock, Timer } from 'lucide-react';
import MetricTile from './ui/MetricTile';
import InsightBanner from './ui/InsightBanner';
import GlassCard from './ui/GlassCard';
import SectionHeader from './ui/SectionHeader';
import { EmptyStateBox } from './ui/InfoBox';
import { FocusVsDistractionLine, IdleBreakBar, DonutAppUsage } from './charts';
import { useThrottledValue } from './utils/smoothNumber';
import ActivityTimeline from './components/ActivityTimeline';

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

  // Throttle data updates for charts to prevent excessive re-renders
  const throttledRecentUsage = useThrottledValue(data?.recent_usage || [], 250);
  const throttledRecentIdle = useThrottledValue(data?.recent_idle || [], 250);

  // Convert usage data to ActivityTimeline format
  const timelineEvents = useMemo(() => {
    const events: any[] = [];
    
    // Add app usage events
    throttledRecentUsage.forEach((usage: any, index: number) => {
      events.push({
        id: `usage-${index}`,
        appName: usage[0] || 'Unknown App',
        action: 'Used application',
        timestamp: usage[2] * 1000, // Convert to milliseconds
        duration: usage[3],
        type: 'app_usage' as const
      });
    });

    // Add idle events
    throttledRecentIdle.forEach((idle: any, index: number) => {
      events.push({
        id: `idle-${index}`,
        appName: 'System',
        action: 'Went idle',
        timestamp: idle[1] * 1000, // Convert to milliseconds
        type: 'idle' as const
      });
    });

    // Sort by timestamp (newest first)
    return events.sort((a, b) => b.timestamp - a.timestamp);
  }, [throttledRecentUsage, throttledRecentIdle]);

  // Prepare chart data
  const prepareScreenTimeData = () => {
    if (!throttledRecentUsage || throttledRecentUsage.length === 0) return [];
    
    // Group usage by hour
    const hourlyData: { [key: string]: number } = {};
    throttledRecentUsage.forEach((usage: any) => {
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
    if (!throttledRecentUsage || throttledRecentUsage.length === 0) return [];
    
    // Group by app name
    const appData: { [key: string]: number } = {};
    throttledRecentUsage.forEach((usage: any) => {
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
    if (!throttledRecentUsage || throttledRecentUsage.length === 0) return [];
    
    // Simulate focus vs distraction data (in real implementation, this would come from backend)
    const hours = Array.from({ length: 24 }, (_, i) => i);
    return hours.map(hour => ({
      hour,
      focus: Math.floor(Math.random() * 60) + 20, // Simulated focus time in minutes
      distraction: Math.floor(Math.random() * 30) + 5 // Simulated distraction time in minutes
    }));
  };

  const prepareIdleBreakData = () => {
    if (!throttledRecentIdle || throttledRecentIdle.length === 0) return [];
    
    // Group idle periods by hour and convert to minutes
    const hourlyIdle: { [key: number]: number } = {};
    throttledRecentIdle.forEach((idle: any) => {
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
        <div className="card text-center">
          <div className="flex flex-col items-center gap-4 py-8">
            <div className="w-16 h-16 rounded-full bg-brand/10 flex items-center justify-center">
              <svg className="w-8 h-8 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-text">Welcome to your dashboard!</h3>
              <p className="text-text-muted max-w-md">
                We're setting up your personalized analytics. Make sure the backend service is running and keep the tracker active. 
                Your insights will appear here once we start collecting data.
              </p>
              <div className="flex items-center justify-center gap-4 pt-2">
                <a href="#" className="text-sm text-brand hover:text-brand-hover transition-colors">
                  Learn more about getting started →
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const screenTimeData = prepareScreenTimeData();
  const appUsageData = prepareAppUsageData();
  const focusDistractionData = prepareFocusDistractionData();
  const idleBreakData = prepareIdleBreakData();

  return (
    <div className="dashboard-content max-w-7xl mx-auto mt-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className={`px-3 py-1.5 rounded text-dashboard-sm ${
          backendConnected ? 'bg-green-500/20 text-green-300 border border-green-500/40' : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/40'
        }`}>
          {backendConnected ? 'Connected (Tauri)' : 'Connected via HTTP'}
        </div>
      </div>

      {/* 12-Column Grid Layout */}
      <div className="grid grid-cols-12 gap-3 md:gap-4 xl:gap-6">
        
        {/* Row 1: AI Insights Banner - Full Width */}
        {insights?.suggestions && insights.suggestions.length > 0 && (
          <div className="col-span-12">
            <InsightBanner
              title="AI Insights"
              insights={insights.suggestions}
              status={getInsightStatus(insights.suggestions)}
              defaultExpanded={false}
            />
          </div>
        )}

        {/* Burnout Signals Banner - Full Width */}
        {data.burnout_signals && data.burnout_signals.length > 0 && (
          <div className="col-span-12">
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
            />
          </div>
        )}

        {/* Row 2: KPI Metrics - Four Cards */}
        <div className="col-span-12 sm:col-span-6 xl:col-span-3">
          <MetricTile
            icon={<BarChart3 />}
            label="Focus Score"
            value={`${data.focus_score}%`}
            hint="Percentage of productive time vs total active time"
            tone={getFocusScoreTone(data.focus_score)}
            interactive
          />
        </div>
        <div className="col-span-12 sm:col-span-6 xl:col-span-3">
          <MetricTile
            icon={<MousePointer />}
            label="App Switches"
            value={data.metrics_summary.app_switches}
            hint="Number of application context switches"
            tone={getAppSwitchesTone(data.metrics_summary.app_switches)}
            interactive
          />
        </div>
        <div className="col-span-12 sm:col-span-6 xl:col-span-3">
          <MetricTile
            icon={<Clock />}
            label="Idle Events"
            value={data.metrics_summary.idle_events}
            hint="Times you stepped away from the computer"
            tone="default"
            interactive
          />
        </div>
        <div className="col-span-12 sm:col-span-6 xl:col-span-3">
          <MetricTile
            icon={<Timer />}
            label="Total Minutes"
            value={Math.round((data.metrics_summary.total_app_time || 0) / 60)}
            hint="Total active screen time today"
            tone="default"
            interactive
          />
        </div>

        {/* Row 3: Daily Screen Time (7 cols) + App Usage Distribution (5 cols) */}
        <div className="col-span-12 lg:col-span-7">
          <GlassCard className="h-full">
            <SectionHeader
              title="Daily Screen Time"
              subtitle="Hourly breakdown of active computer usage"
              tooltip="Shows your screen time distribution throughout the day. Peak hours may indicate periods of high focus or potential overwork."
              className="mb-4"
            />
            <div className="min-h-[280px]">
              {screenTimeData[0]?.data.length > 0 ? (
                <div className="text-dashboard-sm text-text-muted">
                  Screen time chart will be implemented with hour-by-hour data
                </div>
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center space-y-3">
                    <div className="w-12 h-12 rounded-full bg-brand/10 flex items-center justify-center mx-auto">
                      <svg className="w-6 h-6 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="space-y-1">
                      <h4 className="font-medium text-text">Building your screen time profile</h4>
                      <p className="text-sm text-text-muted">
                        Keep the backend running and tracker active to see your daily usage patterns.
                      </p>
                      <a href="#" className="text-xs text-brand hover:text-brand-hover transition-colors">
                        Learn more →
                      </a>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </GlassCard>
        </div>
        
        <div className="col-span-12 lg:col-span-5">
          <GlassCard className="h-full">
            <SectionHeader
              title="App Usage Distribution"
              subtitle="Top applications by time spent"
              tooltip="Visual breakdown of which applications consume most of your time. This helps identify productivity apps vs potential distractions."
              className="mb-4"
            />
            <div className="min-h-[280px]">
              {appUsageData.length > 0 ? (
                <DonutAppUsage data={appUsageData} height={280} />
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center space-y-3">
                    <div className="w-12 h-12 rounded-full bg-brand/10 flex items-center justify-center mx-auto">
                      <svg className="w-6 h-6 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div className="space-y-1">
                      <h4 className="font-medium text-text">Desktop tracking in progress</h4>
                      <p className="text-sm text-text-muted">
                        This chart populates automatically as you use different applications throughout the day.
                      </p>
                      <a href="#" className="text-xs text-brand hover:text-brand-hover transition-colors">
                        Learn more →
                      </a>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </GlassCard>
        </div>

        {/* Row 4: Focus vs Distraction (7 cols) + Idle & Break Frequency (5 cols) */}
        <div className="col-span-12 lg:col-span-7">
          <GlassCard className="h-full">
            <SectionHeader
              title="Focus vs Distraction Trend"
              subtitle="Productive vs non-productive time throughout the day"
              tooltip="Compares time spent in productive applications versus potentially distracting ones. Helps identify when you're most focused and when distractions peak."
              className="mb-4"
            />
            <div className="min-h-[280px]">
              {focusDistractionData.length > 0 ? (
                <FocusVsDistractionLine data={focusDistractionData} height={280} />
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center space-y-3">
                    <div className="w-12 h-12 rounded-full bg-brand/10 flex items-center justify-center mx-auto">
                      <svg className="w-6 h-6 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                    </div>
                    <div className="space-y-1">
                      <h4 className="font-medium text-text">Analyzing your focus patterns</h4>
                      <p className="text-sm text-text-muted">
                        We're learning about your productivity patterns. Use your computer normally and we'll start showing focus vs distraction trends.
                      </p>
                      <a href="#" className="text-xs text-brand hover:text-brand-hover transition-colors">
                        Learn more →
                      </a>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </GlassCard>
        </div>
        
        <div className="col-span-12 lg:col-span-5">
          <GlassCard className="h-full">
            <SectionHeader
              title="Idle & Break Frequency"
              subtitle="When you step away from your computer"
              tooltip="Shows patterns of breaks and idle time. Regular breaks are healthy, but irregular patterns might indicate stress or distraction."
              className="mb-4"
            />
            <div className="min-h-[280px]">
              {idleBreakData.length > 0 ? (
                <IdleBreakBar data={idleBreakData} height={280} />
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center space-y-3">
                    <div className="w-12 h-12 rounded-full bg-brand/10 flex items-center justify-center mx-auto">
                      <svg className="w-6 h-6 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="space-y-1">
                      <h4 className="font-medium text-text">Ready to track your breaks</h4>
                      <p className="text-sm text-text-muted">
                        Take some breaks and step away from your computer! We'll track your break patterns to help optimize your work-rest balance.
                      </p>
                      <a href="#" className="text-xs text-brand hover:text-brand-hover transition-colors">
                        Learn more →
                      </a>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </GlassCard>
        </div>

        {/* Row 5: Recent Activity - Full Width with Virtualized Timeline */}
        <div className="col-span-12">
          <GlassCard>
            <SectionHeader
              title="Recent Activity"
              subtitle="Latest application usage events"
              tooltip="Real-time feed of your recent computer activity. Useful for reviewing what you've been working on and identifying patterns."
              className="mb-4"
            />
            <ActivityTimeline 
              events={timelineEvents}
              maxHeight={400}
            />
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
