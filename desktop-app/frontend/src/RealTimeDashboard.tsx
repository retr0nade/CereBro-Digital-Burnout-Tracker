import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { ResponsiveLine } from '@nivo/line';
import { ResponsivePie } from '@nivo/pie';
import webSocketService, { WebSocketEvent, WebSocketStatus } from './WebSocketService';
import { useSmoothedNumber, useThrottledValue } from './utils/smoothNumber';
import ActivityTimeline from './components/ActivityTimeline';
import SectionHeader from './ui/SectionHeader';
import { EmptyStateBox } from './ui/InfoBox';
import MetricTile from './ui/MetricTile';
import GlassCard from './ui/GlassCard';
import { BarChart3, MousePointer, Clock, Timer, Activity } from 'lucide-react';

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
  const [data, setData] = useState<MetricsData | null>(null);
  const [realTimeMetrics, setRealTimeMetrics] = useState<RealTimeMetrics>({
    appUsage: [],
    idleStatus: null,
    inputActivity: [],
    focusSessions: [],
    breaks: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState(false);
  const [wsStatus, setWsStatus] = useState<WebSocketStatus>({ connected: false, connecting: false });

  // Apply smoothing to rapid-changing metrics to reduce jitter
  const smoothedFocusScore = useSmoothedNumber(data?.focus_score || 0, 120, 18);
  const smoothedAppSwitches = useSmoothedNumber(data?.metrics_summary?.app_switches || 0, 120, 18);
  const smoothedIdleEvents = useSmoothedNumber(data?.metrics_summary?.idle_events || 0, 120, 18);

  // Throttle chart data updates to prevent excessive re-renders
  const throttledInputActivity = useThrottledValue(realTimeMetrics.inputActivity, 250);
  const throttledAppUsage = useThrottledValue(realTimeMetrics.appUsage, 250);

  // Convert real-time data to ActivityTimeline format
  const timelineEvents = useMemo(() => {
    const events: any[] = [];
    
    // Add app usage events
    throttledAppUsage.forEach((usage, index) => {
      events.push({
        id: `rt-usage-${index}`,
        appName: usage.app_name,
        action: 'Used application',
        timestamp: usage.timestamp * 1000,
        duration: usage.duration,
        type: 'app_usage' as const
      });
    });

    // Add input activity events
    throttledInputActivity.forEach((activity, index) => {
      events.push({
        id: `rt-input-${index}`,
        appName: 'System',
        action: `Input activity (${activity.total_inputs} inputs)`,
        timestamp: activity.timestamp * 1000,
        type: 'input' as const
      });
    });

    // Add focus session events
    realTimeMetrics.focusSessions.forEach((session, index) => {
      events.push({
        id: `rt-focus-${index}`,
        appName: 'Focus Timer',
        action: session.was_interrupted ? 'Focus session interrupted' : 'Focus session completed',
        timestamp: session.timestamp * 1000,
        duration: session.duration,
        type: 'focus' as const
      });
    });

    // Add break events
    realTimeMetrics.breaks.forEach((breakEvent, index) => {
      events.push({
        id: `rt-break-${index}`,
        appName: 'Break Monitor',
        action: `${breakEvent.break_type} break`,
        timestamp: breakEvent.timestamp * 1000,
        duration: breakEvent.duration,
        type: 'break' as const
      });
    });

    // Sort by timestamp (newest first) and limit to last 50 events
    return events
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, 50);
  }, [throttledAppUsage, throttledInputActivity, realTimeMetrics.focusSessions, realTimeMetrics.breaks]);

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

  // WebSocket event handlers
  const handleAppUsageUpdate = useCallback((event: WebSocketEvent) => {
    console.log('App usage update received:', event.data);
    setRealTimeMetrics(prev => ({
      ...prev,
      appUsage: [
        ...prev.appUsage,
        {
          app_name: event.data.app_name,
          duration: event.data.duration,
          timestamp: event.timestamp
        }
      ].slice(-50) // Keep last 50 entries
    }));
  }, []);

  const handleIdleStatus = useCallback((event: WebSocketEvent) => {
    console.log('Idle status update received:', event.data);
    setRealTimeMetrics(prev => ({
      ...prev,
      idleStatus: {
        is_idle: event.data.is_idle,
        duration: event.data.idle_seconds,
        timestamp: event.timestamp
      }
    }));
  }, []);

  const handleInputActivity = useCallback((event: WebSocketEvent) => {
    console.log('Input activity update received:', event.data);
    setRealTimeMetrics(prev => ({
      ...prev,
      inputActivity: [
        ...prev.inputActivity,
        {
          timestamp: event.timestamp,
          total_inputs: event.data.total_inputs,
          keypress_count: event.data.keypress_count,
          mouse_click_count: event.data.mouse_click_count
        }
      ].slice(-30) // Keep last 30 entries
    }));
  }, []);

  const handleFocusSessionUpdate = useCallback((event: WebSocketEvent) => {
    console.log('Focus session update received:', event.data);
    setRealTimeMetrics(prev => ({
      ...prev,
      focusSessions: [
        ...prev.focusSessions,
        {
          session_id: event.data.session_id,
          duration: event.data.duration,
          was_interrupted: event.data.was_interrupted,
          timestamp: event.timestamp
        }
      ].slice(-10) // Keep last 10 entries
    }));
  }, []);

  const handleBreakUpdate = useCallback((event: WebSocketEvent) => {
    console.log('Break update received:', event.data);
    setRealTimeMetrics(prev => ({
      ...prev,
      breaks: [
        ...prev.breaks,
        {
          duration: event.data.duration,
          break_type: event.data.break_type,
          timestamp: event.timestamp
        }
      ].slice(-10) // Keep last 10 entries
    }));
  }, []);

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
          <button onClick={fetchData} className="btn btn-danger mt-4">Retry</button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-4xl mx-auto mt-8 p-6">
        <div className="bg-white bg-opacity-10 rounded-xl p-6 shadow-lg">
          <p className="text-center text-gray-400">No data available</p>
        </div>
      </div>
    );
  }

  // Prepare real-time chart data

  // Prepare real-time chart data
  const inputActivityData = [
    {
      id: 'Total Inputs',
      data: throttledInputActivity.map((activity, i) => ({
        x: new Date(activity.timestamp * 1000).toLocaleTimeString(),
        y: activity.total_inputs
      }))
    },
    {
      id: 'Keypresses',
      data: throttledInputActivity.map((activity, i) => ({
        x: new Date(activity.timestamp * 1000).toLocaleTimeString(),
        y: activity.keypress_count
      }))
    },
    {
      id: 'Mouse Clicks',
      data: throttledInputActivity.map((activity, i) => ({
        x: new Date(activity.timestamp * 1000).toLocaleTimeString(),
        y: activity.mouse_click_count
      }))
    }
  ];

  const appUsageData = throttledAppUsage.map(usage => ({
    id: usage.app_name,
    label: usage.app_name,
    value: usage.duration
  }));

  return (
    <div className="max-w-7xl mx-auto mt-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Real-Time Dashboard</h1>
      </div>

      {/* 12-Column Grid Layout */}
      <div className="grid grid-cols-12 gap-3 md:gap-4 xl:gap-6">
        
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
            label="Current Status"
            value={getConnectionStatusText(backendConnected, wsStatus)}
            hint="Backend and WebSocket connection status"
            tone={getConnectionStatusTone(backendConnected, wsStatus)}
            interactive
          />
        </div>

        {/* Row 2: Real-time Charts */}
        <div className="col-span-12 lg:col-span-7">
          <GlassCard className="h-full">
            <SectionHeader
              title="Real-time Input Activity"
              subtitle="Live input activity tracking"
              tooltip="Shows your real-time keyboard and mouse activity patterns."
              className="mb-4"
            />
            <div className="min-h-[280px]">
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
                    legendPosition: 'middle'
                  }}
                  axisBottom={{
                    tickSize: 5,
                    tickPadding: 5,
                    tickRotation: 0,
                    legend: 'Time',
                    legendOffset: 36,
                    legendPosition: 'middle'
                  }}
                  colors={['#12ffe0', '#ff6b6b', '#4ecdc4']}
                  pointSize={6}
                  pointColor={{ theme: 'background' }}
                  pointBorderWidth={2}
                  pointBorderColor={{ from: 'serieColor' }}
                  pointLabelYOffset={-12}
                  useMesh={true}
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
                  <EmptyStateBox
                    title="No Input Activity Data"
                    description="Start typing and moving your mouse to see real-time input activity patterns."
                    icon="activity"
                  />
                </div>
              )}
            </div>
          </GlassCard>
        </div>
        
        <div className="col-span-12 lg:col-span-5">
          <GlassCard className="h-full">
            <SectionHeader
              title="Recent App Usage"
              subtitle="Top applications by time spent"
              tooltip="Visual breakdown of which applications consume most of your time."
              className="mb-4"
            />
            <div className="min-h-[280px]">
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
                  <EmptyStateBox
                    title="No App Usage Data"
                    description="Start using applications to see a breakdown of where you spend your time."
                    icon="activity"
                  />
                </div>
              )}
            </div>
          </GlassCard>
        </div>

        {/* Row 3: Activity Timeline - Full Width */}
        <div className="col-span-12">
          <GlassCard>
            <SectionHeader
              title="Real-time Activity Timeline"
              subtitle="Live activity feed with 5-minute grouping"
              tooltip="Real-time feed of your computer activity, grouped by time for better readability."
              className="mb-4"
            />
            <div className="h-[400px]">
              <ActivityTimeline 
                events={timelineEvents}
                maxHeight={400}
              />
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
