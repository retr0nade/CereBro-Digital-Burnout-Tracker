import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  TooltipProps,
} from 'recharts';
import { motion } from 'framer-motion';
import { Monitor } from 'lucide-react';
import { formatMinutes, truncateText, getChartColor } from './utils';

interface AppUsageDataPoint {
  id: string;
  label: string;
  value: number; // in minutes
  color?: string;
}

interface DonutAppUsageProps {
  data: AppUsageDataPoint[];
  height?: number;
  className?: string;
  maxItems?: number;
}

interface CustomTooltipProps extends TooltipProps<number, string> {}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload }) => {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const data = payload[0].payload as AppUsageDataPoint;
  const percentage = payload[0].percent || 0;

  return (
    <motion.div
      className="bg-surface border border-border rounded-lg p-3 shadow-pop max-w-xs"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.15 }}
    >
      <div className="flex items-start gap-3">
        <Monitor className="w-4 h-4 text-text-muted flex-shrink-0 mt-0.5" />
        <div className="min-w-0 flex-1">
          <div className="text-dashboard-sm font-medium text-text mb-1 leading-tight">
            {data.label}
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-3">
              <span className="text-dashboard-sm text-text-muted">Time Used</span>
              <span className="text-dashboard-sm font-medium text-text">
                {formatMinutes(data.value)}
              </span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-dashboard-sm text-text-muted">Percentage</span>
              <span className="text-dashboard-sm font-medium text-text">
                {percentage.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const CenterLabel: React.FC<{ 
  cx: number; 
  cy: number; 
  totalMinutes: number;
  totalApps: number;
}> = ({ cx, cy, totalMinutes, totalApps }) => {
  return (
    <g>
      <text
        x={cx}
        y={cy - 10}
        textAnchor="middle"
        dominantBaseline="middle"
        className="fill-text font-bold"
        fontSize="24"
      >
        {formatMinutes(totalMinutes)}
      </text>
      <text
        x={cx}
        y={cy + 15}
        textAnchor="middle"
        dominantBaseline="middle"
        className="fill-text-muted"
        fontSize="13"
        letterSpacing="0.025em"
      >
        {totalApps} app{totalApps !== 1 ? 's' : ''}
      </text>
    </g>
  );
};

const CustomLegend: React.FC<{ 
  payload?: any[]; 
  data: AppUsageDataPoint[];
}> = ({ payload, data }) => {
  if (!payload) return null;

  return (
    <div className="flex flex-wrap justify-center gap-4 mt-4 px-4">
      {payload.map((entry, index) => {
        const appData = data.find(d => d.label === entry.value);
        const displayLabel = truncateText(entry.value, 15);
        
        return (
          <motion.div
            key={`legend-${index}`}
            className="flex items-center gap-2 group cursor-default"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <div
              className="w-3 h-3 rounded-sm flex-shrink-0"
              style={{ backgroundColor: entry.color }}
            />
            <div className="min-w-0">
              <div className="text-dashboard-sm text-text truncate group-hover:text-brand transition-colors">
                {displayLabel}
              </div>
              {appData && (
                <div className="text-xs text-text-muted">
                  {formatMinutes(appData.value)}
                </div>
              )}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
};

export default function DonutAppUsage({ 
  data, 
  height = 400, 
  className = '',
  maxItems = 8
}: DonutAppUsageProps) {
  // Process and optimize data
  const processedData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    // Sort by value and take top N items
    const sorted = [...data]
      .filter(item => item.value > 0)
      .sort((a, b) => b.value - a.value);
    
    const topItems = sorted.slice(0, maxItems);
    const remainder = sorted.slice(maxItems);
    
    // Add "Others" category if there are more items
    const processedItems = [...topItems];
    if (remainder.length > 0) {
      const otherTotal = remainder.reduce((sum, item) => sum + item.value, 0);
      processedItems.push({
        id: 'others',
        label: `${remainder.length} Other Apps`,
        value: otherTotal,
        color: getChartColor(maxItems)
      });
    }
    
    // Assign colors if not provided
    return processedItems.map((item, index) => ({
      ...item,
      color: item.color || getChartColor(index)
    }));
  }, [data, maxItems]);

  // Calculate totals
  const totalMinutes = useMemo(() => 
    processedData.reduce((sum, item) => sum + item.value, 0), 
    [processedData]
  );

  const totalApps = useMemo(() => {
    const otherItem = processedData.find(item => item.id === 'others');
    const directApps = processedData.filter(item => item.id !== 'others').length;
    const otherAppsCount = otherItem ? 
      parseInt(otherItem.label.split(' ')[0]) || 0 : 0;
    return directApps + otherAppsCount;
  }, [processedData]);

  if (processedData.length === 0) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ height }}>
        <div className="text-center">
          <Monitor className="w-12 h-12 text-text-muted mx-auto mb-3 opacity-50" />
          <div className="text-text-muted text-dashboard-sm">No app usage data available</div>
        </div>
      </div>
    );
  }

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={processedData}
            cx="50%"
            cy="45%"
            labelLine={false}
            outerRadius={Math.min(height * 0.25, 100)}
            innerRadius={Math.min(height * 0.15, 60)}
            paddingAngle={2}
            dataKey="value"
            animationBegin={0}
            animationDuration={1000}
            animationEasing="ease-out"
          >
            {processedData.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.color}
                stroke="var(--color-surface)"
                strokeWidth={2}
              />
            ))}
            <CenterLabel
              cx={0}
              cy={0}
              totalMinutes={totalMinutes}
              totalApps={totalApps}
            />
          </Pie>
          
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      
      {/* Custom Legend */}
      <CustomLegend data={processedData} payload={processedData.map((item, index) => ({
        value: item.label,
        color: item.color,
        id: item.id
      }))} />
    </div>
  );
}
