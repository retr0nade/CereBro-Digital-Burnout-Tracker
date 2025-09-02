import React from 'react';
import { motion } from 'framer-motion';
import { BarChart3, MousePointer, Clock, Timer } from 'lucide-react';
import GlassCard from '../ui/GlassCard';
import MetricTile from '../ui/MetricTile';

interface LivePreviewProps {
  theme: 'dark' | 'light';
  reduceMotion: boolean;
  idleTimeout: number;
  focusSessionLength: number;
  breakRemindersEnabled: boolean;
  notificationsEnabled: boolean;
}

export default function LivePreview({
  theme,
  reduceMotion,
  idleTimeout,
  focusSessionLength,
  breakRemindersEnabled,
  notificationsEnabled
}: LivePreviewProps) {
  const previewData = {
    focus_score: 78,
    app_switches: 24,
    idle_events: 3,
    total_minutes: 142
  };

  return (
    <GlassCard className="h-full">
      <div className="p-4">
        <h3 className="text-lg font-semibold text-text mb-4">Live Preview</h3>
        <p className="text-sm text-text-muted mb-4">
          See how your settings affect the interface
        </p>

        {/* Theme Preview */}
        <div className="mb-4 p-3 rounded-lg bg-white/5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-text">Theme</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              theme === 'dark' 
                ? 'bg-neutral-600/50 text-neutral-300' 
                : 'bg-neutral-200/50 text-neutral-700'
            }`}>
              {theme === 'dark' ? 'Dark' : 'Light'}
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <span>Motion: {reduceMotion ? 'Reduced' : 'Full'}</span>
            <span>•</span>
            <span>Notifications: {notificationsEnabled ? 'On' : 'Off'}</span>
          </div>
        </div>

        {/* Settings Summary */}
        <div className="space-y-2 mb-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-text-muted">Idle Timeout</span>
            <span className="text-text font-medium">{idleTimeout} min</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-text-muted">Focus Sessions</span>
            <span className="text-text font-medium">{focusSessionLength} min</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-text-muted">Break Reminders</span>
            <span className={`text-xs font-medium ${
              breakRemindersEnabled ? 'text-green-400' : 'text-neutral-500'
            }`}>
              {breakRemindersEnabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
        </div>

        {/* Sample Metrics */}
        <div className="grid grid-cols-2 gap-2">
          <motion.div
            className="p-2 rounded-lg bg-white/5 text-center"
            whileHover={reduceMotion ? {} : { scale: 1.05 }}
            transition={{ duration: 0.2 }}
          >
            <div className="text-lg font-bold text-text">{previewData.focus_score}%</div>
            <div className="text-xs text-text-muted">Focus Score</div>
          </motion.div>
          <motion.div
            className="p-2 rounded-lg bg-white/5 text-center"
            whileHover={reduceMotion ? {} : { scale: 1.05 }}
            transition={{ duration: 0.2 }}
          >
            <div className="text-lg font-bold text-text">{previewData.app_switches}</div>
            <div className="text-xs text-text-muted">App Switches</div>
          </motion.div>
        </div>

        {/* Animation Demo */}
        <div className="mt-4 p-3 rounded-lg bg-white/5">
          <div className="text-xs text-text-muted mb-2">Animation Preview</div>
          <div className="flex items-center gap-2">
            <motion.div
              className="w-3 h-3 rounded-full bg-brand"
              animate={reduceMotion ? {} : { 
                scale: [1, 1.2, 1],
                opacity: [1, 0.7, 1]
              }}
              transition={{ 
                duration: 2, 
                repeat: Infinity,
                ease: "easeInOut"
              }}
            />
            <motion.div
              className="w-3 h-3 rounded-full bg-brand"
              animate={reduceMotion ? {} : { 
                scale: [1, 1.2, 1],
                opacity: [1, 0.7, 1]
              }}
              transition={{ 
                duration: 2, 
                repeat: Infinity,
                delay: 0.5,
                ease: "easeInOut"
              }}
            />
            <motion.div
              className="w-3 h-3 rounded-full bg-brand"
              animate={reduceMotion ? {} : { 
                scale: [1, 1.2, 1],
                opacity: [1, 0.7, 1]
              }}
              transition={{ 
                duration: 2, 
                repeat: Infinity,
                delay: 1,
                ease: "easeInOut"
              }}
            />
            <span className="text-xs text-text-muted ml-2">
              {reduceMotion ? 'Motion reduced' : 'Full animations'}
            </span>
          </div>
        </div>
      </div>
    </GlassCard>
  );
}
