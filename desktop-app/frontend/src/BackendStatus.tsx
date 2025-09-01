import React from 'react';

interface BackendStatusProps {
  status: {
    running: boolean;
    port: number;
    error?: string;
  };
  onStart: () => void;
  onStop: () => void;
}

export default function BackendStatus({ status, onStart, onStop }: BackendStatusProps) {
  return (
    <div className="flex items-center space-x-3">
      {/* Status Indicator */}
      <div className="flex items-center space-x-2">
        <div 
          className={`w-3 h-3 rounded-full ${
            status.running 
              ? 'bg-green-500 animate-pulse' 
              : 'bg-red-500'
          }`}
        />
        <span className="text-sm font-medium">
          {status.running ? 'Backend Running' : 'Backend Stopped'}
        </span>
      </div>

      {/* Port Display */}
      <span className="text-xs text-gray-400">
        Port {status.port}
      </span>

      {/* Error Message */}
      {status.error && (
        <div className="text-xs text-red-400 max-w-xs truncate" title={status.error}>
          {status.error}
        </div>
      )}

      {/* Control Buttons */}
      <div className="flex space-x-2">
        {status.running ? (
          <button onClick={onStop} className="btn btn-danger px-2 py-1 text-xs">Stop</button>
        ) : (
          <button onClick={onStart} className="btn btn-primary px-2 py-1 text-xs">Start</button>
        )}
      </div>
    </div>
  );
} 