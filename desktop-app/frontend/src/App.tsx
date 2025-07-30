import React, { useEffect, useState } from 'react';
import Dashboard from './Dashboard';
import ScreenTime from './ScreenTime';
import Preferences from './Preferences';

function App() {
  const [page, setPage] = useState('dashboard');
  return (
    <div className="bg-gradient-to-tr from-indigo-600 via-purple-700 to-pink-500 min-h-screen text-white">
      <nav className="flex gap-4 p-4 font-bold">
        <button onClick={()=>setPage('dashboard')} className={page==='dashboard'?"underline":""}>Dashboard</button>
        <button onClick={()=>setPage('screentime')} className={page==='screentime'?"underline":""}>Screentime</button>
        <button onClick={()=>setPage('prefs')} className={page==='prefs'?"underline":""}>Preferences</button>
      </nav>
      {page === 'dashboard' && <Dashboard />}
      {page === 'screentime' && <ScreenTime />}
      {page === 'prefs' && <Preferences />}
    </div>
  );
}
export default App;
