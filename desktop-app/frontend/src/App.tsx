import React, { useEffect, useState } from "react";
import Dashboard from "./Dashboard";
import RealTimeDashboard from "./RealTimeDashboard";
import ScreenTime from "./ScreenTime";
import Settings from "./Settings";
import ServiceManager from "./ServiceManager";
import DataExport from "./DataExport";
import BackendStatus from "./BackendStatus";
import { useEffect as useReactEffect, useState as useReactState } from 'react';
import { toast } from './services/eventHandlers';

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

  const navItem = (key: typeof currentView, label: string) => (
    <button
      onClick={() => setCurrentView(key)}
      className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
        currentView === key
          ? 'bg-brand-600/20 text-white border border-brand-600/40'
          : 'text-neutral-300 hover:text-white hover:bg-white/5'
      }`}
    >
      {label}
    </button>
  );

  const [theme, setTheme] = useState<'dark' | 'light'>(() => 'dark');
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') root.classList.add('dark'); else root.classList.remove('dark');
  }, [theme]);

  const [toasts, setToasts] = useState<Array<{id:number; type:string; message:string}>>([]);
  useEffect(() => toast.subscribe(setToasts), []);

  return (
    <div className="app-shell selection:bg-brand-400/30">
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="hidden md:flex md:w-64 flex-col gap-2 p-4 glass">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-xl font-bold text-brand-400">CereBro</h1>
            <button
              className="btn btn-secondary px-2 py-1 text-xs"
              onClick={() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))}
              title="Toggle theme"
            >
              {theme === 'dark' ? 'Light' : 'Dark'}
            </button>
          </div>
          <nav className="space-y-1">
            {navItem('dashboard', 'Dashboard')}
            {navItem('realtime', 'Real-time')}
            {navItem('screentime', 'Screen Time')}
            {navItem('services', 'Services')}
            {navItem('settings', 'Settings')}
            {navItem('export', 'Export')}
          </nav>
          <div className="mt-auto text-[10px] text-neutral-400">
            v{new Date().getFullYear()}
          </div>
        </aside>

        {/* Main area */}
        <div className="flex-1 flex flex-col">
          {/* Top bar */}
          <header className="glass px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="md:hidden font-semibold text-brand-400">CereBro</span>
              <div className="hidden md:block text-sm muted">Mental Burnout Tracker</div>
            </div>
            <div className="flex items-center gap-3">
              <BackendStatus status={backendStatus} onStart={startBackend} onStop={stopBackend} />
              <a className="text-xs uppercase tracking-widest text-white/70 hover:underline" target="_blank" rel="noopener noreferrer" href="https://github.com/retr0nade/CereBro-Mental-Burnout-Tracker">GitHub</a>
            </div>
          </header>

          {/* Content */}
          <main className="p-4">
            {currentView === 'dashboard' && <Dashboard />}
            {currentView === 'realtime' && <RealTimeDashboard />}
            {currentView === 'screentime' && <ScreenTime />}
            {currentView === 'settings' && <Settings />}
            {currentView === 'services' && <ServiceManager />}
            {currentView === 'export' && <DataExport />}
          </main>

          <footer className="px-4 py-3 text-center text-xs text-white/40">
            © {new Date().getFullYear()} retr0nade — CereBro Mental Burnout Tracker
          </footer>
        </div>
      </div>

      {/* Toasts */}
      <div className="fixed bottom-4 right-4 space-y-2 z-50">
        {toasts.map(t => (
          <div key={t.id} className={`px-3 py-2 rounded shadow text-sm ${t.type === 'error' ? 'bg-red-600 text-white' : 'bg-neutral-800 text-white'}`}>{t.message}</div>
        ))}
      </div>
    </div>
  );
}
