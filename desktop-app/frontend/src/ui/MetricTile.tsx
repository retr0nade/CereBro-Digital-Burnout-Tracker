import React from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';
import { clsx } from 'clsx';
import GlassCard from './GlassCard';

interface MetricTileProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  hint?: string;
  tone?: 'default' | 'ok' | 'warn' | 'danger';
  className?: string;
  interactive?: boolean;
}

const toneStyles = {
  default: {
    accent: 'text-brand',
    bg: 'bg-brand/5',
    border: 'border-brand/20',
  },
  ok: {
    accent: 'text-ok',
    bg: 'bg-ok/5',
    border: 'border-ok/20',
  },
  warn: {
    accent: 'text-warn',
    bg: 'bg-warn/5',
    border: 'border-warn/20',
  },
  danger: {
    accent: 'text-danger',
    bg: 'bg-danger/5',
    border: 'border-danger/20',
  },
};

export default function MetricTile({
  icon,
  label,
  value,
  hint,
  tone = 'default',
  className,
  interactive = false,
}: MetricTileProps) {
  const styles = toneStyles[tone];
  
  // Animated value with spring physics
  const displayValue = typeof value === 'number' ? value : parseFloat(value.toString()) || 0;
  const springValue = useSpring(displayValue, {
    stiffness: 300,
    damping: 30,
    mass: 0.8,
  });
  
  const animatedValue = useTransform(springValue, (latest) => {
    if (typeof value === 'string' && isNaN(parseFloat(value))) {
      return value; // Return original string if not numeric
    }
    return Math.round(latest).toLocaleString();
  });

  return (
    <GlassCard 
      className={clsx(
        "p-6 relative overflow-hidden",
        styles.bg,
        styles.border,
        className
      )}
      interactive={interactive}
    >
      {/* Background accent */}
      <div className={clsx(
        "absolute top-0 left-0 w-1 h-full",
        styles.accent.replace('text-', 'bg-')
      )} />
      
      {/* Content */}
      <div className="relative z-10 flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {/* Icon */}
          <motion.div
            className={clsx(
              "inline-flex items-center justify-center w-10 h-10 rounded-xl mb-4",
              styles.bg,
              "border",
              styles.border
            )}
            whileHover={{ scale: 1.1, rotate: 5 }}
            transition={{ type: "spring", stiffness: 400, damping: 15 }}
          >
            <div className={clsx("w-5 h-5", styles.accent)}>
              {icon}
            </div>
          </motion.div>

          {/* Value */}
          <div className="mb-2">
            <motion.div
              className={clsx(
                "text-4xl font-bold tracking-tight",
                styles.accent
              )}
              style={{ fontVariantNumeric: 'tabular-nums' }}
            >
              {typeof value === 'string' && isNaN(parseFloat(value)) ? (
                value
              ) : (
                <motion.span>{animatedValue}</motion.span>
              )}
            </motion.div>
            
            {/* Unit or suffix */}
            {typeof value === 'string' && value.includes('%') && (
              <span className={clsx("text-2xl font-medium ml-1", styles.accent)}>
                %
              </span>
            )}
          </div>

          {/* Label */}
          <div className="space-y-1">
            <h3 className="font-medium text-text text-sm leading-tight">
              {label}
            </h3>
            
            {/* Hint */}
            {hint && (
              <motion.p 
                className="text-xs text-text-muted leading-relaxed"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                transition={{ delay: 0.2 }}
              >
                {hint}
              </motion.p>
            )}
          </div>
        </div>

        {/* Decorative element */}
        <motion.div
          className={clsx(
            "w-2 h-2 rounded-full ml-4 mt-2 opacity-60",
            styles.accent.replace('text-', 'bg-')
          )}
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.6, 1, 0.6],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </div>

      {/* Hover glow effect */}
      {interactive && (
        <motion.div
          className={clsx(
            "absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-300",
            "bg-gradient-to-br from-white/[0.02] to-transparent"
          )}
          whileHover={{ opacity: 1 }}
        />
      )}
    </GlassCard>
  );
}
