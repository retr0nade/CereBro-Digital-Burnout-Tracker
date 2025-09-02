import React, { useEffect, useState, useCallback } from 'react';
import { ResponsiveLine } from '@nivo/line';
import { ResponsivePie } from '@nivo/pie';
import webSocketService, { WebSocketEvent, WebSocketStatus } from './WebSocketService';
import { useSmoothedNumber, useThrottledValue } from './utils/smoothNumber';

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

  // Apply smoothing to rapid-changing metrics to reduce jitter
  const smoothedFocusScore = useSmoothedNumber(data?.focus_score || 0, 120, 18);
  const smoothedAppSwitches = useSmoothedNumber(data?.metrics_summary?.app_switches || 0, 120, 18);
  const smoothedIdleEvents = useSmoothedNumber(data?.metrics_summary?.idle_events || 0, 120, 18);

  // Throttle chart data updates to prevent excessive re-renders
  const throttledInputActivity = useThrottledValue(realTimeMetrics.inputActivity, 250);
  const throttledAppUsage = useThrottledValue(realTimeMetrics.appUsage, 250);

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
    <div className="max-w-6xl mx-auto mt-4 p-4">
      <h1 className="text-2xl font-semibold mb-4">Real-Time</h1>
      
      {/* Connection Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className={`p-3 rounded-lg ${
          backendConnected 
            ? 'bg-green-500 bg-opacity-20 border border-green-500' 
            : 'bg-yellow-500 bg-opacity-20 border border-yellow-500'
        }`}>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              backendConnected ? 'bg-green-500' : 'bg-yellow-500'
            }`} />
            <span className="text-sm">
              {backendConnected 
                ? 'Backend Connected' 
                : 'Backend Disconnected'
              }
            </span>
          </div>
        </div>

        <div className={`p-3 rounded-lg ${
          wsStatus.connected 
            ? 'bg-blue-500 bg-opacity-20 border border-blue-500' 
            : wsStatus.connecting
            ? 'bg-yellow-500 bg-opacity-20 border border-yellow-500'
            : 'bg-red-500 bg-opacity-20 border border-red-500'
        }`}>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              wsStatus.connected ? 'bg-blue-500' : wsStatus.connecting ? 'bg-yellow-500' : 'bg-red-500'
            }`} />
            <span className="text-sm">
              {wsStatus.connected 
                ? 'WebSocket Connected' 
                : wsStatus.connecting
                ? 'WebSocket Connecting...'
                : 'WebSocket Disconnected'
              }
            </span>
          </div>
        </div>
      </div>
      
      {/* Real-time Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <div className="card">
          <div className="text-center">
            <div className="text-4xl font-bold text-white">{smoothedFocusScore}%</div>
            <div className="text-green-100">Focus Score</div>
          </div>
        </div>
        
        <div className="card">
          <div className="text-center">
            <div className="text-4xl font-bold text-white">{smoothedAppSwitches}</div>
            <div className="text-blue-100">App Switches</div>
          </div>
        </div>
        
        <div className="card">
          <div className="text-center">
            <div className="text-4xl font-bold text-white">{smoothedIdleEvents}</div>
            <div className="text-purple-100">Idle Events</div>
          </div>
        </div>

        <div className="card">
          <div className="text-center">
            <div className="text-4xl font-bold text-white">
              {realTimeMetrics.idleStatus?.is_idle ? 'Idle' : 'Active'}
            </div>
            <div className="text-orange-100">Current Status</div>
          </div>
        </div>
      </div>

      {/* Real-time Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        {/* Input Activity Chart */}
        <div className="card">
          <h3 className="card-title">Real-time Input Activity</h3>
          <div className="h-64">
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
              <div className="h-full flex items-center justify-center muted">
                <p>No input activity data available</p>
              </div>
            )}
          </div>
        </div>

        {/* App Usage Pie Chart */}
        <div className="card">
          <h3 className="card-title">Recent App Usage</h3>
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
              <div className="h-full flex items-center justify-center muted">
                <p>No app usage data available</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Real-time Activity Feed */}
      <div className="card">
        <h3 className="card-title">Real-time Activity Feed</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {realTimeMetrics.appUsage.slice(-10).reverse().map((usage, index) => (
            <div key={index} className="flex justify-between items-center py-2 border-b border-white/10">
              <span className="text-sm">📱 {usage.app_name}</span>
              <span className="text-xs muted">
                {usage.duration}s • {new Date(usage.timestamp * 1000).toLocaleTimeString()}
              </span>
            </div>
          ))}
          {realTimeMetrics.inputActivity.slice(-5).reverse().map((activity, index) => (
            <div key={`input-${index}`} className="flex justify-between items-center py-2 border-b border-white/10">
              <span className="text-sm">⌨️ Input Activity</span>
              <span className="text-xs muted">
                {activity.total_inputs} inputs • {new Date(activity.timestamp * 1000).toLocaleTimeString()}
              </span>
            </div>
          ))}
          {realTimeMetrics.focusSessions.slice(-3).reverse().map((session, index) => (
            <div key={`focus-${index}`} className="flex justify-between items-center py-2 border-b border-white/10">
              <span className="text-sm">🎯 Focus Session</span>
              <span className="text-xs muted">
                {session.duration}s • {session.was_interrupted ? 'Interrupted' : 'Completed'} • {new Date(session.timestamp * 1000).toLocaleTimeString()}
              </span>
            </div>
          ))}
          {realTimeMetrics.breaks.slice(-3).reverse().map((break_, index) => (
            <div key={`break-${index}`} className="flex justify-between items-center py-2 border-b border-white/10">
              <span className="text-sm">☕ Break</span>
              <span className="text-xs muted">
                {break_.duration}s • {break_.break_type} • {new Date(break_.timestamp * 1000).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
