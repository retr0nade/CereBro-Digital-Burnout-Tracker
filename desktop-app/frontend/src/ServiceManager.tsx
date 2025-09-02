import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Monitor, 
  Clock, 
  MousePointer, 
  BarChart3, 
  Timer, 
  Coffee,
  RefreshCw
} from 'lucide-react';
import ServiceStatusCard from './components/ServiceStatusCard';
import ServiceStatusSkeleton from './components/ServiceStatusSkeleton';
import SectionHeader from './ui/SectionHeader';
import GlassCard from './ui/GlassCard';
import { toast } from './services/eventHandlers';

interface ServiceStatus {
  name: string;
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping';
  uptime?: number; // seconds
  last_crash?: string; // ISO timestamp
  description: string;
  icon?: React.ReactNode;
}

declare global {
  interface Window {
    __TAURI__: {
      invoke: (command: string, args?: any) => Promise<any>;
    };
  }
}

export default function ServiceManager() {
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const serviceDefinitions = [
    {
      name: 'window_tracker',
      displayName: 'Window Tracker',
      description: 'Monitors which applications you\'re using and tracks window usage patterns for productivity analysis.',
      icon: <Monitor className="w-5 h-5" />
    },
    {
      name: 'idle_monitor',
      displayName: 'Idle Monitor',
      description: 'Detects when you\'re away from your computer and logs idle periods for work-life balance insights.',
      icon: <Clock className="w-5 h-5" />
    },
    {
      name: 'input_logger',
      displayName: 'Input Logger',
      description: 'Tracks your keyboard keypresses and mouse clicks to analyze activity patterns and productivity.',
      icon: <MousePointer className="w-5 h-5" />
    },
    {
      name: 'screen_time_tracker',
      displayName: 'Screen Time Tracker',
      description: 'Calculates your total daily screen time and provides insights into digital wellness patterns.',
      icon: <BarChart3 className="w-5 h-5" />
    },
    {
      name: 'focus_timer',
      displayName: 'Focus Timer',
      description: 'Manages and logs focus sessions to help you maintain productivity and track deep work periods.',
      icon: <Timer className="w-5 h-5" />
    },
    {
      name: 'break_monitor',
      displayName: 'Break Monitor',
      description: 'Monitors for user inactivity breaks and system lock/unlock events for comprehensive activity tracking.',
      icon: <Coffee className="w-5 h-5" />
    }
  ];

  const fetchServiceStatus = async () => {
    try {
      setLoading(true);
      setError(null);

      if (window.__TAURI__) {
        const result = await window.__TAURI__.invoke('get_service_status');
        
        const serviceStatuses: ServiceStatus[] = serviceDefinitions.map(service => {
          const status = result[service.name] || {};
          return {
            name: service.displayName,
            status: status.status || 'stopped',
            uptime: status.uptime_seconds,
            last_crash: status.last_error_timestamp,
            description: service.description,
            icon: service.icon
          };
        });

        setServices(serviceStatuses);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch service status';
      setError(errorMessage);
      console.error('Service status fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRestartService = async (serviceName: string) => {
    try {
      // Find the service key from display name
      const serviceKey = serviceDefinitions.find(s => s.displayName === serviceName)?.name;
      if (!serviceKey) return;

      if (window.__TAURI__) {
        await window.__TAURI__.invoke('restart_service', { name: serviceKey });
        toast.notify('success', `${serviceName} restart initiated`);
        
        // Refresh status after a short delay
        setTimeout(fetchServiceStatus, 2000);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to restart service';
      toast.notify('error', errorMessage);
      console.error('Service restart error:', err);
    }
  };

  useEffect(() => {
    fetchServiceStatus();
    const interval = setInterval(fetchServiceStatus, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-7xl mx-auto mt-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Service Manager</h1>
          <p className="text-text-muted mt-1">
            Monitor and control individual tracking services
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={fetchServiceStatus}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-brand/20 text-brand hover:bg-brand/30 border border-brand/40 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span className="text-sm font-medium">Refresh</span>
        </motion.button>
      </div>

      {/* Error State */}
      {error && (
        <GlassCard className="mb-6 border border-red-500/40">
          <div className="p-4">
            <h3 className="text-lg font-semibold text-red-400 mb-2">Connection Error</h3>
            <p className="text-red-300 text-sm">{error}</p>
            <button 
              onClick={fetchServiceStatus}
              className="mt-3 px-3 py-1.5 rounded-lg bg-red-500/20 text-red-300 hover:bg-red-500/30 border border-red-500/40 text-sm"
            >
              Retry
            </button>
          </div>
        </GlassCard>
      )}

      {/* Service Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        <AnimatePresence mode="wait">
          {loading ? (
            // Skeleton loaders
            Array.from({ length: 6 }).map((_, index) => (
              <motion.div
                key={`skeleton-${index}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <ServiceStatusSkeleton />
              </motion.div>
            ))
          ) : (
            // Actual service cards
            services.map((service, index) => (
              <motion.div
                key={service.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <ServiceStatusCard
                  service={service}
                  onRestart={handleRestartService}
                />
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      {/* Information Section */}
      <div className="mt-8">
        <GlassCard>
          <SectionHeader
            title="Service Information"
            subtitle="Understanding what each service tracks"
            tooltip="Detailed information about each tracking service and its purpose"
            className="mb-4"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {serviceDefinitions.map((service) => (
              <div key={service.name} className="flex items-start gap-3 p-3 rounded-lg bg-white/5">
                <div className="w-5 h-5 text-brand mt-0.5 flex-shrink-0">
                  {service.icon}
                </div>
                <div>
                  <h4 className="font-medium text-text mb-1">{service.displayName}</h4>
                  <p className="text-text-muted leading-relaxed">{service.description}</p>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
