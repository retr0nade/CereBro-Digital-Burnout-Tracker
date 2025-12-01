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
import { useScreenshotMode, ScreenshotModeWrapper } from './utils/screenshotMode';
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
  const screenshotMode = useScreenshotMode();

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
      }
    } catch (error) {
      console.error('Failed to check backend status:', error);
    }
  };

  const startBackend = async () => {
    try {
      if (isTauriAvailable()) {
        setIsStarting(true);
        await invoke('start_backend_command');

        // Artificial delay to show loading state and allow backend to init
        await new Promise(resolve => setTimeout(resolve, 3000));

        await checkBackendStatus();
        setIsStarting(false);
        toast.notify('success', 'Backend started');
      }
    } catch (error) {
      console.error('Failed to start backend:', error);
      setIsStarting(false);
      toast.notify('error', `Failed to start backend: ${error}`);
    }
  };

  const stopBackend = async () => {
    try {
      if (isTauriAvailable()) {
        setIsStopping(true);
        await invoke('stop_backend_command');

        // Artificial delay to show stopping animation
        await new Promise(resolve => setTimeout(resolve, 2000));

        await checkBackendStatus();
        setIsStopping(false);
        toast.notify('success', 'Backend stopped');
      }
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
      <ScreenshotModeWrapper hideInScreenshot={screenshotMode.hideToastNotifications}>
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
      </ScreenshotModeWrapper>

      {/* Debug Panel - Development Only */}
      <ScreenshotModeWrapper hideInScreenshot={screenshotMode.hideDebugPanel}>
        <DebugPanel />
      </ScreenshotModeWrapper>

      {/* Particle Effect for Theme Switch */}
      <ScreenshotModeWrapper hideInScreenshot={screenshotMode.hideFloatingElements}>
        <ParticleEffect
          trigger={particleTrigger}
          onComplete={() => setParticleTrigger(false)}
        />
      </ScreenshotModeWrapper>
    </>
  );
}
