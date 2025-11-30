import React, { useEffect, useState } from 'react';

interface ServiceStatus {
  name: string;
  status: string;
  start_time?: string;
  last_error?: string;
  restart_count: number;
  max_restarts: number;
  uptime?: string;
}

interface ServiceControlProps {
  serviceName: string;
  displayName: string;
  description: string;
}

import { invoke, isTauriAvailable } from './utils/tauri';

const ServiceControl: React.FC<ServiceControlProps> = ({ serviceName, displayName, description }) => {
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      if (isTauriAvailable()) {
        const services = await invoke('get_service_status');
        const serviceStatus = services[serviceName];
        if (serviceStatus) {
          setStatus(serviceStatus);
        }
      }
    } catch (err) {
      console.error('Failed to fetch service status:', err);
    }
  };

  const startService = async () => {
    try {
      setLoading(true);
      setError(null);

      if (isTauriAvailable()) {
        const result = await invoke('start_service', { name: serviceName });
        if (result.success) {
          await fetchStatus();
        } else {
          setError(result.message);
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start service';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const stopService = async () => {
    try {
      setLoading(true);
      setError(null);

      if (isTauriAvailable()) {
        const result = await invoke('stop_service', { name: serviceName });
        if (result.success) {
          await fetchStatus();
        } else {
          setError(result.message);
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to stop service';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [serviceName]);

  const isRunning = status?.status === 'running' || status?.status === 'initialized';
  const isStopped = status?.status === 'stopped' || status?.status === 'not_initialized';

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div
            className={`w-3 h-3 rounded-full ${isRunning
                ? 'bg-green-500 animate-pulse'
                : isStopped
                  ? 'bg-red-500'
                  : 'bg-yellow-500'
              }`}
          />
          <div>
            <h3 className="text-lg font-semibold">{displayName}</h3>
            <p className="text-sm muted">{description}</p>
          </div>
        </div>

        <div className="flex space-x-2">
          {isRunning ? (
            <button
              onClick={stopService}
              disabled={loading}
              className="btn btn-danger"
            >
              {loading ? 'Stopping...' : 'Stop'}
            </button>
          ) : (
            <button
              onClick={startService}
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? 'Starting...' : 'Start'}
            </button>
          )}
        </div>
      </div>

      {status && (
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="muted">Status:</span>
            <span className={`ml-2 font-medium ${isRunning ? 'text-green-400' :
                isStopped ? 'text-red-400' : 'text-yellow-400'
              }`}>
              {status.status}
            </span>
          </div>

          {status.restart_count > 0 && (
            <div>
              <span className="muted">Restarts:</span>
              <span className="ml-2">
                {status.restart_count}/{status.max_restarts}
              </span>
            </div>
          )}

          {status.uptime && (
            <div>
              <span className="muted">Uptime:</span>
              <span className="ml-2">{status.uptime}</span>
            </div>
          )}

          {status.last_error && (
            <div className="col-span-2">
              <span className="muted">Last Error:</span>
              <span className="ml-2 text-red-400 text-xs">{status.last_error}</span>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="mt-3 p-2 border border-red-500/40 rounded text-red-300 text-sm">
          {error}
        </div>
      )}
    </div>
  );
}

export default ServiceControl;
