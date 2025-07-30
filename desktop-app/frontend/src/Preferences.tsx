import React, { useEffect, useState } from 'react';
const allMetrics = [
  {key:"track_apps",label:"Active App Tracking",desc:"Tracks which application is in the foreground and for how long."},
  {key:"track_idle",label:"Idle Time Tracking",desc:"Detects keyboard/mouse inactivity for focus and break analysis."},
  {key:"track_screenshots",label:"Screenshots",desc:"Takes periodic desktop screenshots for session review."},
  {key:"track_audio",label:"Ambient Noise Detection",desc:"Microphone audio levels for noisy/quiet environment context."}
]
export default function Preferences() {
  const [prefs,setPrefs] = useState<any>({});
  useEffect(()=>{fetch('/api/preferences').then(r=>r.json()).then(setPrefs)},[]);
  function onToggle(key:string){
    fetch('/api/preferences',{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...prefs,[key]:!prefs[key]})})
      .then(()=>setPrefs({...prefs,[key]:!prefs[key]}));
  }
  return (
    <div className="max-w-xl mx-auto my-8">
      <h1 className="text-2xl font-bold mb-4">Preferences</h1>
      <div>
        {allMetrics.map(m=>(
          <div key={m.key} className="flex items-center gap-4 bg-white bg-opacity-10 rounded-xl p-4 my-3">
            <label className="font-semibold w-64">{m.label}</label>
            <input type="checkbox" checked={prefs[m.key]} onChange={()=>onToggle(m.key)}
              className="accent-pink-500 w-7 h-7"/>
            <span className="text-xs opacity-80">{m.desc}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
