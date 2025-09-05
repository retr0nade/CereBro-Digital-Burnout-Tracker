import React, { useEffect, useState } from "react";
import Dashboard from "./Dashboard";
import RealTimeDashboard from "./RealTimeDashboard";
import ScreenTime from "./ScreenTime";
import Settings from "./Settings";
import ServiceManager from "./ServiceManager";
import DataExport from "./DataExport";
import AppShell from "./layout/AppShell";
import DebugPanel from "./components/DebugPanel";
import { toast } from './services/eventHandlers';
import { useCursorTracking } from './hooks/useCursorTracking';

interface BackendStatusType {
  running: boolean;
  port: number;
  error?: string;
}

declare global {
  interface Window {
    __TAURI__: {
      invoke: (command: string, args?: any) => Promise<any>;
    };
  }
}

export default function App() {
  const [currentView, setCurrentView] = useState<'dashboard' | 'realtime' | 'screentime' | 'settings' | 'services' | 'export'>('dashboard');
  const [backendStatus, setBackendStatus] = useState<BackendStatusType>({
    running: false,
    port: 5005,
    error: undefined
  });

  // Initialize cursor tracking for animated background
  useCursorTracking();

  useEffect(() => {
    // Check backend status on mount
    checkBackendStatus();
    
    // Set up periodic status checks
    const interval = setInterval(checkBackendStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkBackendStatus = async () => {
    try {
      if (window.__TAURI__) {
        const status = await window.__TAURI__.invoke('get_backend_status');
        setBackendStatus(status);
      }
    } catch (error) {
      console.error('Failed to get backend status:', error);
    }
  };

  const startBackend = async () => {
    try {
      if (window.__TAURI__) {
        await window.__TAURI__.invoke('start_backend_command');
        setTimeout(checkBackendStatus, 1000);
        toast.notify('success', 'Backend started');
      }
    } catch (error) {
      console.error('Failed to start backend:', error);
      toast.notify('error', 'Failed to start backend');
    }
  };

  const stopBackend = async () => {
    try {
      if (window.__TAURI__) {
        await window.__TAURI__.invoke('stop_backend_command');
        setTimeout(checkBackendStatus, 1000);
        toast.notify('success', 'Backend stopped');
      }
    } catch (error) {
      console.error('Failed to stop backend:', error);
      toast.notify('error', 'Failed to stop backend');
    }
  };



  const [theme, setTheme] = useState<'dark' | 'light'>(() => 'dark');
  
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

  // Theme toggle handler
  const handleThemeToggle = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  // Toast state
  const [toasts, setToasts] = useState<Array<{id:number; type:string; message:string}>>([]);
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
        {renderCurrentView()}
      </AppShell>

      {/* Toast notifications */}
      <div className="fixed bottom-4 right-4 space-y-2 z-50">
        {toasts.map(t => (
          <div 
            key={t.id} 
            className={`px-4 py-3 rounded-xl shadow-pop text-sm font-medium border backdrop-blur-sm ${
              t.type === 'error' 
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
    </>
  );
}
