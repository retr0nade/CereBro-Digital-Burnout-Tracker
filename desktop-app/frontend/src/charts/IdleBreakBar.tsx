import React, { memo, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { StableContainer } from './StableRechart';
import { Point } from '../state/analyticsStore';
import { legendFormatter, formatHour, calculateYDomain } from './utils';

interface IdleBreakBarProps {
  data: Point[];
  height?: number;
  animationOnMountOnly?: boolean;
}

// Custom tooltip component with memo to prevent re-renders
const CustomTooltip = memo(({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div 
      className="bg-surface border border-border rounded-lg p-3 shadow-pop"
      style={{ pointerEvents: 'auto' }}
    >
      <div className="text-sm font-medium text-text mb-2">
        {formatHour(label)}
      </div>
      {payload.map((entry: any, index: number) => (
        <div key={index} className="flex items-center justify-between gap-3 mb-1">
          <div className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-sm text-text-muted">{entry.name}</span>
          </div>
          <span className="text-sm font-medium text-text">
            {Math.round(entry.value)}m
          </span>
        </div>
      ))}
    </div>
  );
});

CustomTooltip.displayName = 'CustomTooltip';


export const IdleBreakBar = memo<IdleBreakBarProps>(({ 
  data, 
  height = 280,
  animationOnMountOnly = true 
}) => {
  // Transform data for chart
  const chartData = useMemo(() => {
    return data.map(point => ({
      hour: new Date(point.t).getHours(),
      idle: Math.round((point.idle || 0) / 60), // Convert to minutes
      breaks: Math.round((point.focus || 0) / 60) // Using focus as break placeholder
    }));
  }, [data]);

  const yDomain = useMemo(() => {
    const allValues = data.flatMap(point => [
      point.idle || 0,
      point.focus || 0 // Using focus as break time placeholder
    ]);
    return calculateYDomain(allValues);
  }, [data]);

  if (!chartData.length) {
    return (
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
          </div>
        </div>
      </div>
    );
  }

  return (
    <StableContainer 
      height={height} 
      animationOnMountOnly={animationOnMountOnly}
    >
      <BarChart data={chartData} margin={{ top: 20, right: 20, bottom: 50, left: 60 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis 
          dataKey="hour"
          tickFormatter={formatHour}
          minTickGap={24}
          interval="preserveStartEnd"
          className="axis-label"
        />
        <YAxis 
          domain={yDomain}
          className="axis-label"
          tickFormatter={(value) => `${value}m`}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend 
          wrapperStyle={{ paddingTop: '20px' }}
          formatter={(value) => legendFormatter(value)}
        />
        <Bar 
          dataKey="idle" 
          stackId="a"
          fill="#F59E0B" 
          name="Idle Time"
          radius={[0, 0, 4, 4]}
        />
        <Bar 
          dataKey="breaks" 
          stackId="a"
          fill="#8B5CF6" 
          name="Break Time"
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </StableContainer>
  );
});

IdleBreakBar.displayName = 'IdleBreakBar';