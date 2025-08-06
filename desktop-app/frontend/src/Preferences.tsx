import React, { useEffect, useState } from 'react';

interface Preferences {
  track_apps: boolean;
  track_idle: boolean;
  idle_threshold: number;
  track_screenshots: boolean;
  track_audio: boolean;
  track_input: boolean;
  focus_reminders: boolean;
  break_suggestions: boolean;
  theme: 'light' | 'dark' | 'auto';
}

export default function Preferences() {
  const [preferences, setPreferences] = useState<Preferences>({
    track_apps: true,
    track_idle: true,
    idle_threshold: 180,
    track_screenshots: false,
    track_audio: false,
    track_input: false,
    focus_reminders: true,
    break_suggestions: true,
    theme: 'dark'
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchPreferences();
  }, []);

  const fetchPreferences = async () => {
    try {
      const response = await fetch('http://localhost:5005/api/preferences');
      if (response.ok) {
        const data = await response.json();
        setPreferences({ ...preferences, ...data });
      }
    } catch (error) {
      console.error('Failed to fetch preferences:', error);
    } finally {
      setLoading(false);
    }
  };

  const savePreferences = async () => {
    setSaving(true);
    setMessage(null);
    
    try {
      const response = await fetch('http://localhost:5005/api/preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences),
      });
      
      if (response.ok) {
        setMessage('Preferences saved successfully!');
        setTimeout(() => setMessage(null), 3000);
      } else {
        setMessage('Failed to save preferences');
      }
    } catch (error) {
      setMessage('Error saving preferences');
      console.error('Save preferences error:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = (key: keyof Preferences) => {
    setPreferences(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleNumberChange = (key: keyof Preferences, value: number) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleThemeChange = (theme: 'light' | 'dark' | 'auto') => {
    setPreferences(prev => ({
      ...prev,
      theme
    }));
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto mt-8 p-6">
        <div className="bg-white bg-opacity-10 rounded-xl p-6 shadow-lg">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-300 rounded w-1/3 mb-4"></div>
            <div className="space-y-3">
              <div className="h-4 bg-gray-300 rounded"></div>
              <div className="h-4 bg-gray-300 rounded w-5/6"></div>
              <div className="h-4 bg-gray-300 rounded w-4/6"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto mt-8 p-6">
      <h1 className="text-3xl font-bold mb-6 text-center">Preferences</h1>
      
      {message && (
        <div className={`mb-6 p-4 rounded-lg ${
          message.includes('success') 
            ? 'bg-green-500 bg-opacity-20 border border-green-500 text-green-300'
            : 'bg-red-500 bg-opacity-20 border border-red-500 text-red-300'
        }`}>
          {message}
        </div>
      )}

      <div className="bg-white bg-opacity-10 rounded-xl p-6 shadow-lg space-y-6">
        
        {/* Monitoring Settings */}
        <div>
          <h2 className="text-xl font-bold mb-4">Monitoring Settings</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium">Track Application Usage</label>
                <p className="text-xs text-gray-400">Monitor which applications you use</p>
              </div>
              <button
                onClick={() => handleToggle('track_apps')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  preferences.track_apps ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  preferences.track_apps ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium">Track Idle Time</label>
                <p className="text-xs text-gray-400">Monitor when you're inactive</p>
              </div>
              <button
                onClick={() => handleToggle('track_idle')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  preferences.track_idle ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  preferences.track_idle ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium">Track Input Activity</label>
                <p className="text-xs text-gray-400">Monitor keyboard and mouse activity</p>
              </div>
              <button
                onClick={() => handleToggle('track_input')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  preferences.track_input ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  preferences.track_input ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium">Track Audio</label>
                <p className="text-xs text-gray-400">Monitor microphone activity</p>
              </div>
              <button
                onClick={() => handleToggle('track_audio')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  preferences.track_audio ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  preferences.track_audio ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium">Take Screenshots</label>
                <p className="text-xs text-gray-400">Capture screen activity (privacy sensitive)</p>
              </div>
              <button
                onClick={() => handleToggle('track_screenshots')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  preferences.track_screenshots ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  preferences.track_screenshots ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>
        </div>

        {/* Idle Threshold */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Idle Time Threshold</h3>
          <div className="flex items-center space-x-4">
            <input
              type="range"
              min="60"
              max="600"
              step="30"
              value={preferences.idle_threshold}
              onChange={(e) => handleNumberChange('idle_threshold', parseInt(e.target.value))}
              className="flex-1"
            />
            <span className="text-sm font-mono w-16">
              {Math.floor(preferences.idle_threshold / 60)}m {preferences.idle_threshold % 60}s
            </span>
          </div>
        </div>

        {/* Wellness Features */}
        <div>
          <h2 className="text-xl font-bold mb-4">Wellness Features</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium">Focus Reminders</label>
                <p className="text-xs text-gray-400">Get notified when you're distracted</p>
              </div>
              <button
                onClick={() => handleToggle('focus_reminders')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  preferences.focus_reminders ? 'bg-green-600' : 'bg-gray-600'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  preferences.focus_reminders ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium">Break Suggestions</label>
                <p className="text-xs text-gray-400">Get reminded to take breaks</p>
              </div>
              <button
                onClick={() => handleToggle('break_suggestions')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  preferences.break_suggestions ? 'bg-green-600' : 'bg-gray-600'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  preferences.break_suggestions ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>
        </div>

        {/* Theme Settings */}
        <div>
          <h2 className="text-xl font-bold mb-4">Appearance</h2>
          <div className="grid grid-cols-3 gap-3">
            {(['light', 'dark', 'auto'] as const).map((theme) => (
              <button
                key={theme}
                onClick={() => handleThemeChange(theme)}
                className={`p-3 rounded-lg border-2 transition-colors ${
                  preferences.theme === theme
                    ? 'border-blue-500 bg-blue-500 bg-opacity-20'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="text-sm font-medium capitalize">{theme}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Save Button */}
        <div className="pt-6 border-t border-gray-600">
          <button
            onClick={savePreferences}
            disabled={saving}
            className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {saving ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>
      </div>
    </div>
  );
}
