import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  TooltipProps,
} from 'recharts';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { stableDomain, clampedSeries, formatHour, formatMinutes, percentageChange } from './utils';

interface FocusDataPoint {
  hour: number;
  focus: number;
  distraction: number;
}

interface FocusVsDistractionLineProps {
  data: FocusDataPoint[];
  height?: number;
  className?: string;
}

interface CustomTooltipProps extends TooltipProps<number, string> {
  data?: FocusDataPoint[];
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label, data }) => {
  if (!active || !payload || !payload.length || !data) {
    return null;
  }

  const focusValue = payload.find(p => p.dataKey === 'focus')?.value || 0;
  const distractionValue = payload.find(p => p.dataKey === 'distraction')?.value || 0;
  const delta = focusValue - distractionValue;

  // Calculate trend from previous hour
  const currentIndex = data.findIndex(d => d.hour === Number(label));
  const previousIndex = currentIndex > 0 ? currentIndex - 1 : null;
  const trend = previousIndex !== null 
    ? percentageChange(focusValue, data[previousIndex].focus)
    : 0;

  const getTrendIcon = () => {
    if (Math.abs(trend) < 5) return <Minus className="w-3 h-3 text-text-muted" />;
    return trend > 0 
      ? <TrendingUp className="w-3 h-3 text-ok" />
      : <TrendingDown className="w-3 h-3 text-danger" />;
  };

  return (
    <motion.div
      className="bg-surface border border-border rounded-lg p-3 shadow-pop"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.15 }}
    >
      <div className="text-dashboard-sm font-medium text-text mb-2">
        {formatHour(Number(label))}
      </div>
      
      <div className="space-y-1.5">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-ok" />
            <span className="text-dashboard-sm text-text-muted">Focus</span>
          </div>
          <span className="text-dashboard-sm font-medium text-text">
            {formatMinutes(focusValue)}
          </span>
        </div>
        
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-danger" />
            <span className="text-dashboard-sm text-text-muted">Distraction</span>
          </div>
          <span className="text-dashboard-sm font-medium text-text">
            {formatMinutes(distractionValue)}
          </span>
        </div>
        
        <div className="border-t border-border pt-1.5 mt-1.5">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              {getTrendIcon()}
              <span className="text-dashboard-sm text-text-muted">Net Focus</span>
            </div>
            <span className={`text-dashboard-sm font-medium ${
              delta > 0 ? 'text-ok' : delta < 0 ? 'text-danger' : 'text-text-muted'
            }`}>
              {delta > 0 ? '+' : ''}{formatMinutes(Math.abs(delta))}
            </span>
          </div>
          
          {Math.abs(trend) >= 5 && (
            <div className="flex items-center justify-between gap-4 mt-1">
              <span className="text-dashboard-sm text-text-muted">Trend</span>
              <span className={`text-dashboard-sm font-medium ${
                trend > 0 ? 'text-ok' : 'text-danger'
              }`}>
                {trend > 0 ? '+' : ''}{trend.toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default function FocusVsDistractionLine({ 
  data, 
  height = 320, 
  className = '' 
}: FocusVsDistractionLineProps) {
  // Process and optimize data
  const processedData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    // Clamp series to last 48 hours for performance
    const clamped = clampedSeries(data, 48);
    
    // Ensure data is sorted by hour
    return clamped.sort((a, b) => a.hour - b.hour);
  }, [data]);

  // Calculate stable domains
  const focusDomain = useMemo(() => 
    stableDomain(processedData, 'focus', 0.1), [processedData]
  );
  const distractionDomain = useMemo(() => 
    stableDomain(processedData, 'distraction', 0.1), [processedData]
  );
  
  // Use the larger domain for both lines to ensure proper comparison
  const yDomain: [number, number] = useMemo(() => [
    Math.min(focusDomain[0], distractionDomain[0]),
    Math.max(focusDomain[1], distractionDomain[1])
  ], [focusDomain, distractionDomain]);

  if (processedData.length === 0) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ height }}>
        <div className="text-text-muted text-dashboard-sm">No focus data available</div>
      </div>
    );
  }

  // Determine optimal tick count based on data length
  const tickCount = Math.min(8, Math.max(4, Math.ceil(processedData.length / 6)));

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={processedData}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="var(--color-border)" 
            opacity={0.3}
          />
          
          <XAxis
            dataKey="hour"
            tickFormatter={formatHour}
            tick={{ 
              fill: 'var(--color-text-muted)', 
              fontSize: 13,
              letterSpacing: '0.025em'
            }}
            axisLine={{ stroke: 'var(--color-border)' }}
            tickLine={{ stroke: 'var(--color-border)' }}
            angle={0}
            textAnchor="middle"
            height={40}
            tickCount={tickCount}
            minTickGap={20}
            interval="preserveStartEnd"
          />
          
          <YAxis
            domain={yDomain}
            tickFormatter={(value) => formatMinutes(value)}
            tick={{ 
              fill: 'var(--color-text-muted)', 
              fontSize: 13,
              letterSpacing: '0.025em'
            }}
            axisLine={{ stroke: 'var(--color-border)' }}
            tickLine={{ stroke: 'var(--color-border)' }}
            width={60}
            tickCount={6}
          />
          
          <Tooltip 
            content={<CustomTooltip data={processedData} />}
            cursor={{ 
              stroke: 'var(--color-focus)', 
              strokeWidth: 1,
              strokeDasharray: '2 2'
            }}
          />
          
          <Legend
            wrapperStyle={{
              fontSize: '13px',
              color: 'var(--color-text-muted)',
              letterSpacing: '0.025em'
            }}
            iconType="line"
          />
          
          <Line
            type="monotone"
            dataKey="focus"
            stroke="var(--color-ok)"
            strokeWidth={2.5}
            dot={{ 
              fill: 'var(--color-ok)', 
              strokeWidth: 0,
              r: 4
            }}
            activeDot={{ 
              r: 6, 
              fill: 'var(--color-ok)',
              stroke: 'var(--color-surface)',
              strokeWidth: 2
            }}
            name="Focus Time"
            connectNulls={false}
            animationBegin={0}
            animationDuration={800}
            animationEasing="ease-out"
          />
          
          <Line
            type="monotone"
            dataKey="distraction"
            stroke="var(--color-danger)"
            strokeWidth={2.5}
            dot={{ 
              fill: 'var(--color-danger)', 
              strokeWidth: 0,
              r: 4
            }}
            activeDot={{ 
              r: 6, 
              fill: 'var(--color-danger)',
              stroke: 'var(--color-surface)',
              strokeWidth: 2
            }}
            name="Distraction Time"
            connectNulls={false}
            animationBegin={200}
            animationDuration={800}
            animationEasing="ease-out"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
