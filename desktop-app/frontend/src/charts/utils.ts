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