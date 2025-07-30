import React, { useEffect, useState } from 'react';
export default function ScreenTime() {
  const [data, setData] = useState<any>({});
  useEffect(()=>{fetch('http://localhost:5005/api/metrics').then(r=>r.json()).then(setData)},[]);
  const usage = data?.recent_usage || [];
  return (
    <div className="max-w-xl mx-auto mt-10 text-white">
      <h1 className="text-2xl font-bold mb-6">App Usage (Today)</h1>
      <div className="bg-white bg-opacity-10 rounded-xl">
        <table className="w-full table-auto">
          <thead>
            <tr className="border-b border-white/20">
              <th className="text-left px-4 py-2">App</th>
              <th className="text-left px-4 py-2">Title</th>
              <th className="text-left px-4 py-2">When</th>
            </tr>
          </thead>
          <tbody>
            {usage.map((row:any,i:number) => (
              <tr key={i} className="hover:bg-white hover:bg-opacity-5 transition">
                <td className="px-4 py-1">{row[0]}</td>
                <td className="px-4 py-1">{row[1]}</td>
                <td className="px-4 py-1">{(new Date(row[2]*1000)).toLocaleTimeString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
