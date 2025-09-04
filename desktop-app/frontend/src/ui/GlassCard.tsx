import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { clsx } from 'clsx';

interface GlassCardProps extends Omit<HTMLMotionProps<"div">, 'className'> {
  className?: string;
  interactive?: boolean;
}

export default function GlassCard({ 
  children, 
  className, 
  interactive = false, 
  ...props 
}: React.PropsWithChildren<GlassCardProps>) {
  const baseClasses = clsx(
    // Core glass styling with enhanced borders and shadows
    "rounded-2xl border border-white/10 backdrop-blur-md",
    "bg-surface/40 shadow-[0_1px_0_rgba(255,255,255,0.06)_inset,0_8px_24px_rgba(0,0,0,0.35)]",
    "transition-all duration-300 ease-out",
    
    // Interactive states with enhanced hover effects
    interactive && "cursor-pointer hover:shadow-[0_1px_0_rgba(255,255,255,0.08)_inset,0_12px_32px_rgba(0,0,0,0.4)] hover:bg-surface/50",
    interactive && "hover:border-white/15 hover:-translate-y-0.5",
    
    // Focus states
    "focus-visible:outline-2 focus-visible:outline-focus focus-visible:outline-offset-2",
    "focus-visible:shadow-[0_1px_0_rgba(255,255,255,0.08)_inset,0_12px_32px_rgba(0,0,0,0.4),0_0_0_4px_rgba(59,130,246,0.1)]",
    
    // Custom classes
    className
  );

  const motionProps = interactive ? {
    whileHover: { 
      y: -2,
      transition: { type: "spring", stiffness: 400, damping: 25 }
    },
    whileTap: { 
      y: 0,
      transition: { type: "spring", stiffness: 600, damping: 25 }
    },
  } : {};

  return (
    <motion.div
      className={baseClasses}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        type: "spring", 
        stiffness: 300, 
        damping: 30,
        delay: 0.1 
      }}
      {...motionProps}
      {...props}
    >
      {children}
    </motion.div>
  );
}
