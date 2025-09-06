import React, { useEffect, useRef, memo } from 'react';
import { ResponsiveContainer } from 'recharts';

interface StableContainerProps {
  children: React.ReactNode;
  animationOnMountOnly?: boolean;
  width?: string | number;
  height?: string | number;
  className?: string;
}

export const StableContainer = memo<StableContainerProps>(({ 
  children, 
  animationOnMountOnly = true,
  width = '100%',
  height = '100%',
  className 
}) => {
  const mountedRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
  }, []);

  const isAnimationActive = animationOnMountOnly ? !mountedRef.current : true;

  return (
    <ResponsiveContainer width={width} height={height} className={className}>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, {
            ...child.props,
            isAnimationActive
          });
        }
        return child;
      })}
    </ResponsiveContainer>
  );
});

StableContainer.displayName = 'StableContainer';

export default StableContainer;
