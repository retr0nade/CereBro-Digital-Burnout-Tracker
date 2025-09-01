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
    // Core glass styling
    "rounded-2xl border border-white/[0.08] backdrop-blur-md",
    "bg-surface/40 shadow-soft",
    "transition-all duration-300 ease-out",
    
    // Interactive states
    interactive && "cursor-pointer hover:shadow-lift hover:bg-surface/50",
    interactive && "hover:border-white/[0.12] hover:-translate-y-0.5",
    
    // Custom classes
    className
  );

  const motionProps = interactive ? {
    whileHover: { 
      scale: 1.02,
      y: -2,
      transition: { type: "spring", stiffness: 400, damping: 25 }
    },
    whileTap: { 
      scale: 0.98,
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
