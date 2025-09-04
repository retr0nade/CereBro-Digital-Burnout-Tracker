import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

interface BackendStatusType {
  running: boolean;
  port: number;
  error?: string;
}

interface AppShellProps {
  currentView: string;
  onViewChange: (view: string) => void;
  backendStatus: BackendStatusType;
  onStartBackend: () => void;
  onStopBackend: () => void;
  theme: 'light' | 'dark';
  onThemeToggle: () => void;
}

interface MainAreaProps {
  sidebarCollapsed: boolean;
}

function MainArea({ children, sidebarCollapsed }: React.PropsWithChildren<MainAreaProps>) {
  return (
    <motion.div
      className="flex-1 flex flex-col min-h-screen"
      animate={{
        marginLeft: 0, // Sidebar is positioned absolute/fixed, so no margin needed
      }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      <div className="flex-1 flex flex-col">
        {/* Main content area */}
        <main className="flex-1 p-6">
          <div className="max-w-screen-2xl mx-auto">
            <motion.div
              className="min-h-full"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              {children}
            </motion.div>
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-border bg-surface/50 backdrop-blur-sm">
          <div className="max-w-screen-2xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between text-dashboard-sm text-text-muted">
              <div className="flex items-center gap-4">
                <span>© {new Date().getFullYear()} retr0nade</span>
                <span className="hidden sm:inline">CereBro Mental Burnout Tracker</span>
              </div>
              <div className="flex items-center gap-4">
                <motion.div
                  className="flex items-center gap-2"
                  animate={{
                    opacity: [0.5, 1, 0.5],
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                >
                  <div className="w-1 h-1 bg-ok rounded-full" />
                  <span>System Active</span>
                </motion.div>
                <span className="hidden md:inline">Press ⌘K for quick actions</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </motion.div>
  );
}

export default function AppShell({
  children,
  currentView,
  onViewChange,
  backendStatus,
  onStartBackend,
  onStopBackend,
  theme,
  onThemeToggle,
}: React.PropsWithChildren<AppShellProps>) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    // Check localStorage for saved preference
    const saved = localStorage.getItem('sidebar-collapsed');
    return saved === 'true';
  });

  // Save sidebar state to localStorage
  useEffect(() => {
    localStorage.setItem('sidebar-collapsed', sidebarCollapsed.toString());
  }, [sidebarCollapsed]);

  // Auto-collapse on smaller screens
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setSidebarCollapsed(true);
      }
    };

    handleResize(); // Check initial size
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Toggle sidebar with Cmd/Ctrl + B
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        e.preventDefault();
        setSidebarCollapsed(prev => !prev);
      }
      
      // Toggle theme with Cmd/Ctrl + Shift + T
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'T') {
        e.preventDefault();
        onThemeToggle();
      }

      // Close tooltips/popovers with Escape
      if (e.key === 'Escape') {
        // This will close any open tooltips or popovers
        const activeElement = document.activeElement as HTMLElement;
        if (activeElement && activeElement.blur) {
          activeElement.blur();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onThemeToggle]);

  const handleToggleSidebar = () => {
    setSidebarCollapsed(prev => !prev);
  };

  return (
    <div className={clsx(
      "app-shell min-h-screen",
      "selection:bg-brand/30 selection:text-white"
    )}>
      {/* Skip to main content link for screen readers */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50 bg-brand text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-focus"
      >
        Skip to main content
      </a>
      
      <div className="flex min-h-screen relative">
        {/* Sidebar */}
        <motion.div
          className="relative z-30"
          layout
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        >
          <Sidebar
            currentView={currentView}
            onViewChange={onViewChange}
            collapsed={sidebarCollapsed}
            onToggle={handleToggleSidebar}
          />
        </motion.div>

        {/* Main content area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Topbar */}
          <Topbar
            backendStatus={backendStatus}
            onStartBackend={onStartBackend}
            onStopBackend={onStopBackend}
            theme={theme}
            onThemeToggle={onThemeToggle}
          />

          {/* Main content */}
          <main id="main-content" className="flex-1">
            <MainArea sidebarCollapsed={sidebarCollapsed}>
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentView}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2, ease: "easeOut" }}
                >
                  {children}
                </motion.div>
              </AnimatePresence>
            </MainArea>
          </main>
        </div>
      </div>

      {/* Overlay for mobile when sidebar is expanded */}
      <AnimatePresence>
        {!sidebarCollapsed && (
          <motion.div
            className="fixed inset-0 bg-overlay z-20 lg:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarCollapsed(true)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
