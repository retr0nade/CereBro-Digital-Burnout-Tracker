import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart3, 
  Activity, 
  Clock, 
  Settings, 
  Server, 
  Download,
  Menu,
  X
} from 'lucide-react';
import { clsx } from 'clsx';

interface SidebarProps {
  currentView: string;
  onViewChange: (view: string) => void;
  collapsed?: boolean;
  onToggle?: () => void;
}

interface NavItem {
  key: string;
  label: string;
  icon: React.ComponentType<any>;
  shortcut?: string;
}

const navItems: NavItem[] = [
  { key: 'dashboard', label: 'Dashboard', icon: BarChart3, shortcut: 'D' },
  { key: 'realtime', label: 'Real-time', icon: Activity, shortcut: 'R' },
  { key: 'screentime', label: 'Screen Time', icon: Clock, shortcut: 'S' },
  { key: 'services', label: 'Services', icon: Server, shortcut: 'V' },
  { key: 'settings', label: 'Settings', icon: Settings, shortcut: ',' },
  { key: 'export', label: 'Export', icon: Download, shortcut: 'E' },
];

export default function Sidebar({ currentView, onViewChange, collapsed = false, onToggle }: SidebarProps) {
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  // Keyboard navigation
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey) {
        const item = navItems.find(item => 
          item.shortcut && e.key.toLowerCase() === item.shortcut.toLowerCase()
        );
        if (item) {
          e.preventDefault();
          onViewChange(item.key);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onViewChange]);

  const sidebarVariants = {
    expanded: { width: 240 },
    collapsed: { width: 60 }
  };

  const underlineVariants = {
    hidden: { scaleX: 0, opacity: 0 },
    visible: { scaleX: 1, opacity: 1 }
  };

  return (
    <motion.aside
      className={clsx(
        "flex flex-col border-r border-border bg-surface/50 backdrop-blur-sm",
        "transition-all duration-300 ease-out"
      )}
      variants={sidebarVariants}
      animate={collapsed ? 'collapsed' : 'expanded'}
      initial={false}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <AnimatePresence mode="wait">
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="flex items-center gap-2"
            >
              <div className="w-8 h-8 rounded-lg bg-brand flex items-center justify-center">
                <BarChart3 className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold text-text">CereBro</span>
            </motion.div>
          )}
        </AnimatePresence>
        
        <button
          onClick={onToggle}
          className={clsx(
            "p-1.5 rounded-md transition-colors",
            "hover:bg-surface-alt focus:outline-none focus:ring-2 focus:ring-focus",
            collapsed && "mx-auto"
          )}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <Menu className="w-4 h-4 text-text-muted" />
          ) : (
            <X className="w-4 h-4 text-text-muted" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.key;
          const isHovered = hoveredItem === item.key;

          return (
            <div key={item.key} className="relative">
              <button
                onClick={() => onViewChange(item.key)}
                onMouseEnter={() => setHoveredItem(item.key)}
                onMouseLeave={() => setHoveredItem(null)}
                className={clsx(
                  "relative w-full flex items-center gap-3 px-3 py-2.5 rounded-lg",
                  "transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-focus",
                  "group",
                  isActive
                    ? "bg-brand/10 text-brand border border-brand/20"
                    : "text-text-muted hover:text-text hover:bg-surface-alt",
                  collapsed && "justify-center px-2"
                )}
                title={collapsed ? `${item.label} (${item.shortcut ? `Cmd+${item.shortcut}` : ''})` : undefined}
              >
                <Icon className={clsx(
                  "w-5 h-5 transition-transform duration-200",
                  isActive ? "text-brand" : "text-text-muted group-hover:text-text",
                  (isHovered || isActive) && "scale-110"
                )} />
                
                <AnimatePresence mode="wait">
                  {!collapsed && (
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="flex items-center justify-between flex-1 min-w-0"
                    >
                      <span className="font-medium truncate">{item.label}</span>
                      {item.shortcut && (
                        <span className="text-dashboard-sm text-text-muted/60 font-mono">
                          ⌘{item.shortcut}
                        </span>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Active indicator underline */}
                {isActive && (
                  <motion.div
                    className="absolute bottom-0 left-2 right-2 h-0.5 bg-brand rounded-full"
                    variants={underlineVariants}
                    initial="hidden"
                    animate="visible"
                    layoutId="activeIndicator"
                  />
                )}
              </button>

              {/* Tooltip for collapsed state */}
              <AnimatePresence>
                {collapsed && isHovered && (
                  <motion.div
                    initial={{ opacity: 0, x: -10, scale: 0.9 }}
                    animate={{ opacity: 1, x: 0, scale: 1 }}
                    exit={{ opacity: 0, x: -10, scale: 0.9 }}
                    className={clsx(
                      "absolute left-full top-1/2 -translate-y-1/2 ml-2 z-50",
                      "bg-surface border border-border rounded-lg px-3 py-2 shadow-pop",
                      "text-sm font-medium text-text whitespace-nowrap"
                    )}
                  >
                    {item.label}
                    {item.shortcut && (
                                              <span className="text-text-muted ml-2 text-dashboard-sm">⌘{item.shortcut}</span>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <AnimatePresence mode="wait">
          {!collapsed ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-dashboard-sm text-text-muted text-center"
            >
              v{new Date().getFullYear()}
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-2 h-2 bg-ok rounded-full mx-auto"
              title="System running"
            />
          )}
        </AnimatePresence>
      </div>
    </motion.aside>
  );
}
