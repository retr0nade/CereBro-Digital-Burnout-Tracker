import { Outlet } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Activity, 
  Brain, 
  AlertTriangle, 
  MessageSquareText, 
  Settings 
} from 'lucide-react';

const navItems = [
  { name: 'Dashboard', icon: LayoutDashboard, path: '/' },
  { name: 'Activity Timeline', icon: Activity, path: '/timeline' },
  { name: 'Focus Analytics', icon: Brain, path: '/focus' },
  { name: 'Distraction Analysis', icon: AlertTriangle, path: '/distractions' },
  { name: 'AI Copilot', icon: MessageSquareText, path: '/copilot' },
  { name: 'Settings', icon: Settings, path: '/settings' },
];

export default function AppShell() {
  return (
    <div className="flex bg-gray-950 text-gray-100 h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-6">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
            Cerebro
          </h1>
        </div>
        <nav className="flex-1 px-4 space-y-2">
          {navItems.map((item) => (
            <a 
              key={item.name} 
              href={item.path} 
              className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors text-gray-400 hover:text-white"
            >
              <item.icon className="w-5 h-5" />
              <span>{item.name}</span>
            </a>
          ))}
        </nav>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-gray-800 bg-gray-900/50 flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center space-x-4">
            <div className="flex flex-col">
              <span className="text-sm text-gray-400">Current Focus</span>
              <span className="font-semibold text-green-400">--</span>
            </div>
            <div className="flex flex-col border-l border-gray-700 pl-4">
              <span className="text-sm text-gray-400">Today's Deep Work</span>
              <span className="font-semibold">0h 0m</span>
            </div>
          </div>
          <div className="flex items-center space-x-4 text-sm gap-2">
            <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full border border-green-500/30 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              System Active
            </span>
          </div>
        </header>
        
        <main className="flex-1 overflow-auto p-6 bg-gray-950">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
