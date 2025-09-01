import React from 'react';
import { motion } from 'framer-motion';
import { Github, Sun, Moon, Play, Square } from 'lucide-react';
import { clsx } from 'clsx';

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
        "sticky top-0 z-40 backdrop-blur-sm bg-surface/80",
        "border-b border-gradient-to-r from-border via-border-hover to-border",
        "px-6 py-4"
      )}
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      {/* Gradient hairline border */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border-hover to-transparent" />
      
      <div className="flex items-center justify-between max-w-screen-2xl mx-auto">
        {/* Left side - Brand */}
        <div className="flex items-center gap-3">
          <motion.div
            className="flex items-center gap-2"
            whileHover={{ scale: 1.02 }}
            transition={{ type: "spring", stiffness: 400 }}
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand to-brand-hover flex items-center justify-center shadow-glow">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                className="w-4 h-4 text-white"
              >
                ⚡
              </motion.div>
            </div>
            <div className="hidden sm:block">
              <h1 className="font-semibold text-text">CereBro</h1>
              <p className="text-dashboard-sm text-text-muted -mt-0.5">Mental Burnout Tracker</p>
            </div>
          </motion.div>
        </div>

        {/* Right side - Controls */}
        <div className="flex items-center gap-3">
          {/* Connection Status Chip */}
          <motion.div
            className={clsx(
              "flex items-center gap-2 px-3 py-1.5 rounded-full text-dashboard-sm font-medium",
              "border transition-all duration-200",
              backendStatus.running
                ? "bg-ok-muted/20 border-ok/30 text-ok"
                : "bg-danger-muted/20 border-danger/30 text-danger"
            )}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <motion.div
              className={clsx(
                "w-2 h-2 rounded-full",
                backendStatus.running ? "bg-ok" : "bg-danger"
              )}
              animate={{
                scale: backendStatus.running ? [1, 1.2, 1] : 1,
                opacity: backendStatus.running ? [1, 0.7, 1] : 0.8
              }}
              transition={{
                duration: 2,
                repeat: backendStatus.running ? Infinity : 0,
                ease: "easeInOut"
              }}
            />
            <span className="hidden sm:inline">
              {backendStatus.running ? 'Connected' : 'Disconnected'}
            </span>
          </motion.div>

          {/* Start/Stop Button */}
          <motion.button
            onClick={backendStatus.running ? onStopBackend : onStartBackend}
            className={clsx(
              "flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm",
              "transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-focus",
              "shadow-soft hover:shadow-lift",
              backendStatus.running
                ? "bg-danger hover:bg-red-600 text-white"
                : "bg-brand hover:bg-brand-hover text-white"
            )}
            whileHover={{ scale: 1.02, y: -1 }}
            whileTap={{ scale: 0.98 }}
          >
            {backendStatus.running ? (
              <>
                <Square className="w-4 h-4" />
                <span className="hidden sm:inline">Stop</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span className="hidden sm:inline">Start</span>
              </>
            )}
          </motion.button>

          {/* Theme Toggle */}
          <motion.button
            onClick={onThemeToggle}
            className={clsx(
              "p-2.5 rounded-lg transition-all duration-200",
              "hover:bg-surface-alt focus:outline-none focus:ring-2 focus:ring-focus",
              "border border-border hover:border-border-hover"
            )}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
          >
            <motion.div
              initial={false}
              animate={{ rotate: theme === 'dark' ? 0 : 180 }}
              transition={{ type: "spring", stiffness: 200, damping: 10 }}
            >
              {theme === 'dark' ? (
                <Sun className="w-4 h-4 text-text-muted" />
              ) : (
                <Moon className="w-4 h-4 text-text-muted" />
              )}
            </motion.div>
          </motion.button>

          {/* GitHub Link */}
          <motion.a
            href="https://github.com/retr0nade/CereBro-Mental-Burnout-Tracker"
            target="_blank"
            rel="noopener noreferrer"
            className={clsx(
              "flex items-center gap-2 px-3 py-2 rounded-lg",
              "text-text-muted hover:text-text transition-all duration-200",
              "hover:bg-surface-alt focus:outline-none focus:ring-2 focus:ring-focus",
              "border border-border hover:border-border-hover"
            )}
            whileHover={{ scale: 1.02, y: -1 }}
            whileTap={{ scale: 0.98 }}
          >
            <Github className="w-4 h-4" />
            <span className="hidden lg:inline text-dashboard-sm font-medium uppercase tracking-wider">
              GitHub
            </span>
          </motion.a>
        </div>
      </div>
    </motion.header>
  );
}
