import React, { useEffect, useState } from "react";
import Dashboard from "./Dashboard";
import RealTimeDashboard from "./RealTimeDashboard";
import ScreenTime from "./ScreenTime";
import Settings from "./Settings";
import ServiceManager from "./ServiceManager";
import DataExport from "./DataExport";
import AppShell from "./layout/AppShell";
import DebugPanel from "./components/DebugPanel";
import ParticleEffect from "./components/ParticleEffect";
import LoadingState from "./ui/LoadingState";
import { toast } from './services/eventHandlers';
import { useCursorTracking } from './hooks/useCursorTracking';

import { invoke, isTauriAvailable } from './utils/tauri';

interface BackendStatusType {
  running: boolean;
  port: number;
  error?: string;
}



export default function App() {
  const [currentView, setCurrentView] = useState<'dashboard' | 'realtime' | 'screentime' | 'settings' | 'services' | 'export'>('dashboard');
  const [backendStatus, setBackendStatus] = useState<BackendStatusType>({
    running: false,
    port: 5005,
    error: undefined
  });

  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);

  // Initialize cursor tracking for animated background
  useCursorTracking();

  // Initialize screenshot mode


  useEffect(() => {
    // Check backend status on mount
    checkBackendStatus();

    // Set up periodic status checks
    const interval = setInterval(checkBackendStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkBackendStatus = async () => {
    try {
      if (isTauriAvailable()) {
        const status = await invoke('get_backend_status');
        setBackendStatus(status);
      } else {
        // Fallback for browser mode: Check via HTTP
        try {
          const response = await fetch('http://localhost:5005/api/status');
          if (response.ok) {
            const data = await response.json();
            // Map the API response to BackendStatusType
            // The API returns { status: "success", services: { ... } }
            // We check if any service is running to determine overall "running" status
            const services = data.services;
            const isRunning = Object.values(services).some((s: any) => s.status === 'running');

            setBackendStatus({
              running: isRunning,
              port: 5005,
              error: undefined
            });
          } else {
            setBackendStatus(prev => ({ ...prev, running: false }));
          }
        } catch (e) {
          // Backend likely not running or not accessible
          setBackendStatus(prev => ({ ...prev, running: false }));
        }
      }
    } catch (error) {
      console.error('Failed to check backend status:', error);
      setBackendStatus(prev => ({ ...prev, running: false }));
    }
  };

  const startBackend = async () => {
    try {
      setIsStarting(true);

      if (isTauriAvailable()) {
        await invoke('start_backend_command');
      } else {
        // Fallback for browser: Simulate start
        console.log("Browser mode: Simulating backend start...");
      }

      // Artificial delay to show loading state and allow backend to init
      await new Promise(resolve => setTimeout(resolve, 3000));

      // Update status
      if (isTauriAvailable()) {
        await checkBackendStatus();
      } else {
        // In browser, we assume it started for UI testing purposes
        // or the periodic check will pick it up if it's actually running locally
        setBackendStatus(prev => ({ ...prev, running: true, error: undefined }));
      }

      setIsStarting(false);
      toast.notify('success', 'Backend started');
    } catch (error) {
      console.error('Failed to start backend:', error);
      setIsStarting(false);
      toast.notify('error', `Failed to start backend: ${error}`);
    }
  };

  const stopBackend = async () => {
    try {
      setIsStopping(true);

      if (isTauriAvailable()) {
        await invoke('stop_backend_command');
      } else {
        // Fallback for browser: Simulate stop delay
        console.log("Browser mode: Simulating backend stop...");
      }

      // Artificial delay to show stopping animation and ensure process cleanup
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Force update status to stopped
      setBackendStatus(prev => ({ ...prev, running: false, error: undefined }));

      // Skip immediate checkBackendStatus() to avoid race conditions where 
      // the backend might still be shutting down and report "running".
      // The periodic interval will eventually verify the status.

      setIsStopping(false);
      toast.notify('success', 'Backend stopped');
    } catch (error) {
      console.error('Failed to stop backend:', error);
      setIsStopping(false);
      toast.notify('error', 'Failed to stop backend');
    }
  };



  const [theme, setTheme] = useState<'dark' | 'light'>(() => 'dark');
  const [particleTrigger, setParticleTrigger] = useState(false);

  // Theme effect
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'light') {
      root.classList.add('theme-light');
      root.classList.remove('dark');
    } else {
      root.classList.remove('theme-light');
      root.classList.add('dark');
    }
  }, [theme]);

  // Theme toggle handler with particle effect
  const handleThemeToggle = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
    setParticleTrigger(true);
  };

  // Toast state
  const [toasts, setToasts] = useState<Array<{ id: number; type: string; message: string }>>([]);
  useEffect(() => toast.subscribe(setToasts), []);

  // Render current view content
  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'realtime':
        return <RealTimeDashboard />;
      case 'screentime':
        return <ScreenTime />;
      case 'settings':
        return <Settings />;
      case 'services':
        return <ServiceManager />;
      case 'export':
        return <DataExport />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <>
      <AppShell
        currentView={currentView}
        onViewChange={setCurrentView}
        backendStatus={backendStatus}
        onStartBackend={startBackend}
        onStopBackend={stopBackend}
        theme={theme}
        onThemeToggle={handleThemeToggle}
      >
        {isStarting ? (
          <LoadingState
            autoAdvance={true}
            duration={600}
            onComplete={() => { }}
          />
        ) : isStopping ? (
          <LoadingState
            autoAdvance={true}
            duration={500}
            steps={[
              "Stopping background services...",
              "Saving session data...",
              "Disconnecting...",
              "Done"
            ]}
            onComplete={() => { }}
          />
        ) : (
          renderCurrentView()
        )}
      </AppShell>
      {/* Toast notifications */}
      {/* Toast notifications */}
      <div className="fixed bottom-4 right-4 space-y-2 z-50 toast-notifications">
        {toasts.map(t => (
          <div
            key={t.id}
            className={`px-4 py-3 rounded-xl shadow-pop text-sm font-medium border backdrop-blur-sm ${t.type === 'error'
              ? 'bg-danger/90 border-danger text-white'
              : t.type === 'success'
                ? 'bg-ok/90 border-ok text-white'
                : 'bg-surface/90 border-border text-text'
              }`}
          >
            {t.message}
          </div>
        ))}
      </div>

      {/* Debug Panel - Development Only */}
      <DebugPanel />

      {/* Particle Effect for Theme Switch */}
      <ParticleEffect
        trigger={particleTrigger}
        onComplete={() => setParticleTrigger(false)}
      />
    </>
  );
}
