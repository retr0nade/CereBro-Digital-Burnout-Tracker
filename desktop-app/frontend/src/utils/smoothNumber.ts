import { useMotionValue, useSpring, useTransform } from 'framer-motion';
import { useEffect, useState } from 'react';

/**
 * Hook that smoothly animates number changes using spring physics
 * to reduce visual jitter when data streams quickly
 */
export function useSmoothedNumber(
  value: number, 
  stiffness: number = 120, 
  damping: number = 18
): number {
  // Create a motion value to store the target value
  const motionValue = useMotionValue(value);
  
  // Create a spring that will smoothly animate to the target
  const spring = useSpring(motionValue, {
    stiffness,
    damping,
    mass: 1,
  });
  
  // Transform the spring value to a rounded number for display
  const roundedValue = useTransform(spring, (latest) => Math.round(latest));
  
  // Update the motion value when the input value changes
  useEffect(() => {
    motionValue.set(value);
  }, [value, motionValue]);
  
  // Return the current spring value, rounded
  return Math.round(spring.get());
}

/**
 * Hook that throttles rapid value changes to prevent excessive re-renders
 * Useful for chart data that updates frequently
 */
export function useThrottledValue<T>(value: T, delay: number = 250): T {
  const [throttledValue, setThrottledValue] = useState<T>(value);
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setThrottledValue(value);
    }, delay);
    
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);
  
  return throttledValue;
}
