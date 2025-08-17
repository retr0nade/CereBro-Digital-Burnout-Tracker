import React from 'react';
import ServiceControl from './ServiceControl';

export default function ServiceManager() {
  const services = [
    {
      serviceName: 'window_tracker',
      displayName: 'Window Tracker',
      description: 'Tracks active applications and window usage'
    },
    {
      serviceName: 'idle_monitor',
      displayName: 'Idle Monitor',
      description: 'Monitors user inactivity and logs idle periods'
    },
    {
      serviceName: 'input_logger',
      displayName: 'Input Logger',
      description: 'Logs keyboard keypresses and mouse clicks'
    },
    {
      serviceName: 'screen_time_tracker',
      displayName: 'Screen Time Tracker',
      description: 'Tracks daily active screen time'
    },
    {
      serviceName: 'focus_timer',
      displayName: 'Focus Timer',
      description: 'Manages and logs focus sessions'
    },
    {
      serviceName: 'break_monitor',
      displayName: 'Break Monitor',
      description: 'Monitors for user inactivity breaks and system lock/unlock events'
    }
  ];

  return (
    <div className="max-w-6xl mx-auto mt-8 p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Service Manager</h1>
        <p className="text-gray-300">
          Control individual tracking services. Start or stop services as needed.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {services.map((service) => (
          <ServiceControl
            key={service.serviceName}
            serviceName={service.serviceName}
            displayName={service.displayName}
            description={service.description}
          />
        ))}
      </div>

      <div className="mt-8 p-4 bg-blue-500 bg-opacity-20 border border-blue-500 rounded-lg">
        <h3 className="text-lg font-semibold text-blue-300 mb-2">Service Information</h3>
        <ul className="text-sm text-blue-200 space-y-1">
          <li>• <strong>Window Tracker:</strong> Monitors which applications you're using and for how long</li>
          <li>• <strong>Idle Monitor:</strong> Detects when you're away from your computer</li>
          <li>• <strong>Input Logger:</strong> Tracks your keyboard and mouse activity</li>
          <li>• <strong>Screen Time Tracker:</strong> Calculates your total daily screen time</li>
          <li>• <strong>Focus Timer:</strong> Helps you manage focused work sessions</li>
          <li>• <strong>Break Monitor:</strong> Tracks your breaks and system lock events</li>
        </ul>
      </div>
    </div>
  );
}
