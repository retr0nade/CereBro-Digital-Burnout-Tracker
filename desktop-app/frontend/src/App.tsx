import React, { useEffect, useState } from "react";
import Dashboard from "./Dashboard";
import RealTimeDashboard from "./RealTimeDashboard";
import ScreenTime from "./ScreenTime";
import Preferences from "./Preferences";
import ServiceManager from "./ServiceManager";
import BackendStatus from "./BackendStatus";

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
  const [currentView, setCurrentView] = useState<'dashboard' | 'realtime' | 'screentime' | 'preferences' | 'services'>('dashboard');
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
      }
    } catch (error) {
      console.error('Failed to start backend:', error);
    }
  };

  const stopBackend = async () => {
    try {
      if (window.__TAURI__) {
        await window.__TAURI__.invoke('stop_backend_command');
        setTimeout(checkBackendStatus, 1000);
      }
    } catch (error) {
      console.error('Failed to stop backend:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-700 text-white selection:bg-pink-400/40">
      {/* Header Bar */}
      <div className="w-full bg-black bg-opacity-20 px-8 py-4 flex items-center justify-between shadow">
        <div className="flex items-center space-x-6">
          <h1 className="text-2xl font-bold text-pink-400 tracking-tight">CereBro Burnout Tracker</h1>
          
          {/* Navigation */}
          <nav className="flex space-x-4">
            <button
              onClick={() => setCurrentView('dashboard')}
              className={`px-3 py-2 rounded-lg transition-colors ${
                currentView === 'dashboard' 
                  ? 'bg-pink-500 text-white' 
                  : 'text-gray-300 hover:text-white hover:bg-pink-500/20'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setCurrentView('realtime')}
              className={`px-3 py-2 rounded-lg transition-colors ${
                currentView === 'realtime' 
                  ? 'bg-pink-500 text-white' 
                  : 'text-gray-300 hover:text-white hover:bg-pink-500/20'
              }`}
            >
              Real-time
            </button>
            <button
              onClick={() => setCurrentView('screentime')}
              className={`px-3 py-2 rounded-lg transition-colors ${
                currentView === 'screentime' 
                  ? 'bg-pink-500 text-white' 
                  : 'text-gray-300 hover:text-white hover:bg-pink-500/20'
              }`}
            >
              Screen Time
            </button>
            <button
              onClick={() => setCurrentView('preferences')}
              className={`px-3 py-2 rounded-lg transition-colors ${
                currentView === 'preferences' 
                  ? 'bg-pink-500 text-white' 
                  : 'text-gray-300 hover:text-white hover:bg-pink-500/20'
              }`}
            >
              Preferences
            </button>
            <button
              onClick={() => setCurrentView('services')}
              className={`px-3 py-2 rounded-lg transition-colors ${
                currentView === 'services' 
                  ? 'bg-pink-500 text-white' 
                  : 'text-gray-300 hover:text-white hover:bg-pink-500/20'
              }`}
            >
              Services
            </button>
          </nav>
        </div>

        <div className="flex items-center space-x-4">
          {/* Backend Status */}
          <BackendStatus 
            status={backendStatus}
            onStart={startBackend}
            onStop={stopBackend}
          />
          
          <span className="text-xs uppercase tracking-widest text-white/70 font-semibold">
            <a className="hover:underline" target="_blank" rel="noopener noreferrer" href="https://github.com/retr0nade/CereBro-Mental-Burnout-Tracker">
              GitHub
            </a>
          </span>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex flex-col items-center justify-center px-2">
        {currentView === 'dashboard' && <Dashboard />}
        {currentView === 'realtime' && <RealTimeDashboard />}
        {currentView === 'screentime' && <ScreenTime />}
        {currentView === 'preferences' && <Preferences />}
        {currentView === 'services' && <ServiceManager />}
      </main>

      <footer className="w-full py-4 text-center text-xs text-white/40 mt-8">
        © {new Date().getFullYear()} retr0nade — CereBro Mental Burnout Tracker
      </footer>
    </div>
  );
}
