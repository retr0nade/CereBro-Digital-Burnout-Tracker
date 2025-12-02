import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bug, X, RefreshCw, Activity, Terminal, AlertTriangle } from 'lucide-react';
import { performanceMonitor, RenderStats } from '../utils/performance';
import { listen } from '../utils/tauri';

interface DebugPanelProps {
  className?: string;
}

interface LogEntry {
  id: string;
  timestamp: number;
  message: string;
  type: 'stdout' | 'stderr' | 'error';
}

export default function DebugPanel({ className = '' }: DebugPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [stats, setStats] = useState<RenderStats[]>([]);
  const [isVisible, setIsVisible] = useState(false);
  const [activeTab, setActiveTab] = useState<'perf' | 'logs'>('logs');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Only show in development
  useEffect(() => {
    setIsVisible(process.env.NODE_ENV === 'development');
  }, []);

  // Performance stats update
  useEffect(() => {
    if (!isOpen || activeTab !== 'perf') return;

    const updateStats = () => {
      setStats(performanceMonitor.getStats());
    };

    updateStats();
    const interval = setInterval(updateStats, 1000);

    return () => clearInterval(interval);
  }, [isOpen, activeTab]);

  // Listen for backend logs
  useEffect(() => {
    const unlistenLog = listen('backend-log', (event: any) => {
      const message = event.payload as string;
      const type = message.startsWith('STDERR:') ? 'stderr' : 'stdout';
      addLog(message.replace(/^(STDOUT:|STDERR:)\s*/, ''), type);
    });

    const unlistenError = listen('backend-error', (event: any) => {
      addLog(event.payload as string, 'error');
    });

    return () => {
      unlistenLog.then(f => f());
      unlistenError.then(f => f());
    };
  }, []);

  const addLog = (message: string, type: 'stdout' | 'stderr' | 'error') => {
    setLogs(prev => {
      const newLogs = [...prev, {
        id: Math.random().toString(36).substr(2, 9),
        timestamp: Date.now(),
        message,
        type
      }];
      return newLogs.slice(-100); // Keep last 100 logs
    });
  };

  // Auto-scroll logs
  useEffect(() => {
    if (isOpen && activeTab === 'logs' && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isOpen, activeTab]);

  const resetStats = () => {
    performanceMonitor.reset();
    setStats([]);
  };

  const clearLogs = () => {
    setLogs([]);
  };

  if (!isVisible) return null;

  return (
    <>
      {/* Floating Debug Button */}
      <motion.button
        className="fixed bottom-4 right-4 z-50 bg-red-600 hover:bg-red-700 text-white p-3 rounded-full shadow-lg transition-colors"
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 2 }}
      >
        <Bug className="w-5 h-5" />
      </motion.button>

      {/* Debug Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed bottom-20 right-4 z-50 bg-surface border border-border rounded-lg shadow-xl max-w-md w-full flex flex-col max-h-[500px]"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-3 border-b border-border bg-surface-alt rounded-t-lg">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setActiveTab('logs')}
                  className={`flex items-center gap-2 text-sm font-medium transition-colors ${activeTab === 'logs' ? 'text-brand' : 'text-text-muted hover:text-text'
                    }`}
                >
                  <Terminal className="w-4 h-4" />
                  Backend Logs
                </button>
                <button
                  onClick={() => setActiveTab('perf')}
                  className={`flex items-center gap-2 text-sm font-medium transition-colors ${activeTab === 'perf' ? 'text-brand' : 'text-text-muted hover:text-text'
                    }`}
                >
                  <Activity className="w-4 h-4" />
                  Performance
                </button>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={activeTab === 'perf' ? resetStats : clearLogs}
                  className="p-1 hover:bg-surface rounded transition-colors"
                  title={activeTab === 'perf' ? "Reset Stats" : "Clear Logs"}
                >
                  <RefreshCw className="w-3 h-3 text-text-muted" />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-surface rounded transition-colors"
                  title="Close"
                >
                  <X className="w-3 h-3 text-text-muted" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 bg-surface min-h-[300px]">
              {activeTab === 'perf' ? (
                // Performance Stats
                stats.length === 0 ? (
                  <div className="text-center py-8">
                    <Activity className="w-8 h-8 text-text-muted mx-auto mb-2 opacity-50" />
                    <p className="text-sm text-text-muted">No render data yet</p>
                    <p className="text-xs text-text-muted mt-1">
                      Interact with charts to see render counts
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {stats.map((stat, index) => (
                      <motion.div
                        key={stat.componentName}
                        className="bg-surface-alt rounded-lg p-3"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-text">
                            {stat.componentName}
                          </span>
                          <span className="text-xs text-text-muted">
                            #{index + 1}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <span className="text-text-muted">Renders:</span>
                            <span className="ml-1 font-medium text-text">
                              {stat.renderCount}
                            </span>
                          </div>
                          <div>
                            <span className="text-text-muted">Last:</span>
                            <span className="ml-1 font-medium text-text">
                              {stat.lastRenderTime.toFixed(1)}ms
                            </span>
                          </div>
                          <div className="col-span-2">
                            <span className="text-text-muted">Avg:</span>
                            <span className="ml-1 font-medium text-text">
                              {stat.averageRenderTime.toFixed(1)}ms
                            </span>
                          </div>
                        </div>

                        {/* Performance indicator */}
                        <div className="mt-2">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-1 bg-surface rounded-full overflow-hidden">
                              <div
                                className={`h-full transition-all duration-300 ${stat.averageRenderTime < 5
                                  ? 'bg-green-500'
                                  : stat.averageRenderTime < 10
                                    ? 'bg-yellow-500'
                                    : 'bg-red-500'
                                  }`}
                                style={{
                                  width: `${Math.min(100, (stat.averageRenderTime / 20) * 100)}%`
                                }}
                              />
                            </div>
                            <span className="text-xs text-text-muted">
                              {stat.averageRenderTime < 5 ? 'Fast' :
                                stat.averageRenderTime < 10 ? 'OK' : 'Slow'}
                            </span>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )
              ) : (
                // Backend Logs
                <div className="space-y-1 font-mono text-xs">
                  {logs.length === 0 ? (
                    <div className="text-center py-8">
                      <Terminal className="w-8 h-8 text-text-muted mx-auto mb-2 opacity-50" />
                      <p className="text-sm text-text-muted">No logs yet</p>
                      <p className="text-xs text-text-muted mt-1">
                        Start the backend to see output
                      </p>
                    </div>
                  ) : (
                    logs.map((log) => (
                      <div key={log.id} className={`break-all ${log.type === 'error' ? 'text-red-500 bg-red-500/10 p-1 rounded' :
                        log.type === 'stderr' ? 'text-yellow-500' :
                          'text-text-muted'
                        }`}>
                        <span className="opacity-50 mr-2">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                        {log.message}
                      </div>
                    ))
                  )}
                  <div ref={logsEndRef} />
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-2 border-t border-border bg-surface-alt rounded-b-lg">
              <div className="text-xs text-text-muted text-center flex justify-between px-2">
                <span>{activeTab === 'perf' ? `${stats.length} components` : `${logs.length} lines`}</span>
                <span>Dev Mode</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
