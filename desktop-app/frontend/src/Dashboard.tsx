import React, { useEffect, useState, useMemo } from 'react';
import { BarChart3, MousePointer, Clock, Timer } from 'lucide-react';
import MetricTile from './ui/MetricTile';
import InsightBanner from './ui/InsightBanner';
import GlassCard from './ui/GlassCard';
import SectionHeader from './ui/SectionHeader';
import ChartCard from './ui/ChartCard';
import { EmptyStateBox } from './ui/InfoBox';
import { FocusVsDistractionLine, IdleBreakBar, DonutAppUsage } from './charts';
import { useThrottledValue } from './utils/smoothNumber';
import ActivityTimeline from './components/ActivityTimeline';
import { useScreenshotMode, useScreenshotData, getScreenshotSeedData } from './utils/screenshotMode';
import { 
  useAnalytics, 
  selectDashboardSeries, 
  selectCounters, 
  selectApps, 
  useAnalyticsActions,
  type Point,
  type AppSlice 
} from './state/analyticsStore';
import { focusScore, formatMinutes } from './utils/derive';
import RangeControl from './components/RangeControl';

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

interface AnalyticsData {
  analytics_data: Record<string, {
    daily_summary: any;
    app_stats: Record<string, any>;
    total_app_time: number;
    total_idle_time: number;
    focus_sessions: number;
    breaks: number;
    burnout_signals: any;
  }>;
  total_records: number;
  total_idle_records: number;
  days_analyzed: number;
}

interface MetricsSummary {
  total_app_time?: number;
  app_switches?: number;
  idle_events?: number;
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

// Helper functions to convert backend data to store format
const convertMetricsToPoints = (usage: any[]): Point[] => {
  return usage.map((item: any) => ({
    t: item[2] * 1000, // Convert to milliseconds
    focus: item[3] || 0, // Duration in seconds
    totalInputs: Math.floor(Math.random() * 100) // Placeholder - would come from backend
  }));
};

const convertUsageToAppSlices = (usage: any[]): AppSlice[] => {
  const appData: { [key: string]: number } = {};
  usage.forEach((item: any) => {
    const appName = item[0] || 'Unknown';
    appData[appName] = (appData[appName] || 0) + (item[3] || 0);
  });
  
  return Object.entries(appData).map(([name, minutes]) => ({
    name,
    minutes: Math.round(minutes / 60) // Convert to minutes
  }));
};

export default function Dashboard() {
  // Analytics store selectors
  const data = useAnalytics(selectDashboardSeries);
  const counters = useAnalytics(selectCounters);
  const apps = useAnalytics(selectApps);
  const dashRange = useAnalytics(state => state.dashRange);
  const actions = useAnalyticsActions();
  
  // Local state for UI concerns only
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState(false);
  const [insights, setInsights] = useState<InsightsData | null>(null);
  
  // Screenshot mode
  const screenshotMode = useScreenshotMode();
  const seedData = getScreenshotSeedData();

  const loadAggregatedHistory = async (range: typeof dashRange) => {
    try {
      setLoading(true);
      setError(null);

      // Try Tauri command first
      if (window.__TAURI__) {
        try {
          const result = await window.__TAURI__.invoke('get_system_metrics');
          // Update store with fetched data
          actions.setDashboardSeries(convertMetricsToPoints(result.recent_usage || []));
          actions.setApps(convertUsageToAppSlices(result.recent_usage || []));
          actions.setCounters({
            focusMinutes: Math.round((result.metrics_summary?.total_app_time || 0) / 60),
            distractMinutes: Math.round((result.metrics_summary?.total_app_time || 0) / 60 * 0.3),
            appSwitches: result.metrics_summary?.app_switches || 0,
            idleEvents: result.metrics_summary?.idle_events || 0,
            totalMinutes: Math.round((result.metrics_summary?.total_app_time || 0) / 60)
          });
          setBackendConnected(true);
          return;
        } catch (tauriError) {
          console.log('Tauri command failed, trying direct HTTP...');
        }
      }

      // Determine which endpoint to use based on range
      let endpoint = 'http://localhost:5005/api/metrics';
      let params = '';
      
      if (range.preset === 'week') {
        endpoint = 'http://localhost:5005/api/analytics';
        params = '?days=7';
      } else if (range.preset === 'month') {
        endpoint = 'http://localhost:5005/api/analytics';
        params = '?days=30';
      }
      // For 'today' or custom ranges, use the basic metrics endpoint

      const response = await fetch(endpoint + params);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      
      // Handle different response formats
      let usageData: any[] = [];
      let metricsSummary: MetricsSummary = {};
      
      if (endpoint.includes('/analytics')) {
        // Analytics endpoint returns different structure
        const analyticsResult = result as AnalyticsData;
        usageData = analyticsResult.analytics_data ? 
          Object.values(analyticsResult.analytics_data).flatMap(day => Object.values(day.app_stats || {})) : [];
        metricsSummary = {
          total_app_time: analyticsResult.total_records * 60, // Rough estimate
          app_switches: analyticsResult.total_records,
          idle_events: analyticsResult.total_idle_records || 0
        };
      } else {
        // Basic metrics endpoint
        const metricsResult = result as MetricsData;
        usageData = metricsResult.recent_usage || [];
        metricsSummary = metricsResult.metrics_summary || {};
      }
      
      // Update store with fetched data
      actions.setDashboardSeries(convertMetricsToPoints(usageData));
      actions.setApps(convertUsageToAppSlices(usageData));
      actions.setCounters({
        focusMinutes: Math.round((metricsSummary.total_app_time || 0) / 60),
        distractMinutes: Math.round((metricsSummary.total_app_time || 0) / 60 * 0.3),
        appSwitches: metricsSummary.app_switches || 0,
        idleEvents: metricsSummary.idle_events || 0,
        totalMinutes: Math.round((metricsSummary.total_app_time || 0) / 60)
      });
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

  const handleRangeChange = (range: typeof dashRange) => {
    actions.setDashRange(range);
    loadAggregatedHistory(range);
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
    // Load initial data based on current range
    loadAggregatedHistory(dashRange);
    fetchInsights();
    const interval = setInterval(() => {
      loadAggregatedHistory(dashRange);
      fetchInsights();
    }, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [dashRange.preset, dashRange.from, dashRange.to]);

  // Throttle data updates for charts to prevent excessive re-renders
  const throttledDashboardData = useThrottledValue(data || [], 250);
  const throttledApps = useThrottledValue(apps || [], 250);

  // Convert store data to ActivityTimeline format
  const timelineEvents = useMemo(() => {
    const events: any[] = [];
    
    // Add app usage events from store data
    throttledApps.forEach((app: AppSlice, index: number) => {
      events.push({
        id: `usage-${index}`,
        appName: app.name,
        action: 'Used application',
        timestamp: Date.now() - (index * 60000), // Simulate timestamps
        duration: app.minutes * 60,
        type: 'app_usage' as const
      });
    });

    // Sort by timestamp (newest first)
    return events.sort((a, b) => b.timestamp - a.timestamp);
  }, [throttledApps]);

  // Prepare chart data from store
  const prepareScreenTimeData = () => {
    if (!throttledDashboardData || throttledDashboardData.length === 0) return [];
    
    // Group usage by hour
    const hourlyData: { [key: string]: number } = {};
    throttledDashboardData.forEach((point: Point) => {
      const hour = new Date(point.t).getHours();
      const hourKey = `${hour}:00`;
      hourlyData[hourKey] = (hourlyData[hourKey] || 0) + (point.focus || 0);
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
    if (!throttledApps || throttledApps.length === 0) return [];
    
    // Convert store apps to DonutAppUsage format
    return throttledApps
      .map((app: AppSlice) => ({
        id: app.name.toLowerCase().replace(/\s+/g, '-'),
        label: app.name,
        value: app.minutes,
      }))
      .sort((a, b) => b.value - a.value);
  };

  const prepareFocusDistractionData = (): Point[] => {
    if (!throttledDashboardData || throttledDashboardData.length === 0) return [];
    
    // Convert dashboard data to Point format for charts
    return throttledDashboardData.map(point => ({
      t: point.t,
      focus: point.focus,
      distract: point.distract || 0
    }));
  };

  const prepareIdleBreakData = (): Point[] => {
    if (!throttledDashboardData || throttledDashboardData.length === 0) return [];
    
    // Convert dashboard data to Point format for charts
    return throttledDashboardData.map(point => ({
      t: point.t,
      idle: point.idle || 0,
      focus: Math.floor(Math.random() * 15) + 2 // Simulated break minutes
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
            onClick={() => loadAggregatedHistory(dashRange)}
            className="btn btn-danger mt-4"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
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

  const screenTimeData = screenshotMode.useSeedData ? seedData.screenTimeData : prepareScreenTimeData();
  const appUsageData = screenshotMode.useSeedData ? seedData.appUsageData : prepareAppUsageData();
  const focusDistractionData = screenshotMode.useSeedData ? seedData.focusDistractionData : prepareFocusDistractionData();
  const idleBreakData = screenshotMode.useSeedData ? seedData.idleBreakData : prepareIdleBreakData();

  return (
    <div className="dashboard-content max-w-7xl mx-auto mt-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-[22px] md:text-2xl font-semibold tracking-[-0.01em]">Dashboard</h1>
        <div className="flex items-center gap-4">
          <RangeControl 
            value={dashRange} 
            onChange={handleRangeChange}
          />
          <div className={`px-3 py-1.5 rounded text-dashboard-sm ${
            backendConnected ? 'bg-green-500/20 text-green-300 border border-green-500/40' : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/40'
          }`}>
            {backendConnected ? 'Connected (Tauri)' : 'Connected via HTTP'}
          </div>
        </div>
      </div>

      {/* 12-Column Grid Layout */}
      <div className="grid grid-cols-12 gap-6">
        
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
        {/* TODO: Add burnout signals to store when available */}

        {/* Row 2: KPI Metrics - Four Cards */}
        <div className="col-span-12 sm:col-span-6 xl:col-span-3">
          <MetricTile
            icon={<BarChart3 />}
            label="Focus Score"
            value={`${focusScore(counters.focusMinutes, counters.distractMinutes)}%`}
            hint="Percentage of productive time vs total active time"
            tone={getFocusScoreTone(focusScore(counters.focusMinutes, counters.distractMinutes))}
            interactive
          />
        </div>
        <div className="col-span-12 sm:col-span-6 xl:col-span-3">
          <MetricTile
            icon={<MousePointer />}
            label="App Switches"
            value={counters.appSwitches}
            hint="Number of application context switches"
            tone={getAppSwitchesTone(counters.appSwitches)}
            interactive
          />
        </div>
        <div className="col-span-12 sm:col-span-6 xl:col-span-3">
          <MetricTile
            icon={<Clock />}
            label="Idle Events"
            value={counters.idleEvents}
            hint="Times you stepped away from the computer"
            tone="default"
            interactive
          />
        </div>
        <div className="col-span-12 sm:col-span-6 xl:col-span-3">
          <MetricTile
            icon={<Timer />}
            label="Total Minutes"
            value={formatMinutes(counters.totalMinutes)}
            hint="Total active screen time today"
            tone="default"
            interactive
          />
        </div>

        {/* Row 3: Daily Screen Time (7 cols) + App Usage Distribution (5 cols) */}
        <div className="col-span-12 md:col-span-6 xl:col-span-7">
          <ChartCard
            title="Daily Screen Time"
            subtitle="Hourly breakdown of active computer usage"
            tooltip="Shows your screen time distribution throughout the day. Peak hours may indicate periods of high focus or potential overwork."
            minHeight={320}
          >
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
          </ChartCard>
        </div>
        
        <div className="col-span-12 md:col-span-6 xl:col-span-5">
          <ChartCard
            title="App Usage Distribution"
            subtitle="Top applications by time spent"
            tooltip="Visual breakdown of which applications consume most of your time. This helps identify productivity apps vs potential distractions."
            minHeight={320}
          >
            {appUsageData.length > 0 ? (
              <DonutAppUsage data={appUsageData} height={320} />
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
          </ChartCard>
        </div>

        {/* Row 4: Focus vs Distraction (7 cols) + Idle & Break Frequency (5 cols) */}
        <div className="col-span-12 md:col-span-6 xl:col-span-7">
          <ChartCard
            title="Focus vs Distraction Trend"
            subtitle="Productive vs non-productive time throughout the day"
            tooltip="Compares time spent in productive applications versus potentially distracting ones. Helps identify when you're most focused and when distractions peak."
            minHeight={360}
          >
            {focusDistractionData.length > 0 ? (
              <FocusVsDistractionLine data={focusDistractionData} height={360} />
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
          </ChartCard>
        </div>
        
        <div className="col-span-12 md:col-span-6 xl:col-span-5">
          <ChartCard
            title="Idle & Break Frequency"
            subtitle="When you step away from your computer"
            tooltip="Shows patterns of breaks and idle time. Regular breaks are healthy, but irregular patterns might indicate stress or distraction."
            minHeight={360}
          >
            {idleBreakData.length > 0 ? (
              <IdleBreakBar data={idleBreakData} height={360} />
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
          </ChartCard>
        </div>

        {/* Row 5: Recent Highlights - Full Width */}
        <div className="col-span-12">
          <ChartCard
            title="Recent Highlights"
            subtitle="Key events and insights from the selected period"
            tooltip="Summary of important events and patterns detected in your activity."
            minHeight={200}
          >
            <div className="space-y-3">
              {apps.length > 0 ? (
                <>
                  <div className="flex items-center gap-3 p-3 bg-surface-hover rounded-lg">
                    <div className="w-2 h-2 bg-brand rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm text-text">
                        <strong>{apps[0]?.name}</strong> was your most used application with {apps[0]?.minutes} minutes
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-surface-hover rounded-lg">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm text-text">
                        Focus score of <strong>{focusScore(counters.focusMinutes, counters.distractMinutes)}%</strong> 
                        {focusScore(counters.focusMinutes, counters.distractMinutes) > 70 ? ' - Great focus!' : ' - Room for improvement'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-surface-hover rounded-lg">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm text-text">
                        <strong>{counters.appSwitches}</strong> application switches detected
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-surface-hover rounded-lg">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm text-text">
                        <strong>{counters.idleEvents}</strong> break periods taken
                      </p>
                    </div>
                  </div>
                </>
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center space-y-3">
                    <div className="w-12 h-12 rounded-full bg-brand/10 flex items-center justify-center mx-auto">
                      <svg className="w-6 h-6 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="space-y-1">
                      <h4 className="font-medium text-text">Building your highlights</h4>
                      <p className="text-sm text-text-muted">
                        Select a time range to see key insights and patterns from your activity.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ChartCard>
        </div>
      </div>
    </div>
  );
}
