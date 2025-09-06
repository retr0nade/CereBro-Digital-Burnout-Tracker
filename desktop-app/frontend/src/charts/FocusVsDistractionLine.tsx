import React, { memo, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { StableContainer } from './StableRechart';
import { Point } from '../state/analyticsStore';
import { legendFormatter, formatHour, calculateYDomain } from './utils';

interface FocusVsDistractionLineProps {
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


export const FocusVsDistractionLine = memo<FocusVsDistractionLineProps>(({ 
  data, 
  height = 280,
  animationOnMountOnly = true 
}) => {
  // Transform data for chart
  const chartData = useMemo(() => {
    return data.map(point => ({
      hour: new Date(point.t).getHours(),
      focus: Math.round((point.focus || 0) / 60), // Convert to minutes
      distract: Math.round((point.distract || 0) / 60) // Convert to minutes
    }));
  }, [data]);

  const yDomain = useMemo(() => {
    const allValues = data.flatMap(point => [
      point.focus || 0,
      point.distract || 0
    ]);
    return calculateYDomain(allValues);
  }, [data]);

  if (!chartData.length) {
    return (
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
      <LineChart data={chartData} margin={{ top: 20, right: 20, bottom: 50, left: 60 }}>
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
        <Line 
          type="monotone" 
          dataKey="focus" 
          stroke="#10B981" 
          strokeWidth={2}
          dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
          name="Focus Time"
        />
        <Line 
          type="monotone" 
          dataKey="distract" 
          stroke="#EF4444" 
          strokeWidth={2}
          dot={{ fill: '#EF4444', strokeWidth: 2, r: 4 }}
          name="Distraction Time"
        />
      </LineChart>
    </StableContainer>
  );
});

FocusVsDistractionLine.displayName = 'FocusVsDistractionLine';