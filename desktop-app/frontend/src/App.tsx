import React from "react";
import Dashboard from "./Dashboard";
import ScreenTime from "./ScreenTime";
import Preferences from "./Preferences";

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-700 text-white selection:bg-pink-400/40">
      {/* Header Bar */}
      <div className="w-full bg-black bg-opacity-20 px-8 py-4 flex items-center justify-between shadow">
        <h1 className="text-2xl font-bold text-pink-400 tracking-tight">CereBro Burnout Tracker</h1>
        <span className="text-xs uppercase tracking-widest text-white/70 font-semibold">
          <a className="hover:underline" target="_blank" rel="noopener noreferrer" href="https://github.com/retr0nade/CereBro-Mental-Burnout-Tracker">
            GitHub
          </a>
        </span>
      </div>

      {/* Main Content: Dashboard page(s) */}
      <main className="flex flex-col items-center justify-center px-2">
        <Dashboard />
        <ScreenTime />
        <Preferences />
      </main>

      <footer className="w-full py-4 text-center text-xs text-white/40 mt-8">
        © {new Date().getFullYear()} retr0nade — CereBro Mental Burnout Tracker
      </footer>
    </div>
  );
}
