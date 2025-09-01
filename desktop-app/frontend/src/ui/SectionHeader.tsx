import React from 'react';
import { motion } from 'framer-motion';
import { Info } from 'lucide-react';
import { clsx } from 'clsx';
import * as Tooltip from '@radix-ui/react-tooltip';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  tooltip?: string;
  actions?: React.ReactNode;
  className?: string;
}

export default function SectionHeader({
  title,
  subtitle,
  tooltip,
  actions,
  className,
}: SectionHeaderProps) {
  return (
    <motion.div
      className={clsx(
        "flex items-start justify-between gap-4 mb-6",
        className
      )}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      {/* Title section */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h2 className="text-xl font-semibold text-text leading-tight">
            {title}
          </h2>
          
          {/* Tooltip trigger */}
          {tooltip && (
            <Tooltip.Provider delayDuration={300}>
              <Tooltip.Root>
                <Tooltip.Trigger asChild>
                  <motion.button
                    className={clsx(
                      "inline-flex items-center justify-center w-5 h-5",
                      "rounded-full bg-surface-alt border border-border",
                      "text-text-muted hover:text-text transition-colors",
                      "focus:outline-none focus:ring-2 focus:ring-focus focus:ring-offset-1"
                    )}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    aria-label={`Information about ${title}`}
                  >
                    <Info className="w-3 h-3" />
                  </motion.button>
                </Tooltip.Trigger>
                
                <Tooltip.Portal>
                  <Tooltip.Content
                    className={clsx(
                      "z-50 px-3 py-2 text-sm font-medium text-text",
                      "bg-surface border border-border rounded-lg shadow-pop",
                      "max-w-xs break-words leading-relaxed",
                      "animate-in fade-in-0 zoom-in-95"
                    )}
                    sideOffset={5}
                    side="top"
                  >
                    {tooltip}
                    <Tooltip.Arrow className="fill-surface border-border" />
                  </Tooltip.Content>
                </Tooltip.Portal>
              </Tooltip.Root>
            </Tooltip.Provider>
          )}
        </div>
        
        {/* Subtitle */}
        {subtitle && (
          <motion.p
            className="text-sm text-text-muted leading-relaxed"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            {subtitle}
          </motion.p>
        )}
      </div>

      {/* Actions slot */}
      {actions && (
        <motion.div
          className="flex items-center gap-2 flex-shrink-0"
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          {actions}
        </motion.div>
      )}
    </motion.div>
  );
}
