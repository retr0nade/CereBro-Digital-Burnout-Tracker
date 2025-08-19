import React, { useState, useEffect } from 'react';

interface Settings {
  idle_timeout: number;
  focus_session_length: number;
  break_reminders: {
    enabled: boolean;
    interval_minutes: number;
    duration_minutes: number;
  };
  export_frequency: {
    enabled: boolean;
    interval_hours: number;
    format: 'csv' | 'json';
  };
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<Settings>({
    idle_timeout: 300,
    focus_session_length: 25,
    break_reminders: {
      enabled: true,
      interval_minutes: 60,
      duration_minutes: 5
    },
    export_frequency: {
      enabled: false,
      interval_hours: 24,
      format: 'csv'
    }
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await fetch('http://localhost:5005/api/config');
      if (response.ok) {
        const config = await response.json();
        
        // Map backend config to frontend settings
        setSettings({
          idle_timeout: config.services?.idle_monitor?.timeout_seconds / 60 || 5, // Convert seconds to minutes
          focus_session_length: config.services?.focus_timer?.default_session_length / 60 || 25, // Convert seconds to minutes
          break_reminders: {
            enabled: config.services?.break_monitor?.enabled || true,
            interval_minutes: config.services?.break_monitor?.min_break_duration / 60 || 60, // Convert seconds to minutes
            duration_minutes: config.services?.break_monitor?.max_break_duration / 60 || 15 // Convert seconds to minutes
          },
          export_frequency: {
            enabled: false, // This would be a new setting
            interval_hours: 24,
            format: 'csv'
          }
        });
      } else {
        throw new Error('Failed to load settings');
      }
    } catch (error) {
      console.error('Error loading settings:', error);
      setMessage({ type: 'error', text: 'Failed to load settings' });
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    setMessage(null);

    try {
      // Convert frontend settings to backend config format
      const configUpdates = {
        services: {
          idle_monitor: {
            timeout_seconds: settings.idle_timeout * 60 // Convert minutes to seconds
          },
          focus_timer: {
            default_session_length: settings.focus_session_length * 60 // Convert minutes to seconds
          },
          break_monitor: {
            enabled: settings.break_reminders.enabled,
            min_break_duration: settings.break_reminders.interval_minutes * 60, // Convert minutes to seconds
            max_break_duration: settings.break_reminders.duration_minutes * 60 // Convert minutes to seconds
          }
        }
      };

      const response = await fetch('http://localhost:5005/api/config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(configUpdates)
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Settings saved successfully!' });
      } else {
        const error = await response.json();
        throw new Error(error.error || 'Failed to save settings');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      setMessage({ type: 'error', text: `Failed to save settings: ${error instanceof Error ? error.message : 'Unknown error'}` });
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (path: string, value: any) => {
    setSettings(prev => {
      const newSettings = { ...prev };
      const keys = path.split('.');
      let current: any = newSettings;
      
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }
      
      current[keys[keys.length - 1]] = value;
      return newSettings;
    });
  };

  if (loading) {
    return (
      <div className="w-full max-w-4xl mx-auto p-6">
        <div className="bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-center">
            <svg className="animate-spin h-8 w-8 text-pink-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="ml-3 text-gray-300">Loading settings...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      <div className="bg-gray-800 rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-pink-400 mb-6">Settings</h2>
        
        {/* Message Display */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg ${
            message.type === 'success' 
              ? 'bg-green-600 text-white' 
              : 'bg-red-600 text-white'
          }`}>
            {message.text}
          </div>
        )}

        <div className="space-y-8">
          {/* Idle Timeout Settings */}
          <div className="bg-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-medium text-white mb-4">Idle Detection</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Idle Timeout (minutes)
                </label>
                <input
                  type="number"
                  min="1"
                  max="60"
                  value={settings.idle_timeout}
                  onChange={(e) => handleInputChange('idle_timeout', parseInt(e.target.value) || 5)}
                  className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-pink-500"
                />
                <p className="text-sm text-gray-400 mt-1">
                  Time before the system considers you idle (1-60 minutes)
                </p>
              </div>
            </div>
          </div>

          {/* Focus Session Settings */}
          <div className="bg-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-medium text-white mb-4">Focus Sessions</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Default Session Length (minutes)
                </label>
                <input
                  type="number"
                  min="5"
                  max="120"
                  value={settings.focus_session_length}
                  onChange={(e) => handleInputChange('focus_session_length', parseInt(e.target.value) || 25)}
                  className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-pink-500"
                />
                <p className="text-sm text-gray-400 mt-1">
                  Default duration for focus sessions (5-120 minutes)
                </p>
              </div>
            </div>
          </div>

          {/* Break Reminder Settings */}
          <div className="bg-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-medium text-white mb-4">Break Reminders</h3>
            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="break_reminders_enabled"
                  checked={settings.break_reminders.enabled}
                  onChange={(e) => handleInputChange('break_reminders.enabled', e.target.checked)}
                  className="h-4 w-4 text-pink-600 focus:ring-pink-500 border-gray-300 rounded"
                />
                <label htmlFor="break_reminders_enabled" className="ml-2 text-sm text-gray-300">
                  Enable break reminders
                </label>
              </div>
              
              {settings.break_reminders.enabled && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Reminder Interval (minutes)
                    </label>
                    <input
                      type="number"
                      min="15"
                      max="240"
                      value={settings.break_reminders.interval_minutes}
                      onChange={(e) => handleInputChange('break_reminders.interval_minutes', parseInt(e.target.value) || 60)}
                      className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-pink-500"
                    />
                    <p className="text-sm text-gray-400 mt-1">
                      How often to remind you to take breaks (15-240 minutes)
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Break Duration (minutes)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="60"
                      value={settings.break_reminders.duration_minutes}
                      onChange={(e) => handleInputChange('break_reminders.duration_minutes', parseInt(e.target.value) || 5)}
                      className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-pink-500"
                    />
                    <p className="text-sm text-gray-400 mt-1">
                      Recommended break duration (1-60 minutes)
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Export Frequency Settings */}
          <div className="bg-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-medium text-white mb-4">Automatic Data Export</h3>
            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="export_frequency_enabled"
                  checked={settings.export_frequency.enabled}
                  onChange={(e) => handleInputChange('export_frequency.enabled', e.target.checked)}
                  className="h-4 w-4 text-pink-600 focus:ring-pink-500 border-gray-300 rounded"
                />
                <label htmlFor="export_frequency_enabled" className="ml-2 text-sm text-gray-300">
                  Enable automatic data export
                </label>
              </div>
              
              {settings.export_frequency.enabled && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Export Interval (hours)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="168"
                      value={settings.export_frequency.interval_hours}
                      onChange={(e) => handleInputChange('export_frequency.interval_hours', parseInt(e.target.value) || 24)}
                      className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-pink-500"
                    />
                    <p className="text-sm text-gray-400 mt-1">
                      How often to automatically export data (1-168 hours)
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Export Format
                    </label>
                    <select
                      value={settings.export_frequency.format}
                      onChange={(e) => handleInputChange('export_frequency.format', e.target.value as 'csv' | 'json')}
                      className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-pink-500"
                    >
                      <option value="csv">CSV</option>
                      <option value="json">JSON</option>
                    </select>
                    <p className="text-sm text-gray-400 mt-1">
                      Format for automatic exports
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end space-x-4">
            <button
              onClick={loadSettings}
              disabled={saving}
              className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              Reset to Defaults
            </button>
            <button
              onClick={saveSettings}
              disabled={saving}
              className="px-6 py-3 bg-pink-600 hover:bg-pink-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center"
            >
              {saving ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Saving...
                </>
              ) : (
                'Save Settings'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
