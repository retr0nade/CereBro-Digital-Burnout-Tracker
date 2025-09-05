import React, { useEffect, useState } from 'react';
import { ResponsivePie } from '@nivo/pie';
import { ResponsiveBar } from '@nivo/bar';

interface ScreenTimeData {
  daily_stats: Record<string, {
    apps: Record<string, number>;
    total_time: number;
  }>;
  total_records: number;
  idle_records: number;
}

export default function ScreenTime() {
  const [data, setData] = useState<ScreenTimeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>('');

  useEffect(() => {
    fetchScreenTimeData();
  }, []);

  const fetchScreenTimeData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('http://localhost:5005/api/analytics');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      setData(result);
      
      // Set the most recent date as default
      if (result.daily_stats && Object.keys(result.daily_stats).length > 0) {
        const dates = Object.keys(result.daily_stats).sort();
        setSelectedDate(dates[dates.length - 1]);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch screen time data';
      setError(errorMessage);
      console.error('ScreenTime fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto mt-8 p-6">
        <div className="bg-white bg-opacity-10 rounded-xl p-6 shadow-lg">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-300 rounded w-1/3 mb-4"></div>
            <div className="h-64 bg-gray-300 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto mt-8 p-6">
        <div className="bg-red-500 bg-opacity-20 rounded-xl p-6 shadow-lg border border-red-500">
          <h2 className="text-xl font-bold text-red-400 mb-2">Connection Error</h2>
          <p className="text-red-300">{error}</p>
          <button 
            onClick={fetchScreenTimeData}
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
      <div className="max-w-6xl mx-auto mt-8 p-6">
        <div className="card text-center">
          <div className="flex flex-col items-center gap-4 py-8">
            <div className="w-16 h-16 rounded-full bg-brand/10 flex items-center justify-center">
              <svg className="w-8 h-8 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-text">Ready to track your screen time?</h3>
              <p className="text-text-muted max-w-md">
                To start collecting screen time data, make sure the backend service is running and keep the tracker active. 
                Your daily usage patterns will appear here once we have enough data.
              </p>
              <div className="flex items-center justify-center gap-4 pt-2">
                <a href="#" className="text-sm text-brand hover:text-brand-hover transition-colors">
                  Learn more about screen time tracking →
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Prepare pie chart data for app usage
  const pieData = selectedDate && data.daily_stats[selectedDate] 
    ? Object.entries(data.daily_stats[selectedDate].apps)
        .map(([app, count]) => ({
          id: app,
          label: app,
          value: count as number,
          color: `hsl(${Math.random() * 360}, 70%, 50%)`
        }))
        .sort((a, b) => (b.value as number) - (a.value as number))
        .slice(0, 10) // Top 10 apps
    : [];

  // Prepare bar chart data for daily comparison
  const barData = Object.entries(data.daily_stats)
    .map(([date, stats]) => ({
      date,
      'Total Time': (stats as any).total_time,
      'Active Apps': Object.keys((stats as any).apps).length,
      'Idle Events': data.idle_records // This would need to be per-day data
    }))
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .slice(-7); // Last 7 days

  return (
    <div className="max-w-6xl mx-auto mt-8 p-6">
      <h1 className="text-3xl font-bold mb-6 text-center">Screen Time Analytics</h1>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 shadow-lg">
          <div className="text-center">
            <div className="text-4xl font-bold text-white">{data.total_records}</div>
            <div className="text-blue-100">Total Records</div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 shadow-lg">
          <div className="text-center">
            <div className="text-4xl font-bold text-white">{data.idle_records}</div>
            <div className="text-purple-100">Idle Events</div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 shadow-lg">
          <div className="text-center">
            <div className="text-4xl font-bold text-white">{Object.keys(data.daily_stats).length}</div>
            <div className="text-green-100">Days Tracked</div>
          </div>
        </div>
      </div>

      {/* Date Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Select Date:</label>
        <select
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-pink-500"
        >
          {Object.keys(data.daily_stats).sort().map((date) => (
            <option key={date} value={date}>
              {new Date(date).toLocaleDateString()}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* App Usage Pie Chart */}
        <div className="bg-white bg-opacity-10 rounded-xl p-6 shadow-lg">
          <h3 className="text-xl font-bold mb-4">App Usage Distribution</h3>
          <div className="h-80">
            {pieData.length > 0 ? (
              <ResponsivePie
                data={pieData}
                margin={{ top: 40, right: 80, bottom: 80, left: 80 }}
                innerRadius={0.5}
                padAngle={0.7}
                cornerRadius={3}
                activeOuterRadiusOffset={8}
                borderWidth={1}
                borderColor={{ from: 'color', modifiers: [['darker', 0.2]] }}
                arcLinkLabelsSkipAngle={10}
                arcLinkLabelsTextColor="#ffffff"
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
                    itemTextColor: '#ffffff',
                    itemDirection: 'left-to-right',
                    itemOpacity: 1,
                    symbolSize: 18,
                    symbolShape: 'circle'
                  }
                ]}
              />
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400">
                <p>No app usage data for selected date</p>
              </div>
            )}
          </div>
        </div>

        {/* Daily Activity Bar Chart */}
        <div className="bg-white bg-opacity-10 rounded-xl p-6 shadow-lg">
          <h3 className="text-xl font-bold mb-4">Daily Activity (Last 7 Days)</h3>
          <div className="h-80">
            {barData.length > 0 ? (
              <ResponsiveBar
                data={barData}
                keys={['Total Time', 'Active Apps']}
                indexBy="date"
                margin={{ top: 50, right: 130, bottom: 50, left: 60 }}
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
                  legend: 'Date',
                  legendPosition: 'middle',
                  legendOffset: 32
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
                legends={[
                  {
                    dataFrom: 'keys',
                    anchor: 'bottom-right',
                    direction: 'column',
                    justify: false,
                    translateX: 120,
                    translateY: 0,
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
              <div className="h-full flex items-center justify-center text-gray-400">
                <p>No daily activity data available</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Detailed App List */}
      {selectedDate && data.daily_stats[selectedDate] && (
        <div className="mt-8 bg-white bg-opacity-10 rounded-xl p-6 shadow-lg">
          <h3 className="text-xl font-bold mb-4">
            App Usage Details - {new Date(selectedDate).toLocaleDateString()}
          </h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {Object.entries(data.daily_stats[selectedDate].apps)
              .sort(([, a], [, b]) => (b as number) - (a as number))
              .map(([app, count], index) => (
                <div key={app} className="flex justify-between items-center py-3 border-b border-gray-600">
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-medium text-gray-300">#{index + 1}</span>
                    <span className="text-sm">{app}</span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-400">{count} sessions</span>
                    <div className="w-24 bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-pink-500 h-2 rounded-full"
                        style={{ 
                          width: `${(count as number / Math.max(...Object.values(data.daily_stats[selectedDate].apps).map(v => v as number))) * 100}%` 
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
