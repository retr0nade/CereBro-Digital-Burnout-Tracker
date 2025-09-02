import React from 'react';
import { motion } from 'framer-motion';
import { Clock, RefreshCw, AlertCircle, CheckCircle, XCircle, Info } from 'lucide-react';
import GlassCard from '../ui/GlassCard';

interface ServiceStatus {
  name: string;
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping';
  uptime?: number; // seconds
  last_crash?: string; // ISO timestamp
  description: string;
  icon?: React.ReactNode;
}

interface ServiceStatusCardProps {
  service: ServiceStatus;
  onRestart?: (serviceName: string) => void;
  className?: string;
}

// Helper function to get status tone
const getStatusTone = (status: ServiceStatus['status']): 'ok' | 'warn' | 'danger' => {
  switch (status) {
    case 'running':
      return 'ok';
    case 'starting':
    case 'stopping':
      return 'warn';
    case 'stopped':
    case 'error':
      return 'danger';
    default:
      return 'warn';
  }
};

// Helper function to get status icon
const getStatusIcon = (status: ServiceStatus['status']) => {
  switch (status) {
    case 'running':
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    case 'starting':
    case 'stopping':
      return <RefreshCw className="w-4 h-4 text-yellow-400 animate-spin" />;
    case 'stopped':
    case 'error':
      return <XCircle className="w-4 h-4 text-red-400" />;
    default:
      return <AlertCircle className="w-4 h-4 text-yellow-400" />;
  }
};

// Helper function to format uptime
const formatUptime = (seconds?: number): string => {
  if (!seconds) return 'Unknown';
  
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

// Helper function to format last crash time
const formatLastCrash = (timestamp?: string): string => {
  if (!timestamp) return 'Never';
  
  const crashTime = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - crashTime.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  return crashTime.toLocaleDateString();
};

export default function ServiceStatusCard({ 
  service, 
  onRestart, 
  className = '' 
}: ServiceStatusCardProps) {
  const tone = getStatusTone(service.status);
  const statusIcon = getStatusIcon(service.status);
  
  const handleRestart = () => {
    if (onRestart && service.status !== 'starting' && service.status !== 'stopping') {
      onRestart(service.name);
    }
  };

  return (
    <motion.div
      whileHover={{ 
        scale: 1.02,
        transition: { duration: 0.2 }
      }}
      whileTap={{ 
        scale: 0.98,
        transition: { duration: 0.1 }
      }}
      className={className}
    >
      <GlassCard className="h-full">
        <div className="p-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              {service.icon && (
                <div className="w-6 h-6 text-text-muted">
                  {service.icon}
                </div>
              )}
              <div className="flex items-center gap-1">
                <h3 className="text-lg font-semibold text-text truncate">
                  {service.name}
                </h3>
                <div className="group relative">
                  <Info className="w-4 h-4 text-text-muted cursor-help" />
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-surface/95 border border-border rounded-lg shadow-lg text-xs text-text-muted max-w-xs opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
                    {service.description}
                    <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-surface/95"></div>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {statusIcon}
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                tone === 'ok' ? 'bg-green-500/20 text-green-300 border border-green-500/40' :
                tone === 'warn' ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/40' :
                'bg-red-500/20 text-red-300 border border-red-500/40'
              }`}>
                {service.status}
              </span>
            </div>
          </div>

          {/* Description */}
          <p className="text-sm text-text-muted mb-4 line-clamp-2">
            {service.description}
          </p>

          {/* Stats */}
          <div className="space-y-2 mb-4">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-1 text-text-muted">
                <Clock className="w-3 h-3" />
                <span>Uptime</span>
              </div>
              <span className="text-text font-medium">
                {formatUptime(service.uptime)}
              </span>
            </div>
            
            <div className="flex items-center justify-between text-sm">
              <span className="text-text-muted">Last Crash</span>
              <span className="text-text font-medium">
                {formatLastCrash(service.last_crash)}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleRestart}
              disabled={service.status === 'starting' || service.status === 'stopping'}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                service.status === 'starting' || service.status === 'stopping'
                  ? 'bg-neutral-600/50 text-neutral-400 cursor-not-allowed'
                  : 'bg-brand/20 text-brand hover:bg-brand/30 border border-brand/40'
              }`}
            >
              {service.status === 'starting' || service.status === 'stopping' 
                ? 'Processing...' 
                : 'Restart'
              }
            </motion.button>
          </div>
        </div>
      </GlassCard>
    </motion.div>
  );
}
