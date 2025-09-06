import React from 'react';
import GlassCard from './GlassCard';
import SectionHeader from './SectionHeader';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  tooltip?: string;
  children: React.ReactNode;
  minHeight?: number;
  className?: string;
}

export const ChartCard = React.memo<ChartCardProps>(({ 
  title, 
  subtitle, 
  tooltip,
  children, 
  minHeight = 300,
  className = ''
}) => {
  const chartMinHeight = minHeight;
  
  return (
    <GlassCard className={`${className}`}>
      <SectionHeader
        title={title}
        subtitle={subtitle}
        tooltip={tooltip}
        className="mb-4"
      />
      <div 
        className="overflow-hidden"
        style={{ 
          minHeight: `${chartMinHeight}px`,
          height: `${chartMinHeight}px`,
          '--chart-min': `${chartMinHeight}px`
        } as React.CSSProperties}
      >
        {children}
      </div>
    </GlassCard>
  );
});

ChartCard.displayName = 'ChartCard';

export default ChartCard;
