import React, { useEffect, useState } from 'react';
import { ResponsiveLine } from '@nivo/line';

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

declare global {
  interface Window {
    __TAURI__: {
      invoke: (command: string, args?: any) => Promise<any>;
    };
  }
}

export default function Dashboard() {
  const [data, setData] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState(false);

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

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto mt-8 p-6">
        <div className="bg-white bg-opacity-10 rounded-xl p-6 shadow-lg">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-300 rounded w-1/4 mb-4"></div>
            <div className="h-32 bg-gray-300 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto mt-8 p-6">
        <div className="bg-red-500 bg-opacity-20 rounded-xl p-6 shadow-lg border border-red-500">
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
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
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

  // Prepare chart data
  const chartData = [
    {
      id: 'App Switches',
      data: data.app_switches?.map((switch_data: any, i: number) => ({
        x: new Date(switch_data[1] * 1000).toLocaleTimeString(),
        y: i + 1
      })) || []
    }
  ];

  return (
    <div className="max-w-4xl mx-auto mt-8 p-6">
      <h1 className="text-3xl font-bold mb-6 text-center">CereBro Dashboard</h1>
      
      {/* Connection Status */}
      <div className={`mb-6 p-3 rounded-lg ${
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
              ? 'Connected to backend via Tauri' 
              : 'Connected via HTTP (Tauri unavailable)'
            }
          </span>
        </div>
      </div>
      
      {/* Focus Score Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 shadow-lg">
          <div className="text-center">
            <div className="text-4xl font-bold text-white">{data.focus_score}%</div>
            <div className="text-green-100">Focus Score</div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 shadow-lg">
          <div className="text-center">
            <div className="text-4xl font-bold text-white">{data.metrics_summary.app_switches}</div>
            <div className="text-blue-100">App Switches</div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 shadow-lg">
          <div className="text-center">
            <div className="text-4xl font-bold text-white">{data.metrics_summary.idle_events}</div>
            <div className="text-purple-100">Idle Events</div>
          </div>
        </div>
      </div>

      {/* Burnout Signals */}
      {data.burnout_signals && data.burnout_signals.length > 0 && (
        <div className="bg-yellow-500 bg-opacity-20 rounded-xl p-6 shadow-lg border border-yellow-500 mb-8">
          <h3 className="text-xl font-bold text-yellow-400 mb-4">⚠️ Burnout Signals Detected</h3>
          <ul className="space-y-2">
            {data.burnout_signals.map((signal, index) => (
              <li key={index} className="text-yellow-300 flex items-center">
                <span className="mr-2">•</span>
                {signal}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Chart */}
      <div className="bg-white bg-opacity-10 rounded-xl p-6 shadow-lg">
        <h3 className="text-xl font-bold mb-4">Activity Timeline</h3>
        <div className="h-64">
          {chartData[0].data.length > 0 ? (
            <ResponsiveLine
              data={chartData}
              margin={{ top: 20, right: 20, bottom: 50, left: 60 }}
              xScale={{ type: 'point' }}
              yScale={{ type: 'linear', min: 'auto', max: 'auto' }}
              axisTop={null}
              axisRight={null}
              axisLeft={{
                tickSize: 5,
                tickPadding: 5,
                tickRotation: 0,
                legend: 'Switches',
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
              colors={['#12ffe0']}
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
                  itemTextColor: '#999',
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
            <div className="h-full flex items-center justify-center text-gray-400">
              <p>No activity data available</p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="mt-8 bg-white bg-opacity-10 rounded-xl p-6 shadow-lg">
        <h3 className="text-xl font-bold mb-4">Recent Activity</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {data.recent_usage?.slice(0, 10).map((usage: any, index: number) => (
            <div key={index} className="flex justify-between items-center py-2 border-b border-gray-600">
              <span className="text-sm">{usage[0]}</span>
              <span className="text-xs text-gray-400">
                {new Date(usage[2] * 1000).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
