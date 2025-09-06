import { Point } from '../state/analyticsStore';

/**
 * Calculate focus score as percentage of productive time vs total active time
 * @param focusMinutes - Minutes spent in productive activities
 * @param distractMinutes - Minutes spent in distracting activities
 * @returns Focus score as percentage (0-100)
 */
export const focusScore = (focusMinutes: number, distractMinutes: number): number => {
  const totalMinutes = focusMinutes + distractMinutes;
  if (totalMinutes === 0) return 0;
  return Math.round((focusMinutes / totalMinutes) * 100);
};

/**
 * Sum minutes from a series of points for a specific key
 * @param series - Array of data points
 * @param key - Key to sum ('focus' or 'distract')
 * @returns Total minutes for the specified key
 */
export const sumMinutes = (series: Point[], key: 'focus' | 'distract'): number => {
  return series.reduce((total, point) => {
    const value = point[key];
    return total + (value || 0);
  }, 0);
};

/**
 * Format minutes into human-readable string
 * @param min - Minutes to format
 * @returns Formatted string like "1h 24m" or "45m"
 */
export const formatMinutes = (min: number): string => {
  if (min < 60) {
    return `${Math.round(min)}m`;
  }
  
  const hours = Math.floor(min / 60);
  const minutes = Math.round(min % 60);
  
  if (minutes === 0) {
    return `${hours}h`;
  }
  
  return `${hours}h ${minutes}m`;
};

/**
 * Calculate total active minutes from a series of points
 * @param series - Array of data points
 * @returns Total active minutes (focus + distract)
 */
export const totalActiveMinutes = (series: Point[]): number => {
  return sumMinutes(series, 'focus') + sumMinutes(series, 'distract');
};

/**
 * Calculate productivity ratio from a series of points
 * @param series - Array of data points
 * @returns Productivity ratio (0-1)
 */
export const productivityRatio = (series: Point[]): number => {
  const focus = sumMinutes(series, 'focus');
  const distract = sumMinutes(series, 'distract');
  return focusScore(focus, distract) / 100;
};
