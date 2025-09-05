import React, { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock } from 'lucide-react';
import { shallowCompareChartData, useRenderTracker } from '../utils/performance';

interface ActivityEvent {
  id: string;
  appName: string;
  action: string;
  timestamp: number;
  duration?: number;
  type: 'app_usage' | 'idle' | 'input' | 'focus' | 'break';
}

interface ActivityGroup {
  timestamp: number;
  timeLabel: string;
  events: ActivityEvent[];
}

interface ActivityTimelineProps {
  events: ActivityEvent[];
  maxHeight?: number;
  className?: string;
}

// Helper function to get relative time
const getRelativeTime = (timestamp: number): string => {
  const now = Date.now();
  const diff = now - timestamp;
  
  if (diff < 1000) return 'just now';
  if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`;
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return `${Math.floor(diff / 86400000)}d ago`;
};

// Helper function to get app icon (letter avatar)
const getAppIcon = (appName: string): string => {
  return appName.charAt(0).toUpperCase();
};

// Helper function to get app color
const getAppColor = (appName: string): string => {
  const colors = [
    'bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-orange-500',
    'bg-red-500', 'bg-indigo-500', 'bg-pink-500', 'bg-teal-500'
  ];
  const hash = appName.split('').reduce((a, b) => {
    a = ((a << 5) - a) + b.charCodeAt(0);
    return a & a;
  }, 0);
  return colors[Math.abs(hash) % colors.length];
};

// Helper function to get action icon
const getActionIcon = (type: ActivityEvent['type']): string => {
  switch (type) {
    case 'app_usage': return '📱';
    case 'idle': return '⏸️';
    case 'input': return '⌨️';
    case 'focus': return '🎯';
    case 'break': return '☕';
    default: return '📋';
  }
};

// Simple virtualizer hook
const useVirtualizer = (
  items: ActivityGroup[],
  containerRef: React.RefObject<HTMLDivElement>,
  itemHeight: number = 60,
  overscan: number = 5
) => {
  const [scrollTop, setScrollTop] = useState(0);
  const [containerHeight, setContainerHeight] = useState(0);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      setScrollTop(container.scrollTop);
    };

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerHeight(entry.contentRect.height);
      }
    });

    container.addEventListener('scroll', handleScroll);
    resizeObserver.observe(container);

    return () => {
      container.removeEventListener('scroll', handleScroll);
      resizeObserver.disconnect();
    };
  }, [containerRef]);

  const totalHeight = items.length * itemHeight;
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length - 1,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  );

  const visibleItems = items.slice(startIndex, endIndex + 1);
  const offsetY = startIndex * itemHeight;

  return {
    visibleItems,
    offsetY,
    totalHeight,
    startIndex,
    endIndex,
  };
};

function ActivityTimelineComponent({ 
  events, 
  maxHeight = 400, 
  className = '' 
}: ActivityTimelineProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [prevEventsLength, setPrevEventsLength] = useState(0);
  
  // Track render performance in development
  const renderCount = useRenderTracker('ActivityTimeline');

  // Group events by 5-minute buckets
  const groupedEvents = useMemo(() => {
    if (!events.length) return [];

    const groups: { [key: number]: ActivityEvent[] } = {};
    
    events.forEach(event => {
      // Round timestamp to nearest 5-minute bucket
      const bucketTime = Math.floor(event.timestamp / 300) * 300;
      if (!groups[bucketTime]) {
        groups[bucketTime] = [];
      }
      groups[bucketTime].push(event);
    });

    // Convert to array and sort by timestamp (newest first)
    return Object.entries(groups)
      .map(([timestamp, groupEvents]) => ({
        timestamp: parseInt(timestamp),
        timeLabel: getRelativeTime(parseInt(timestamp)),
        events: groupEvents.sort((a, b) => b.timestamp - a.timestamp)
      }))
      .sort((a, b) => b.timestamp - a.timestamp);
  }, [events]);

  // Detect new events to prevent scroll jumps
  useEffect(() => {
    if (events.length > prevEventsLength) {
      setPrevEventsLength(events.length);
    }
  }, [events.length, prevEventsLength]);

  const { visibleItems, offsetY, totalHeight } = useVirtualizer(
    groupedEvents,
    containerRef,
    80, // Estimated height per group
    3 // Overscan
  );

  // Memoized render function for performance
  const renderEvent = useCallback((event: ActivityEvent) => (
    <motion.div
      key={event.id}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
      className="flex items-center gap-3 py-2 px-3 hover:bg-white/5 rounded-lg transition-colors"
    >
      {/* App Icon */}
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-medium flex-shrink-0 ${getAppColor(event.appName)}`}>
        {getAppIcon(event.appName)}
      </div>
      
      {/* Event Details */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-text truncate">
            {event.appName}
          </span>
          <span className="text-xs text-text-muted">
            {getActionIcon(event.type)}
          </span>
        </div>
        <div className="text-xs text-text-muted">
          {event.action}
          {event.duration && (
            <span className="ml-2 text-text-muted">
              • {Math.round(event.duration / 60)}m
            </span>
          )}
        </div>
      </div>
      
      {/* Time */}
      <div className="text-xs text-text-muted flex-shrink-0">
        {getRelativeTime(event.timestamp)}
      </div>
    </motion.div>
  ), []);

  if (!events.length) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ height: maxHeight }}>
        <div className="text-center">
          <Clock className="w-12 h-12 text-text-muted mx-auto mb-3 opacity-50" />
          <div className="text-text-muted text-dashboard-sm">No activity data available</div>
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <div
        ref={containerRef}
        className="overflow-y-auto scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent"
        style={{ height: maxHeight }}
      >
        <div style={{ height: totalHeight, position: 'relative' }}>
          <div style={{ transform: `translateY(${offsetY}px)` }}>
            <AnimatePresence mode="popLayout">
              {visibleItems.map((group, index) => (
                <motion.div
                  key={group.timestamp}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                  className="mb-4"
                >
                  {/* Time Header */}
                  <div className="flex items-center gap-2 mb-2 px-3">
                    <div className="w-2 h-2 rounded-full bg-brand/60" />
                    <span className="text-xs font-medium text-text-muted">
                      {group.timeLabel}
                    </span>
                    <div className="flex-1 h-px bg-white/10" />
                  </div>
                  
                  {/* Events */}
                  <div className="space-y-1">
                    {group.events.map(renderEvent)}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}

// Memoized component with shallow comparison
const ActivityTimeline = React.memo(ActivityTimelineComponent, shallowCompareChartData);

export default ActivityTimeline;
