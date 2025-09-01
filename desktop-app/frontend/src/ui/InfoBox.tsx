import React from 'react';
import { motion } from 'framer-motion';
import { 
  AlertCircle, 
  Info, 
  Search, 
  Database, 
  Clock, 
  TrendingUp,
  BarChart3,
  Activity,
  type LucideIcon 
} from 'lucide-react';
import { clsx } from 'clsx';

type InfoBoxVariant = 'info' | 'empty' | 'error' | 'warning';
type InfoBoxIcon = 'info' | 'search' | 'database' | 'clock' | 'chart' | 'activity' | 'trending';

interface InfoBoxProps {
  title: string;
  description: string;
  variant?: InfoBoxVariant;
  icon?: InfoBoxIcon;
  action?: React.ReactNode;
  className?: string;
}

const variantStyles = {
  info: {
    bg: 'bg-brand/5',
    border: 'border-brand/20',
    iconColor: 'text-brand',
    textColor: 'text-text',
  },
  empty: {
    bg: 'bg-text-muted/5',
    border: 'border-border',
    iconColor: 'text-text-muted',
    textColor: 'text-text-muted',
  },
  error: {
    bg: 'bg-danger/5',
    border: 'border-danger/20',
    iconColor: 'text-danger',
    textColor: 'text-text',
  },
  warning: {
    bg: 'bg-warn/5',
    border: 'border-warn/20',
    iconColor: 'text-warn',
    textColor: 'text-text',
  },
};

const iconMap: Record<InfoBoxIcon, LucideIcon> = {
  info: Info,
  search: Search,
  database: Database,
  clock: Clock,
  chart: BarChart3,
  activity: Activity,
  trending: TrendingUp,
};

const getDefaultIcon = (variant: InfoBoxVariant): InfoBoxIcon => {
  switch (variant) {
    case 'error':
    case 'warning':
      return 'info';
    case 'empty':
      return 'search';
    default:
      return 'info';
  }
};

export default function InfoBox({
  title,
  description,
  variant = 'info',
  icon: iconProp,
  action,
  className,
}: InfoBoxProps) {
  const styles = variantStyles[variant];
  const iconKey = iconProp || getDefaultIcon(variant);
  const IconComponent = iconMap[iconKey];

  return (
    <motion.div
      className={clsx(
        "flex items-start gap-3 p-4 rounded-xl border",
        styles.bg,
        styles.border,
        "transition-all duration-200",
        className
      )}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ 
        type: "spring", 
        stiffness: 300, 
        damping: 25,
        delay: 0.1 
      }}
    >
      {/* Icon */}
      <motion.div
        className={clsx(
          "flex items-center justify-center w-10 h-10 rounded-lg",
          "bg-surface/50 border border-border/50",
          styles.iconColor
        )}
        initial={{ rotate: -10, scale: 0.8 }}
        animate={{ rotate: 0, scale: 1 }}
        transition={{ 
          type: "spring", 
          stiffness: 400, 
          damping: 15,
          delay: 0.2 
        }}
      >
        <IconComponent className="w-5 h-5" />
      </motion.div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <motion.h3
          className={clsx(
            "font-medium text-sm leading-tight mb-1",
            variant === 'empty' ? 'text-text-muted' : 'text-text'
          )}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          {title}
        </motion.h3>
        
        <motion.p
          className={clsx(
            "text-xs leading-relaxed",
            styles.textColor
          )}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          {description}
        </motion.p>

        {/* Action slot */}
        {action && (
          <motion.div
            className="mt-3"
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            {action}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

// Preset configurations for common use cases
export const EmptyStateBox = (props: Omit<InfoBoxProps, 'variant'>) => (
  <InfoBox {...props} variant="empty" />
);

export const ErrorBox = (props: Omit<InfoBoxProps, 'variant'>) => (
  <InfoBox {...props} variant="error" />
);

export const WarningBox = (props: Omit<InfoBoxProps, 'variant'>) => (
  <InfoBox {...props} variant="warning" />
);

export const InfoCard = (props: Omit<InfoBoxProps, 'variant'>) => (
  <InfoBox {...props} variant="info" />
);
