import React from 'react';
import { motion } from 'framer-motion';
import GlassCard from '../ui/GlassCard';

interface ServiceStatusSkeletonProps {
  className?: string;
}

export default function ServiceStatusSkeleton({ className = '' }: ServiceStatusSkeletonProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className={className}
    >
      <GlassCard className="h-full">
        <div className="p-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-neutral-700 rounded animate-pulse" />
              <div className="h-5 bg-neutral-700 rounded w-24 animate-pulse" />
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-neutral-700 rounded animate-pulse" />
              <div className="h-6 bg-neutral-700 rounded w-16 animate-pulse" />
            </div>
          </div>

          {/* Description */}
          <div className="space-y-2 mb-4">
            <div className="h-4 bg-neutral-700 rounded w-full animate-pulse" />
            <div className="h-4 bg-neutral-700 rounded w-3/4 animate-pulse" />
          </div>

          {/* Stats */}
          <div className="space-y-2 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-neutral-700 rounded animate-pulse" />
                <div className="h-3 bg-neutral-700 rounded w-12 animate-pulse" />
              </div>
              <div className="h-3 bg-neutral-700 rounded w-16 animate-pulse" />
            </div>
            
            <div className="flex items-center justify-between">
              <div className="h-3 bg-neutral-700 rounded w-16 animate-pulse" />
              <div className="h-3 bg-neutral-700 rounded w-20 animate-pulse" />
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end">
            <div className="h-7 bg-neutral-700 rounded w-16 animate-pulse" />
          </div>
        </div>
      </GlassCard>
    </motion.div>
  );
}
