import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppShell from './components/layout/AppShell';

// Placeholder Pages
const Dashboard = () => (
  <div>
    <h2 className="text-2xl font-semibold mb-4">Dashboard</h2>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="h-32 bg-gray-900 rounded-xl border border-gray-800 flex items-center justify-center text-gray-500">Metric Card Placeholder</div>
      <div className="h-32 bg-gray-900 rounded-xl border border-gray-800 flex items-center justify-center text-gray-500">Metric Card Placeholder</div>
      <div className="h-32 bg-gray-900 rounded-xl border border-gray-800 flex items-center justify-center text-gray-500">Metric Card Placeholder</div>
    </div>
  </div>
);

const Placeholder = ({ title }: { title: string }) => (
  <div className="flex flex-col items-center justify-center h-full text-gray-400">
    <h2 className="text-3xl font-light">{title}</h2>
    <p className="mt-2 text-sm">Under Construction</p>
  </div>
);

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="timeline" element={<Placeholder title="Activity Timeline" />} />
          <Route path="focus" element={<Placeholder title="Focus Analytics" />} />
          <Route path="distractions" element={<Placeholder title="Distraction Analysis" />} />
          <Route path="copilot" element={<Placeholder title="AI Copilot" />} />
          <Route path="settings" element={<Placeholder title="Settings" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
