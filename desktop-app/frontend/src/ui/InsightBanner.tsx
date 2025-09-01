import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, Brain, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { clsx } from 'clsx';
import GlassCard from './GlassCard';

interface InsightItem {
  id: string;
  type: string;
  severity: 'info' | 'warning' | 'error' | string;
  message: string;
  rule: string;
  timestamp: number;
}

interface InsightBannerProps {
  title: string;
  insights: InsightItem[];
  status?: 'ok' | 'warn' | 'danger';
  className?: string;
  defaultExpanded?: boolean;
}

const statusConfig = {
  ok: {
    accent: 'bg-ok',
    icon: Info,
    iconColor: 'text-ok',
    bgColor: 'bg-ok/5',
    borderColor: 'border-ok/20',
  },
  warn: {
    accent: 'bg-warn',
    icon: AlertTriangle,
    iconColor: 'text-warn',
    bgColor: 'bg-warn/5',
    borderColor: 'border-warn/20',
  },
  danger: {
    accent: 'bg-danger',
    icon: AlertCircle,
    iconColor: 'text-danger',
    bgColor: 'bg-danger/5',
    borderColor: 'border-danger/20',
  },
};

const getSeverityConfig = (severity: string) => {
  switch (severity) {
    case 'warning':
      return statusConfig.warn;
    case 'error':
      return statusConfig.danger;
    default:
      return statusConfig.ok;
  }
};

export default function InsightBanner({
  title,
  insights,
  status = 'ok',
  className,
  defaultExpanded = false,
}: InsightBannerProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const config = statusConfig[status];
  const StatusIcon = config.icon;

  if (!insights || insights.length === 0) {
    return null;
  }

  return (
    <GlassCard 
      className={clsx(
        "relative overflow-hidden",
        config.bgColor,
        config.borderColor,
        className
      )}
    >
      {/* Accent bar */}
      <div className={clsx("absolute top-0 left-0 w-1 h-full", config.accent)} />
      
      {/* Header */}
      <motion.div
        className="p-6 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
        whileHover={{ backgroundColor: 'rgba(255, 255, 255, 0.02)' }}
        whileTap={{ scale: 0.995 }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Icon */}
            <motion.div
              className={clsx(
                "flex items-center justify-center w-10 h-10 rounded-xl",
                config.bgColor,
                "border",
                config.borderColor
              )}
              whileHover={{ scale: 1.05, rotate: 2 }}
              transition={{ type: "spring", stiffness: 400, damping: 15 }}
            >
              <Brain className={clsx("w-5 h-5", config.iconColor)} />
            </motion.div>

            {/* Title and count */}
            <div>
              <h3 className="font-semibold text-text text-lg">{title}</h3>
              <p className="text-sm text-text-muted">
                {insights.length} insight{insights.length !== 1 ? 's' : ''} found
              </p>
            </div>
          </div>

          {/* Expand/collapse button */}
          <motion.div
            className={clsx(
              "flex items-center justify-center w-8 h-8 rounded-lg",
              "hover:bg-surface-alt transition-colors"
            )}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <motion.div
              animate={{ rotate: isExpanded ? 180 : 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 25 }}
            >
              <ChevronDown className="w-4 h-4 text-text-muted" />
            </motion.div>
          </motion.div>
        </div>

        {/* Preview (when collapsed) */}
        <AnimatePresence>
          {!isExpanded && insights.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="mt-4 overflow-hidden"
            >
              <div className="flex items-center gap-2 text-sm text-text-muted">
                <div className={clsx(
                  "w-2 h-2 rounded-full",
                  getSeverityConfig(insights[0].severity).accent
                )} />
                <span className="truncate">{insights[0].message}</span>
                {insights.length > 1 && (
                  <span className="text-xs bg-surface-alt px-2 py-0.5 rounded-full">
                    +{insights.length - 1} more
                  </span>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Expanded details */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="border-t border-border/50"
          >
            <div className="p-6 pt-4 space-y-4">
              {insights.map((insight, index) => {
                const severityConfig = getSeverityConfig(insight.severity);
                const SeverityIcon = severityConfig.icon;

                return (
                  <motion.div
                    key={insight.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-start gap-3 group"
                  >
                    {/* Severity indicator */}
                    <div className={clsx(
                      "flex items-center justify-center w-6 h-6 rounded-md mt-0.5",
                      severityConfig.bgColor,
                      "border",
                      severityConfig.borderColor,
                      "group-hover:scale-105 transition-transform"
                    )}>
                      <SeverityIcon className={clsx("w-3 h-3", severityConfig.iconColor)} />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-text leading-relaxed">
                        {insight.message}
                      </p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-text-muted">
                        <span className="capitalize font-medium">
                          {insight.type.replace('_', ' ')}
                        </span>
                        <span>•</span>
                        <time>
                          {new Date(insight.timestamp * 1000).toLocaleTimeString()}
                        </time>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </GlassCard>
  );
}
