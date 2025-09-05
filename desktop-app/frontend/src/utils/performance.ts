import React from 'react';

/**
 * Shallow comparison function optimized for chart data
 * Compares data length and last point to minimize unnecessary re-renders
 */
export function shallowCompareChartData<T extends { [key: string]: any }>(
  prevProps: { data?: T[]; [key: string]: any },
  nextProps: { data?: T[]; [key: string]: any }
): boolean {
  // Handle undefined/null data
  if (!prevProps.data || !nextProps.data) {
    return prevProps.data === nextProps.data;
  }

  // Additional safety check for data arrays
  if (!Array.isArray(prevProps.data) || !Array.isArray(nextProps.data)) {
    return prevProps.data === nextProps.data;
  }

  // Compare data length first (fastest check)
  if (prevProps.data.length !== nextProps.data.length) {
    return false;
  }

  // If no data, they're equal
  if (prevProps.data.length === 0) {
    return true;
  }

  // Compare last data point (most likely to change)
  const prevLast = prevProps.data[prevProps.data.length - 1];
  const nextLast = nextProps.data[nextProps.data.length - 1];
  
  if (!prevLast || !nextLast) {
    return false;
  }

  // Compare all keys in the last data point
  const prevKeys = Object.keys(prevLast);
  const nextKeys = Object.keys(nextLast);
  
  if (prevKeys.length !== nextKeys.length) {
    return false;
  }

  for (const key of prevKeys) {
    if (prevLast[key] !== nextLast[key]) {
      return false;
    }
  }

  // Compare other props (excluding data)
  const prevOtherProps = { ...prevProps };
  const nextOtherProps = { ...nextProps };
  delete prevOtherProps.data;
  delete nextOtherProps.data;

  for (const key in prevOtherProps) {
    if (prevOtherProps[key] !== nextOtherProps[key]) {
      return false;
    }
  }

  return true;
}

/**
 * Rolling window utility for time-series data
 * Caps arrays to a maximum number of points while preserving data shape
 */
export function createRollingWindow<T>(maxPoints: number = 72) {
  return function rollingWindow(data: T[]): T[] {
    if (!data || data.length <= maxPoints) {
      return data;
    }

    // For small overruns, just take the most recent points
    if (data.length <= maxPoints * 1.2) {
      return data.slice(-maxPoints);
    }

    // For larger datasets, use intelligent decimation
    const step = data.length / maxPoints;
    const result: T[] = [];

    for (let i = 0; i < maxPoints; i++) {
      const index = Math.floor(i * step);
      if (index < data.length) {
        result.push(data[index]);
      }
    }

    // Always include the last point to preserve the most recent data
    if (result[result.length - 1] !== data[data.length - 1]) {
      result[result.length - 1] = data[data.length - 1];
    }

    return result;
  };
}

/**
 * RequestAnimationFrame batching utility for realtime updates
 */
export class RAFBatcher {
  private pendingUpdates = new Set<() => void>();
  private rafId: number | null = null;

  schedule(updateFn: () => void): void {
    this.pendingUpdates.add(updateFn);
    
    if (this.rafId === null) {
      this.rafId = requestAnimationFrame(() => {
        this.flush();
      });
    }
  }

  private flush(): void {
    const updates = Array.from(this.pendingUpdates);
    this.pendingUpdates.clear();
    this.rafId = null;

    updates.forEach(update => update());
  }

  cancel(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.pendingUpdates.clear();
  }
}

/**
 * Hook for using RAF batching in React components
 */
export function useRAFBatching() {
  const batcherRef = React.useRef<RAFBatcher | null>(null);
  
  if (!batcherRef.current) {
    batcherRef.current = new RAFBatcher();
  }

  React.useEffect(() => {
    return () => {
      batcherRef.current?.cancel();
    };
  }, []);

  return batcherRef.current;
}

/**
 * Performance monitoring utilities for development
 */
export interface RenderStats {
  componentName: string;
  renderCount: number;
  lastRenderTime: number;
  averageRenderTime: number;
}

class PerformanceMonitor {
  private stats = new Map<string, RenderStats>();
  private renderTimes = new Map<string, number[]>();

  recordRender(componentName: string, renderTime: number): void {
    const existing = this.stats.get(componentName);
    const renderTimes = this.renderTimes.get(componentName) || [];
    
    renderTimes.push(renderTime);
    // Keep only last 10 render times for average calculation
    if (renderTimes.length > 10) {
      renderTimes.shift();
    }
    
    const averageRenderTime = renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length;
    
    this.stats.set(componentName, {
      componentName,
      renderCount: (existing?.renderCount || 0) + 1,
      lastRenderTime: renderTime,
      averageRenderTime
    });
    
    this.renderTimes.set(componentName, renderTimes);
  }

  getStats(): RenderStats[] {
    return Array.from(this.stats.values()).sort((a, b) => b.renderCount - a.renderCount);
  }

  reset(): void {
    this.stats.clear();
    this.renderTimes.clear();
  }
}

export const performanceMonitor = new PerformanceMonitor();

/**
 * Hook for tracking component render performance
 */
export function useRenderTracker(componentName: string) {
  const renderCountRef = React.useRef(0);
  const startTimeRef = React.useRef(performance.now());
  
  React.useEffect(() => {
    renderCountRef.current += 1;
    const renderTime = performance.now() - startTimeRef.current;
    performanceMonitor.recordRender(componentName, renderTime);
    startTimeRef.current = performance.now();
  });

  return renderCountRef.current;
}
