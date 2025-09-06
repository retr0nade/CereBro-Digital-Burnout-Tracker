import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { ResponsiveLine } from '@nivo/line';
import { ResponsivePie } from '@nivo/pie';
import { motion } from 'framer-motion';
import webSocketService, { WebSocketEvent, WebSocketStatus } from './WebSocketService';
import { useSmoothedNumber, useThrottledValue } from './utils/smoothNumber';
import ActivityTimeline from './components/ActivityTimeline';
import SectionHeader from './ui/SectionHeader';
import { EmptyStateBox } from './ui/InfoBox';
import MetricTile from './ui/MetricTile';
import GlassCard from './ui/GlassCard';
import ChartCard from './ui/ChartCard';
import { BarChart3, MousePointer, Clock, Timer, Activity } from 'lucide-react';
import { createRollingWindow, useRAFBatching, useRenderTracker } from './utils/performance';
import { useScreenshotMode, getScreenshotSeedData } from './utils/screenshotMode';
import { 
  useAnalytics, 
  selectRealtime, 
  selectCounters, 
  selectActions,
  type Point 
} from './state/analyticsStore';
import { focusScore, formatMinutes } from './utils/derive';
import WindowSelect from './components/WindowSelect';

interface RealTimeMetrics {
  appUsage: Array<{
    app_name: string;
    duration: number;
    timestamp: number;
  }>;
  idleStatus: {
    is_idle: boolean;
    duration?: number;
    timestamp: number;
  } | null;
  inputActivity: Array<{
    timestamp: number;
    total_inputs: number;
    keypress_count: number;
    mouse_click_count: number;
  }>;
  focusSessions: Array<{
    session_id: string;
    duration: number;
    was_interrupted: boolean;
    timestamp: number;
  }>;
  breaks: Array<{
    duration: number;
    break_type: string;
    timestamp: number;
  }>;
}

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
  };
}

// Helper function to get connection status tone
const getConnectionStatusTone = (backendConnected: boolean, wsStatus: WebSocketStatus): 'default' | 'ok' | 'warn' | 'danger' => {
  if (backendConnected && wsStatus.connected) return 'ok';
  if (backendConnected || wsStatus.connecting) return 'warn';
  return 'danger';
};

// Helper function to get connection status text
const getConnectionStatusText = (backendConnected: boolean, wsStatus: WebSocketStatus): string => {
  if (backendConnected && wsStatus.connected) return 'All Connected';
  if (backendConnected && wsStatus.connecting) return 'Connecting...';
  if (backendConnected && !wsStatus.connected) return 'Backend Only';
  return 'Disconnected';
};

export default function RealTimeDashboard() {
  // Analytics store selectors - ONLY using realtime data
  const rt = useAnalytics(selectRealtime);
  const counters = useAnalytics(selectCounters);
  const actions = useAnalytics(selectActions);
  
  // Get current window setting from store
  const rtWindowMinutes = useAnalytics(state => state.rtWindowMinutes);
  
  // Local state for UI concerns only
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState(false);
  const [wsStatus, setWsStatus] = useState<WebSocketStatus>({ connected: false, connecting: false });

  // Performance optimizations
  const rafBatcher = useRAFBatching();
  const renderCount = useRenderTracker('RealTimeDashboard');
  
  // Screenshot mode
  const screenshotMode = useScreenshotMode();
  const seedData = getScreenshotSeedData();
  
  // Create rolling window functions for different data types
  const rollingWindow72 = createRollingWindow(72); // 72 points for 6 hours at 5-min intervals
  const rollingWindow48 = createRollingWindow(48); // 48 points for 4 hours at 5-min intervals

  // Apply smoothing to rapid-changing metrics to reduce jitter
  const smoothedFocusScore = useSmoothedNumber(focusScore(counters.focusMinutes, counters.distractMinutes), 120, 18);
  const smoothedAppSwitches = useSmoothedNumber(counters.appSwitches, 120, 18);
  const smoothedIdleEvents = useSmoothedNumber(counters.idleEvents, 120, 18);

  // Throttle chart data updates and apply rolling window caps
  const throttledRealtimeData = useThrottledValue(rollingWindow72(rt), 250);

  // Convert real-time data to ActivityTimeline format
  const timelineEvents = useMemo(() => {
    if (screenshotMode.useSeedData) {
      return seedData.activityTimelineEvents;
    }
    
    const events: any[] = [];
    
    // Add real-time data points as events
    throttledRealtimeData.forEach((point: Point, index) => {
      events.push({
        id: `rt-point-${index}`,
        appName: 'System',
        action: `Activity (${point.totalInputs || 0} inputs)`,
        timestamp: point.t,
        type: 'input' as const
      });
    });

    // Sort by timestamp (newest first) and limit to last 50 events
    return events
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, 50);
  }, [throttledRealtimeData, screenshotMode.useSeedData, seedData.activityTimelineEvents]);

  const handleWindowChange = (minutes: number) => {
    // Update the rolling window size in the store
    actions.setRtWindowMinutes(minutes);
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Try Tauri command first
      if (window.__TAURI__) {
        try {
          const result = await window.__TAURI__.invoke('get_system_metrics');
          // Update store with fetched data
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

      // Fallback to direct HTTP
      const response = await fetch('http://localhost:5005/api/metrics');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      // Update store with fetched data
      actions.setCounters({
        focusMinutes: Math.round((result.metrics_summary?.total_app_time || 0) / 60),
        distractMinutes: Math.round((result.metrics_summary?.total_app_time || 0) / 60 * 0.3),
        appSwitches: result.metrics_summary?.app_switches || 0,
        idleEvents: result.metrics_summary?.idle_events || 0,
        totalMinutes: Math.round((result.metrics_summary?.total_app_time || 0) / 60)
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

  // WebSocket event handlers with RAF batching
  const handleAppUsageUpdate = useCallback((event: WebSocketEvent) => {
    console.log('App usage update received:', event.data);
    rafBatcher.schedule(() => {
      // Add real-time point to store
      actions.appendRealtime({
        t: event.timestamp * 1000,
        focus: event.data.duration,
        totalInputs: Math.floor(Math.random() * 50) + 10 // Placeholder
      });
      // Bump app switches counter
      actions.bumpCounter("appSwitches");
    });
  }, [rafBatcher, actions]);

  const handleIdleStatus = useCallback((event: WebSocketEvent) => {
    console.log('Idle status update received:', event.data);
    rafBatcher.schedule(() => {
      // Add real-time point to store
      actions.appendRealtime({
        t: event.timestamp * 1000,
        idle: event.data.idle_seconds || 0,
        totalInputs: 0
      });
      // Bump idle events counter
      actions.bumpCounter("idleEvents");
    });
  }, [rafBatcher, actions]);

  const handleInputActivity = useCallback((event: WebSocketEvent) => {
    console.log('Input activity update received:', event.data);
    rafBatcher.schedule(() => {
      // Add real-time point to store
      actions.appendRealtime({
        t: event.timestamp * 1000,
        totalInputs: event.data.total_inputs,
        focus: event.data.keypress_count,
        distract: event.data.mouse_click_count
      });
    });
  }, [rafBatcher, actions]);

  const handleFocusSessionUpdate = useCallback((event: WebSocketEvent) => {
    console.log('Focus session update received:', event.data);
    rafBatcher.schedule(() => {
      // Add real-time point to store
      actions.appendRealtime({
        t: event.timestamp * 1000,
        focus: event.data.duration,
        totalInputs: Math.floor(Math.random() * 20) + 5
      });
    });
  }, [rafBatcher, actions]);

  const handleBreakUpdate = useCallback((event: WebSocketEvent) => {
    console.log('Break update received:', event.data);
    rafBatcher.schedule(() => {
      // Add real-time point to store
      actions.appendRealtime({
        t: event.timestamp * 1000,
        idle: event.data.duration,
        totalInputs: 0
      });
    });
  }, [rafBatcher, actions]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // WebSocket setup
  useEffect(() => {
    // Subscribe to WebSocket status changes
    const unsubscribeStatus = webSocketService.onStatusChange(setWsStatus);

    // Subscribe to real-time events
    webSocketService.subscribe('app_usage_update', handleAppUsageUpdate);
    webSocketService.subscribe('idle_status', handleIdleStatus);
    webSocketService.subscribe('input_activity', handleInputActivity);
    webSocketService.subscribe('focus_session_update', handleFocusSessionUpdate);
    webSocketService.subscribe('break_update', handleBreakUpdate);

    // Try to connect
    webSocketService.connect().catch(console.error);

    return () => {
      unsubscribeStatus();
      webSocketService.unsubscribe('app_usage_update', handleAppUsageUpdate);
      webSocketService.unsubscribe('idle_status', handleIdleStatus);
      webSocketService.unsubscribe('input_activity', handleInputActivity);
      webSocketService.unsubscribe('focus_session_update', handleFocusSessionUpdate);
      webSocketService.unsubscribe('break_update', handleBreakUpdate);
    };
  }, [handleAppUsageUpdate, handleIdleStatus, handleInputActivity, handleFocusSessionUpdate, handleBreakUpdate]);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto mt-4 p-4">
        <div className="card">
          <div className="animate-pulse">
            <div className="h-4 bg-neutral-700 rounded w-1/4 mb-4"></div>
            <div className="h-32 bg-neutral-800 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto mt-4 p-4">
        <div className="card border border-red-500/40">
          <h2 className="text-xl font-bold text-red-400 mb-2">Connection Error</h2>
          <p className="text-red-300">{error}</p>
          <p className="text-sm text-red-400 mt-2">
            {backendConnected 
              ? 'Make sure the backend server is running on port 5005'
              : 'Backend service is not available'
            }
          </p>
                          <motion.button 
                  onClick={fetchData} 
                  className="btn btn-danger mt-4 focus-ring"
                  whileHover={{ y: -2 }}
                  whileTap={{ y: 0 }}
                >
                  Retry
                </motion.button>
        </div>
      </div>
    );
  }

  if (!rt || rt.length === 0) {
    return (
      <div className="max-w-4xl mx-auto mt-8 p-6">
        <div className="card text-center">
          <div className="flex flex-col items-center gap-4 py-8">
            <div className="w-16 h-16 rounded-full bg-brand/10 flex items-center justify-center">
              <svg className="w-8 h-8 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-text">Real-time tracking starting up</h3>
              <p className="text-text-muted max-w-md">
                We're initializing your live analytics dashboard. Make sure the backend service is running and keep the tracker active. 
                Your real-time insights will appear here shortly.
              </p>
              <div className="flex items-center justify-center gap-4 pt-2">
                <a href="#" className="text-sm text-brand hover:text-brand-hover transition-colors">
                  Learn more about real-time tracking →
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Prepare real-time chart data from store
  const inputActivityData = screenshotMode.useSeedData ? seedData.inputActivityData : [
    {
      id: 'Total Inputs',
      data: throttledRealtimeData.map((point: Point, i) => ({
        x: new Date(point.t).toLocaleTimeString(),
        y: point.totalInputs || 0
      }))
    },
    {
      id: 'Focus Inputs',
      data: throttledRealtimeData.map((point: Point, i) => ({
        x: new Date(point.t).toLocaleTimeString(),
        y: point.focus || 0
      }))
    },
    {
      id: 'Distraction Inputs',
      data: throttledRealtimeData.map((point: Point, i) => ({
        x: new Date(point.t).toLocaleTimeString(),
        y: point.distract || 0
      }))
    }
  ];

  const appUsageData = screenshotMode.useSeedData ? seedData.realtimeAppUsageData : throttledRealtimeData.map((point: Point, index) => ({
    id: `Activity-${index}`,
    label: `Activity ${index + 1}`,
    value: point.totalInputs || 0
  }));

  return (
    <div className="max-w-7xl mx-auto mt-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-[22px] md:text-2xl font-semibold tracking-[-0.01em]">Real-Time Dashboard</h1>
        <div className="flex items-center gap-4">
          <WindowSelect 
            value={rtWindowMinutes} 
            onChange={handleWindowChange}
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
        
        {/* Row 1: KPI Metrics - Four Cards */}
        <div className="col-span-12 sm:col-span-6 xl:col-span-3">
          <MetricTile
            icon={<BarChart3 />}
            label="Focus Score"
            value={`${smoothedFocusScore}%`}
            hint="Real-time focus score with smoothing"
            tone="default"
            interactive
          />
        </div>
        <div className="col-span-12 sm:col-span-6 xl:col-span-3">
          <MetricTile
            icon={<MousePointer />}
            label="App Switches"
            value={smoothedAppSwitches}
            hint="Number of application context switches"
            tone="default"
            interactive
          />
        </div>
        <div className="col-span-12 sm:col-span-6 xl:col-span-3">
          <MetricTile
            icon={<Clock />}
            label="Idle Events"
            value={smoothedIdleEvents}
            hint="Times you stepped away from the computer"
            tone="default"
            interactive
          />
        </div>
        <div className="col-span-12 sm:col-span-6 xl:col-span-3">
          <MetricTile
            icon={<Activity />}
            label="Total Time"
            value={formatMinutes(counters.totalMinutes)}
            hint="Total active screen time"
            tone="default"
            interactive
          />
        </div>

        {/* Row 2: Real-time Charts */}
        <div className="col-span-12 md:col-span-6 xl:col-span-7">
          <ChartCard
            title="Live Input Activity"
            subtitle="Real-time keyboard and mouse activity"
            tooltip="Shows your live input activity patterns with point-per-second updates."
            minHeight={360}
          >
            {inputActivityData[0].data.length > 0 ? (
              <ResponsiveLine
                data={inputActivityData}
                margin={{ top: 20, right: 20, bottom: 50, left: 60 }}
                xScale={{ type: 'point' }}
                yScale={{ type: 'linear', min: 'auto', max: 'auto' }}
                axisTop={null}
                axisRight={null}
                axisLeft={{
                  tickSize: 5,
                  tickPadding: 5,
                  tickRotation: 0,
                  legend: 'Inputs',
                  legendOffset: -40,
                  legendPosition: 'middle',
                  tickValues: 'every 2'
                }}
                axisBottom={{
                  tickSize: 5,
                  tickPadding: 5,
                  tickRotation: 0,
                  legend: 'Time',
                  legendOffset: 36,
                  legendPosition: 'middle',
                  tickValues: window.innerWidth < 900 ? 'every 2' : 'every 1'
                }}
                colors={['#12ffe0', '#ff6b6b', '#4ecdc4']}
                pointSize={6}
                pointColor={{ theme: 'background' }}
                pointBorderWidth={2}
                pointBorderColor={{ from: 'serieColor' }}
                pointLabelYOffset={-12}
                useMesh={true}
                enableSlices="x"
                sliceTooltip={({ slice }) => (
                  <div className="bg-surface border border-border rounded-lg p-3 shadow-pop">
                    <div className="text-sm font-medium text-text mb-2">
                      {slice.points[0]?.data.x}
                    </div>
                    {slice.points.map((point) => (
                      <div key={point.id} className="flex items-center justify-between gap-3 mb-1">
                        <div className="flex items-center gap-2">
                          <div 
                            className="w-3 h-3 rounded-full" 
                            style={{ backgroundColor: point.color }}
                          />
                          <span className="text-sm text-text-muted">{point.serieId}</span>
                        </div>
                        <span className="text-sm font-medium text-text">{point.data.y}</span>
                      </div>
                    ))}
                  </div>
                )}
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
                          itemTextColor: '#000'
                        }
                      }
                    ]
                  }
                ]}
              />
            ) : (
              <div className="h-full flex items-center justify-center">
                <div className="text-center space-y-3">
                  <div className="w-12 h-12 rounded-full bg-brand/10 flex items-center justify-center mx-auto">
                    <svg className="w-6 h-6 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 011-1h1a2 2 0 100-4H7a1 1 0 01-1-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
                    </svg>
                  </div>
                  <div className="space-y-1">
                    <h4 className="font-medium text-text">Start interacting to see spikes</h4>
                    <p className="text-sm text-text-muted">
                      Type on your keyboard and move your mouse to see real-time input activity patterns appear here.
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
            title="Live App Usage"
            subtitle={`Last ${rtWindowMinutes} minutes`}
            tooltip="Real-time breakdown of applications used in the current rolling window."
            minHeight={360}
          >
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
                arcLinkLabelsTextColor="#333333"
                arcLinkLabelsThickness={2}
                arcLinkLabelsColor={{ from: 'color' }}
                arcLabelsSkipAngle={10}
                arcLabelsTextColor={{ from: 'color', modifiers: [['darker', 2]] }}
                tooltip={({ datum }) => (
                  <div className="bg-surface border border-border rounded-lg p-3 shadow-pop">
                    <div className="text-sm font-medium text-text mb-1">
                      {datum.label}
                    </div>
                    <div className="text-sm text-text-muted">
                      {Math.round(datum.value)} seconds ({Math.round(datum.percent)}%)
                    </div>
                  </div>
                )}
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
                    symbolShape: 'circle',
                    effects: [
                      {
                        on: 'hover',
                        style: {
                          itemTextColor: '#000'
                        }
                      }
                    ]
                  }
                ]}
              />
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

        {/* Row 3: Activity Timeline - Full Width */}
        <div className="col-span-12">
          <ChartCard
            title="Live Activity Timeline"
            subtitle="Real-time activity feed with virtualized scrolling"
            tooltip="Live feed of your computer activity with virtualized timeline for performance."
            minHeight={400}
          >
            <ActivityTimeline 
              events={timelineEvents}
              maxHeight={400}
            />
          </ChartCard>
        </div>
      </div>
    </div>
  );
}
