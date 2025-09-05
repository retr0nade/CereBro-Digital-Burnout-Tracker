import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bug, X, RefreshCw, Activity } from 'lucide-react';
import { performanceMonitor, RenderStats } from '../utils/performance';

interface DebugPanelProps {
  className?: string;
}

export default function DebugPanel({ className = '' }: DebugPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [stats, setStats] = useState<RenderStats[]>([]);
  const [isVisible, setIsVisible] = useState(false);

  // Only show in development
  useEffect(() => {
    setIsVisible(process.env.NODE_ENV === 'development');
  }, []);

  useEffect(() => {
    if (!isOpen) return;

    const updateStats = () => {
      setStats(performanceMonitor.getStats());
    };

    updateStats();
    const interval = setInterval(updateStats, 1000);

    return () => clearInterval(interval);
  }, [isOpen]);

  const resetStats = () => {
    performanceMonitor.reset();
    setStats([]);
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
            className="fixed bottom-20 right-4 z-50 bg-surface border border-border rounded-lg shadow-xl max-w-sm w-full"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-border">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-text-muted" />
                <h3 className="text-sm font-medium text-text">Performance Debug</h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={resetStats}
                  className="p-1 hover:bg-surface-alt rounded transition-colors"
                  title="Reset Stats"
                >
                  <RefreshCw className="w-3 h-3 text-text-muted" />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-surface-alt rounded transition-colors"
                  title="Close"
                >
                  <X className="w-3 h-3 text-text-muted" />
                </button>
              </div>
            </div>

            {/* Stats Content */}
            <div className="p-4 max-h-96 overflow-y-auto">
              {stats.length === 0 ? (
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
                              className={`h-full transition-all duration-300 ${
                                stat.averageRenderTime < 5
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
              )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-border bg-surface-alt">
              <div className="text-xs text-text-muted text-center">
                <p>Development mode only</p>
                <p className="mt-1">
                  Total components: {stats.length} | 
                  Total renders: {stats.reduce((sum, s) => sum + s.renderCount, 0)}
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
