import React, { useMemo, useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  TooltipProps,
} from 'recharts';
import { motion } from 'framer-motion';
import { Clock, Coffee } from 'lucide-react';
import { stableDomain, formatHour, formatMinutes, shouldHideLabels } from './utils';
import { shallowCompareChartData, useRenderTracker } from '../utils/performance';

interface IdleBreakDataPoint {
  hour: number;
  idle: number;
  breaks: number;
}

interface IdleBreakBarProps {
  data: IdleBreakDataPoint[];
  height?: number;
  className?: string;
}

interface CustomTooltipProps extends TooltipProps<number, string> {}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const idleValue = payload.find(p => p.dataKey === 'idle')?.value || 0;
  const breakValue = payload.find(p => p.dataKey === 'breaks')?.value || 0;
  const total = idleValue + breakValue;

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
            <Clock className="w-3 h-3 text-text-muted" />
            <span className="text-dashboard-sm text-text-muted">Idle Time</span>
          </div>
          <span className="text-dashboard-sm font-medium text-text">
            {formatMinutes(idleValue)}
          </span>
        </div>
        
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Coffee className="w-3 h-3 text-text-muted" />
            <span className="text-dashboard-sm text-text-muted">Breaks</span>
          </div>
          <span className="text-dashboard-sm font-medium text-text">
            {formatMinutes(breakValue)}
          </span>
        </div>
        
        {total > 0 && (
          <div className="border-t border-border pt-1.5 mt-1.5">
            <div className="flex items-center justify-between gap-4">
              <span className="text-dashboard-sm text-text-muted">Total Away</span>
              <span className="text-dashboard-sm font-medium text-text">
                {formatMinutes(total)}
              </span>
            </div>
            
            {idleValue > 0 && breakValue > 0 && (
              <div className="flex items-center justify-between gap-4 mt-1">
                <span className="text-dashboard-sm text-text-muted">Break Ratio</span>
                <span className="text-dashboard-sm font-medium text-text">
                  {Math.round((breakValue / total) * 100)}%
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
};

function IdleBreakBarComponent({ 
  data, 
  height = 320, 
  className = '' 
}: IdleBreakBarProps) {
  const [containerWidth, setContainerWidth] = useState(800); // Default assumption
  
  // Track render performance in development
  const renderCount = useRenderTracker('IdleBreakBar');

  // Process data for the chart
  const processedData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    // Ensure data is sorted by hour
    return data.sort((a, b) => a.hour - b.hour);
  }, [data]);

  // Calculate stable domain for consistent scaling
  const yDomain = useMemo(() => {
    if (processedData.length === 0) return [0, 10];
    
    const maxValues = processedData.map(d => Math.max(d.idle + d.breaks, d.idle, d.breaks));
    const maxTotal = Math.max(...maxValues);
    
    return [0, maxTotal * 1.1]; // 10% padding on top
  }, [processedData]);

  // Determine if labels should be hidden based on available space
  const hideLabels = useMemo(() => 
    shouldHideLabels(containerWidth, processedData.length, 50), 
    [containerWidth, processedData.length]
  );

  if (processedData.length === 0) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ height }}>
        <div className="text-text-muted text-dashboard-sm">No idle/break data available</div>
      </div>
    );
  }

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer 
        width="100%" 
        height="100%"
        onResize={(width) => setContainerWidth(width || 800)}
      >
        <BarChart
          data={processedData}
          margin={{ top: 20, right: 30, left: 20, bottom: hideLabels ? 40 : 60 }}
          barCategoryGap="15%"
        >
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="var(--color-border)" 
            opacity={0.3}
          />
          
          <XAxis
            dataKey="hour"
            tickFormatter={hideLabels ? () => '' : formatHour}
            tick={hideLabels ? false : { 
              fill: 'var(--color-text-muted)', 
              fontSize: 13,
              letterSpacing: '0.025em'
            }}
            axisLine={{ stroke: 'var(--color-border)' }}
            tickLine={{ stroke: 'var(--color-border)' }}
            angle={0}
            textAnchor="middle"
            height={hideLabels ? 20 : 40}
            interval={0}
            minTickGap={10}
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
            content={<CustomTooltip />}
            cursor={{ 
              fill: 'var(--color-surface-alt)', 
              opacity: 0.3
            }}
          />
          
          <Legend
            wrapperStyle={{
              fontSize: '13px',
              color: 'var(--color-text-muted)',
              letterSpacing: '0.025em'
            }}
            iconType="rect"
          />
          
          <Bar
            dataKey="idle"
            stackId="activity"
            fill="var(--color-text-muted)"
            name="Idle Time"
            radius={[0, 0, 0, 0]}
            animationBegin={0}
            animationDuration={800}
            animationEasing="ease-out"
          />
          
          <Bar
            dataKey="breaks"
            stackId="activity"
            fill="var(--color-warn)"
            name="Planned Breaks"
            radius={[4, 4, 0, 0]}
            animationBegin={200}
            animationDuration={800}
            animationEasing="ease-out"
          />
        </BarChart>
      </ResponsiveContainer>
      
      {/* Show hint when labels are hidden */}
      {hideLabels && (
        <motion.div
          className="text-center mt-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <span className="text-dashboard-sm text-text-muted">
            Hover bars for time details
          </span>
        </motion.div>
      )}
    </div>
  );
}

// Memoized component with shallow comparison
const IdleBreakBar = React.memo(IdleBreakBarComponent, shallowCompareChartData);

export default IdleBreakBar;
