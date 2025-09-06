// Shared legend formatter utility
export const legendFormatter = (value: string): string => {
  if (value.length <= 12) return value;
  return value.substring(0, 12) + '...';
};

// Format hour for display
export const formatHour = (hour: number): string => {
  if (hour === 0) return '12 AM';
  if (hour < 12) return `${hour} AM`;
  if (hour === 12) return '12 PM';
  return `${hour - 12} PM`;
};

// Calculate Y-axis domain with padding
export const calculateYDomain = (values: number[], paddingPercent = 0.1): [number, number] => {
  const max = Math.max(...values);
  const min = Math.min(...values);
  
  const padding = (max - min) * paddingPercent;
  
  return [
    Math.max(0, min - padding),
    max + padding
  ];
};

// Format minutes to human readable string
export const formatMinutes = (minutes: number): string => {
  if (minutes < 60) {
    return `${Math.round(minutes)}m`;
  }
  
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = Math.round(minutes % 60);
  
  if (remainingMinutes === 0) {
    return `${hours}h`;
  }
  
  return `${hours}h ${remainingMinutes}m`;
};

// Truncate text with ellipsis
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

// Get chart color by index
export const getChartColor = (index: number): string => {
  const colors = [
    '#3B82F6', // Blue
    '#10B981', // Green
    '#F59E0B', // Yellow
    '#EF4444', // Red
    '#8B5CF6', // Purple
    '#06B6D4', // Cyan
    '#84CC16', // Lime
    '#F97316', // Orange
    '#EC4899', // Pink
    '#6B7280', // Gray
  ];
  
  return colors[index % colors.length];
};