import React, { useEffect, useState } from 'react';

/**
 * Screenshot mode utility for producing clean, consistent screenshots
 * Activates when ?shot=1 is present in the URL
 */

export interface ScreenshotModeConfig {
  isActive: boolean;
  hideControls: boolean;
  useSeedData: boolean;
  highContrast: boolean;
  hideDebugPanel: boolean;
  hideToastNotifications: boolean;
  hideFloatingElements: boolean;
}

/**
 * Hook to detect and manage screenshot mode
 */
export function useScreenshotMode(): ScreenshotModeConfig {
  const [config, setConfig] = useState<ScreenshotModeConfig>({
    isActive: false,
    hideControls: false,
    useSeedData: false,
    highContrast: false,
    hideDebugPanel: false,
    hideToastNotifications: false,
    hideFloatingElements: false,
  });

  useEffect(() => {
    const checkScreenshotMode = () => {
      const urlParams = new URLSearchParams(window.location.search);
      const isActive = urlParams.get('shot') === '1';
      
      if (isActive) {
        // Apply screenshot mode styles
        document.documentElement.classList.add('screenshot-mode');
        
        setConfig({
          isActive: true,
          hideControls: true,
          useSeedData: true,
          highContrast: true,
          hideDebugPanel: true,
          hideToastNotifications: true,
          hideFloatingElements: true,
        });
      } else {
        // Remove screenshot mode styles
        document.documentElement.classList.remove('screenshot-mode');
        
        setConfig({
          isActive: false,
          hideControls: false,
          useSeedData: false,
          highContrast: false,
          hideDebugPanel: false,
          hideToastNotifications: false,
          hideFloatingElements: false,
        });
      }
    };

    // Check on mount
    checkScreenshotMode();

    // Listen for URL changes (for SPA navigation)
    const handlePopState = () => checkScreenshotMode();
    window.addEventListener('popstate', handlePopState);

    return () => {
      window.removeEventListener('popstate', handlePopState);
      document.documentElement.classList.remove('screenshot-mode');
    };
  }, []);

  return config;
}

/**
 * Generate consistent seed data for charts in screenshot mode
 */
export function getScreenshotSeedData() {
  return {
    // Screen time data (last 7 days)
    screenTimeData: [
      {
        id: 'Screen Time',
        data: [
          { hour: 0, value: 0 },
          { hour: 1, value: 0 },
          { hour: 2, value: 0 },
          { hour: 3, value: 0 },
          { hour: 4, value: 0 },
          { hour: 5, value: 0 },
          { hour: 6, value: 15 },
          { hour: 7, value: 45 },
          { hour: 8, value: 120 },
          { hour: 9, value: 180 },
          { hour: 10, value: 240 },
          { hour: 11, value: 195 },
          { hour: 12, value: 90 },
          { hour: 13, value: 60 },
          { hour: 14, value: 210 },
          { hour: 15, value: 285 },
          { hour: 16, value: 255 },
          { hour: 17, value: 180 },
          { hour: 18, value: 120 },
          { hour: 19, value: 90 },
          { hour: 20, value: 75 },
          { hour: 21, value: 45 },
          { hour: 22, value: 30 },
          { hour: 23, value: 15 },
        ]
      }
    ],

    // App usage data
    appUsageData: [
      { id: 'VS Code', label: 'VS Code', value: 420, color: '#007ACC' },
      { id: 'Chrome', label: 'Chrome', value: 380, color: '#4285F4' },
      { id: 'Terminal', label: 'Terminal', value: 180, color: '#00D4AA' },
      { id: 'Figma', label: 'Figma', value: 150, color: '#F24E1E' },
      { id: 'Slack', label: 'Slack', value: 120, color: '#4A154B' },
      { id: 'Spotify', label: 'Spotify', value: 90, color: '#1DB954' },
      { id: 'Notion', label: 'Notion', value: 75, color: '#000000' },
      { id: 'GitHub', label: 'GitHub', value: 60, color: '#24292E' },
    ],

    // Focus vs Distraction data
    focusDistractionData: [
      { hour: 8, focus: 45, distraction: 15 },
      { hour: 9, focus: 120, distraction: 30 },
      { hour: 10, focus: 180, distraction: 60 },
      { hour: 11, focus: 135, distraction: 60 },
      { hour: 12, focus: 60, distraction: 30 },
      { hour: 13, focus: 45, distraction: 15 },
      { hour: 14, focus: 150, distraction: 60 },
      { hour: 15, focus: 210, distraction: 75 },
      { hour: 16, focus: 180, distraction: 75 },
      { hour: 17, focus: 120, distraction: 60 },
      { hour: 18, focus: 90, distraction: 30 },
    ],

    // Idle & Break data
    idleBreakData: [
      { hour: 8, idle: 0, breaks: 0 },
      { hour: 9, idle: 5, breaks: 10 },
      { hour: 10, idle: 8, breaks: 15 },
      { hour: 11, idle: 12, breaks: 20 },
      { hour: 12, idle: 30, breaks: 30 },
      { hour: 13, idle: 15, breaks: 15 },
      { hour: 14, idle: 10, breaks: 15 },
      { hour: 15, idle: 8, breaks: 12 },
      { hour: 16, idle: 12, breaks: 18 },
      { hour: 17, idle: 6, breaks: 10 },
      { hour: 18, idle: 4, breaks: 8 },
    ],

    // Real-time input activity data
    inputActivityData: [
      {
        id: 'Total Inputs',
        data: [
          { x: '09:00', y: 45 },
          { x: '09:15', y: 120 },
          { x: '09:30', y: 85 },
          { x: '09:45', y: 200 },
          { x: '10:00', y: 150 },
          { x: '10:15', y: 180 },
          { x: '10:30', y: 95 },
          { x: '10:45', y: 220 },
          { x: '11:00', y: 160 },
          { x: '11:15', y: 140 },
          { x: '11:30', y: 110 },
          { x: '11:45', y: 75 },
        ]
      },
      {
        id: 'Keypresses',
        data: [
          { x: '09:00', y: 35 },
          { x: '09:15', y: 95 },
          { x: '09:30', y: 65 },
          { x: '09:45', y: 150 },
          { x: '10:00', y: 110 },
          { x: '10:15', y: 135 },
          { x: '10:30', y: 70 },
          { x: '10:45', y: 165 },
          { x: '11:00', y: 120 },
          { x: '11:15', y: 105 },
          { x: '11:30', y: 85 },
          { x: '11:45', y: 55 },
        ]
      },
      {
        id: 'Mouse Clicks',
        data: [
          { x: '09:00', y: 10 },
          { x: '09:15', y: 25 },
          { x: '09:30', y: 20 },
          { x: '09:45', y: 50 },
          { x: '10:00', y: 40 },
          { x: '10:15', y: 45 },
          { x: '10:30', y: 25 },
          { x: '10:45', y: 55 },
          { x: '11:00', y: 40 },
          { x: '11:15', y: 35 },
          { x: '11:30', y: 25 },
          { x: '11:45', y: 20 },
        ]
      }
    ],

    // Real-time app usage data
    realtimeAppUsageData: [
      { id: 'VS Code', label: 'VS Code', value: 45 },
      { id: 'Chrome', label: 'Chrome', value: 30 },
      { id: 'Terminal', label: 'Terminal', value: 15 },
      { id: 'Figma', label: 'Figma', value: 10 },
    ],

    // Activity timeline events
    activityTimelineEvents: [
      {
        id: '1',
        appName: 'VS Code',
        action: 'Opened project',
        timestamp: Date.now() - 300000,
        type: 'app_usage' as const,
      },
      {
        id: '2',
        appName: 'Chrome',
        action: 'Browsed documentation',
        timestamp: Date.now() - 600000,
        type: 'app_usage' as const,
      },
      {
        id: '3',
        appName: 'Terminal',
        action: 'Ran build command',
        timestamp: Date.now() - 900000,
        type: 'app_usage' as const,
      },
      {
        id: '4',
        appName: 'System',
        action: 'Input activity (150 inputs)',
        timestamp: Date.now() - 1200000,
        type: 'input' as const,
      },
      {
        id: '5',
        appName: 'Break Monitor',
        action: 'Short break',
        timestamp: Date.now() - 1500000,
        duration: 300,
        type: 'break' as const,
      },
    ],

    // Metrics summary
    metricsSummary: {
      app_switches: 24,
      recent_usage: 180,
      idle_events: 8,
      focus_score: 78,
      total_app_time: 420,
      total_idle_time: 45,
    },
  };
}

/**
 * Utility to conditionally render elements based on screenshot mode
 */
export function ScreenshotModeWrapper({ 
  children, 
  hideInScreenshot = false 
}: { 
  children?: React.ReactNode; 
  hideInScreenshot?: boolean;
}) {
  const { isActive } = useScreenshotMode();
  
  if (isActive && hideInScreenshot) {
    return null;
  }
  
  return children as React.ReactElement;
}

/**
 * Utility to get data based on screenshot mode
 */
export function useScreenshotData<T>(
  realData: T,
  seedData: T
): T {
  const { useSeedData } = useScreenshotMode();
  return useSeedData ? seedData : realData;
}
