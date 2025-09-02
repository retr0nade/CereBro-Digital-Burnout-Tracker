// Chart utility functions for data processing and formatting

/**
 * Creates a stable domain with padding for consistent chart scaling
 * @param data - Array of data points
 * @param key - Key to extract values from data points
 * @param padPct - Padding percentage (default 10%)
 * @returns [min, max] domain with padding
 */
export function stableDomain(data: any[], key: string, padPct: number = 0.1): [number, number] {
  if (!data || data.length === 0) {
    return [0, 100]; // Fallback domain
  }

  const values = data
    .map(item => typeof item[key] === 'number' ? item[key] : 0)
    .filter(val => !isNaN(val));

  if (values.length === 0) {
    return [0, 100];
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  
  // Handle case where min === max
  if (min === max) {
    const center = min || 10;
    return [center * 0.9, center * 1.1];
  }

  const range = max - min;
  const padding = range * padPct;

  return [
    Math.max(0, min - padding), // Don't go below 0 for most metrics
    max + padding
  ];
}

/**
 * Clamps data series to a maximum number of points for performance
 * Uses intelligent decimation to preserve data shape
 * @param data - Array of data points
 * @param limit - Maximum number of points to keep
 * @returns Clamped data array
 */
export function clampedSeries<T>(data: T[], limit: number = 48): T[] {
  if (!data || data.length <= limit) {
    return data;
  }

  // For small overruns, just take the most recent points
  if (data.length <= limit * 1.2) {
    return data.slice(-limit);
  }

  // For larger datasets, use intelligent decimation
  const step = data.length / limit;
  const result: T[] = [];

  for (let i = 0; i < limit; i++) {
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
}

/**
 * Formats hour number to HH:00 format
 * @param hour - Hour number (0-23)
 * @returns Formatted time string
 */
export function formatHour(hour: number): string {
  const h = Math.floor(Math.max(0, Math.min(23, hour)));
  return `${h.toString().padStart(2, '0')}:00`;
}

/**
 * Formats minutes to human-readable format
 * @param minutes - Number of minutes
 * @returns Formatted time string
 */
export function formatMinutes(minutes: number): string {
  if (minutes < 1) return '< 1 min';
  if (minutes < 60) return `${Math.round(minutes)} min`;
  
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  
  if (mins === 0) return `${hours}h`;
  return `${hours}h ${mins}m`;
}

/**
 * Formats duration with appropriate units
 * @param seconds - Duration in seconds
 * @returns Formatted duration string
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  return formatMinutes(seconds / 60);
}

/**
 * Calculates percentage change between two values
 * @param current - Current value
 * @param previous - Previous value
 * @returns Percentage change
 */
export function percentageChange(current: number, previous: number): number {
  if (previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / previous) * 100;
}

/**
 * Generates a stable color palette for consistent chart theming
 * @param index - Index for color selection
 * @returns CSS color value
 */
export function getChartColor(index: number): string {
  const colors = [
    '#3b82f6', // brand blue
    '#10b981', // success green  
    '#f59e0b', // warning orange
    '#ef4444', // danger red
    '#8b5cf6', // purple
    '#06b6d4', // cyan
    '#84cc16', // lime
    '#f97316', // orange
  ];
  
  return colors[index % colors.length];
}

/**
 * Truncates long text with ellipsis
 * @param text - Text to truncate
 * @param maxLength - Maximum length before truncation
 * @returns Truncated text
 */
export function truncateText(text: string, maxLength: number = 20): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

/**
 * Determines if labels should be hidden based on available width
 * @param containerWidth - Available container width
 * @param dataLength - Number of data points
 * @param minLabelWidth - Minimum width per label
 * @returns Whether labels should be hidden
 */
export function shouldHideLabels(
  containerWidth: number, 
  dataLength: number, 
  minLabelWidth: number = 60
): boolean {
  return (containerWidth / dataLength) < minLabelWidth;
}
