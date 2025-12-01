import React from 'react';
import { motion } from 'framer-motion';
import { Github, Play, Square, Activity } from 'lucide-react';
import { clsx } from 'clsx';
import ToggleSwitch from '../ui/ToggleSwitch';
import { ScreenshotModeWrapper } from '../utils/screenshotMode';

interface BackendStatusType {
  running: boolean;
  port: number;
  error?: string;
}

interface TopbarProps {
  backendStatus: BackendStatusType;
  onStartBackend: () => void;
  onStopBackend: () => void;
  theme: 'light' | 'dark';
  onThemeToggle: () => void;
}

export default function Topbar({
  backendStatus,
  onStartBackend,
  onStopBackend,
  theme,
  onThemeToggle
}: TopbarProps) {
  return (
    <motion.header
      className={clsx(
        "sticky top-0 z-40 backdrop-blur-md bg-surface/80",
        "border-b border-border",
        "px-6 py-3"
      )}
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      <div className="flex items-center justify-between max-w-screen-2xl mx-auto">
        {/* Left side - Brand */}
        <div className="flex items-center gap-4">
          <motion.div
            className="flex items-center gap-3"
            whileHover={{ scale: 1.02 }}
            transition={{ type: "spring", stiffness: 400 }}
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand to-brand-hover flex items-center justify-center shadow-glow ring-1 ring-white/10">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                className="w-5 h-5 text-white"
              >
                ⚡
              </motion.div>
            </div>
            <div>
              <h1 className="font-bold text-lg text-text leading-tight tracking-tight">CereBro</h1>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase tracking-wider font-semibold text-text-muted bg-surface-hover px-1.5 py-0.5 rounded">
                  v2.0
                </span>
                <span className="w-1 h-1 rounded-full bg-border"></span>
                <p className="text-xs text-text-muted font-medium">Burnout Tracker</p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Right side - Controls */}
        <div className="flex items-center gap-4">
          {/* Tracker Status Indicator */}
          <ScreenshotModeWrapper hideInScreenshot={true}>
            <div className="flex items-center gap-3 px-4 py-1.5 rounded-full bg-surface-hover border border-border/50">
              <div className="flex items-center gap-2">
                <Activity size={14} className={backendStatus.running ? "text-brand" : "text-text-muted"} />
                <span className="text-xs font-medium text-text-muted uppercase tracking-wide">Tracker Status</span>
              </div>
              <div className="w-px h-3 bg-border"></div>
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  {backendStatus.running && (
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-ok opacity-75"></span>
                  )}
                  <span className={clsx(
                    "relative inline-flex rounded-full h-2 w-2",
                    backendStatus.running ? "bg-ok" : "bg-danger"
                  )}></span>
                </span>
                <span className={clsx(
                  "text-xs font-semibold",
                  backendStatus.running ? "text-ok" : "text-text-muted"
                )}>
                  {backendStatus.running ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          </ScreenshotModeWrapper>

          <div className="w-px h-8 bg-border mx-1"></div>

          {/* Start/Stop Button */}
          <ScreenshotModeWrapper hideInScreenshot={true}>
            <motion.button
              onClick={backendStatus.running ? onStopBackend : onStartBackend}
              className={clsx(
                "flex items-center gap-2 px-5 py-2 rounded-full font-semibold text-sm shadow-sm",
                "transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-focus focus:ring-offset-2 focus:ring-offset-surface",
                backendStatus.running
                  ? "bg-surface border border-danger/30 text-danger hover:bg-danger/5 hover:border-danger/50"
                  : "bg-brand text-white hover:bg-brand-hover hover:shadow-glow-sm border border-transparent"
              )}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {backendStatus.running ? (
                <>
                  <Square className="w-4 h-4 fill-current" />
                  <span>Stop Tracking</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Start Tracking</span>
                </>
              )}
            </motion.button>
          </ScreenshotModeWrapper>

          {/* Theme Toggle */}
          <ScreenshotModeWrapper hideInScreenshot={true}>
            <ToggleSwitch
              checked={theme === 'dark'}
              onChange={onThemeToggle}
            />
          </ScreenshotModeWrapper>

          {/* GitHub Link */}
          <ScreenshotModeWrapper hideInScreenshot={true}>
            <motion.a
              href="https://github.com/retr0nade/CereBro-Mental-Burnout-Tracker"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-text-muted hover:text-text transition-colors"
              whileHover={{ scale: 1.1, rotate: 5 }}
              whileTap={{ scale: 0.9 }}
            >
              <Github className="w-5 h-5" />
            </motion.a>
          </ScreenshotModeWrapper>
        </div>
      </div>
    </motion.header>
  );
}
