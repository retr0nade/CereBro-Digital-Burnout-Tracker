import React from "react";

interface FocusBarProps {
  focus: number;         // minutes focused today
  distracted: number;    // minutes distracted today
  idle: number;          // minutes idle today
}

export default function FocusBar({ focus, distracted, idle }: FocusBarProps) {
  const total = focus + distracted + idle || 1; // Avoid div/0
  const focusPct = (focus / total) * 100;
  const distractPct = (distracted / total) * 100;
  const idlePct = (idle / total) * 100;

  return (
    <div className="w-full max-w-xl my-6">
      <div className="flex text-xs justify-between mb-1 font-medium">
        <span className="text-green-600">Focus</span>
        <span className="text-yellow-600">Distracted</span>
        <span className="text-gray-500">Idle</span>
      </div>
      <div className="flex overflow-hidden rounded-lg h-5 w-full bg-gray-200">
        <div style={{ width: `${focusPct}%` }} className="bg-green-500 transition-all"></div>
        <div style={{ width: `${distractPct}%` }} className="bg-yellow-400 transition-all"></div>
        <div style={{ width: `${idlePct}%` }} className="bg-gray-400 transition-all"></div>
      </div>
      <div className="flex mt-2 text-xs text-gray-600 justify-between">
        <span>{focus} min focus</span>
        <span>{distracted} min distracted</span>
        <span>{idle} min idle</span>
      </div>
    </div>
  );
}
