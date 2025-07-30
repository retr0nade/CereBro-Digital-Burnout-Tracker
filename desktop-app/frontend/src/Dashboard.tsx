import React, { useEffect, useState } from 'react';
import { ResponsiveLine } from '@nivo/line';

export default function Dashboard() {
  const [data, setData] = useState<any>({});
  useEffect(() => {
    fetch('http://localhost:5005/api/metrics')
      .then(r => r.json()).then(setData);
  }, []);
  return (
    <div className="max-w-xl mx-auto mt-8">
      <h1 className="text-2xl font-bold mb-4">Today’s Focus & Switch Trends</h1>
      <div className="bg-white bg-opacity-10 rounded-xl p-6 shadow-lg">
        <div className="flex justify-between">
          <div>
            <div className="font-mono text-xl">{data.app_switches?.length || 0}</div>
            <div className="text-sm opacity-80">App switches</div>
          </div>
          <div>
            <div className="font-mono text-xl">{data.recent_usage?.length || 0}</div>
            <div className="text-sm opacity-80">Recent Apps</div>
          </div>
        </div>
        <div className="h-56 mt-8">
          {/* Dumb graph using nivo, replace with real data */}
          <ResponsiveLine
            data={[
              {
                id: 'App switches',
                data: data.app_switches?.map((x: any, i: number) => ({
                  x: new Date(x[1]*1000).toLocaleTimeString(),
                  y: i
                })) || []
              }
            ]}
            margin={{ top: 10, right: 10, bottom: 40, left: 50 }}
            xScale={{ type: 'point' }}
            axisLeft={{tickSize:0}}
            axisBottom={{tickSize:2}}
            colors={['#12ffe0']}
            pointSize={4}
            pointColor="#fff"
            lineWidth={2}
            enableGridY={false}
            useMesh={true}
          />
        </div>
      </div>
    </div>
  );
}
