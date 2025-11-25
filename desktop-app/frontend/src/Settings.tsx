import React, { useState, useEffect } from 'react';
import { config } from './config';
import { Save, RefreshCw, AlertCircle, Check, RotateCcw } from 'lucide-react';
import { motion } from 'framer-motion';
import GlassCard from './ui/GlassCard';
import SectionHeader from './ui/SectionHeader';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from './ui/Select';
import { Slider } from './ui/Slider';
import { Switch } from './ui/Switch';
import LivePreview from './components/LivePreview';

interface Settings {
  theme: 'dark' | 'light' | 'system';
  reduceMotion: boolean;
  dataRetentionDays: number;
  autoExportEnabled: boolean;
  exportFormat: 'csv' | 'json';
  exportFrequency: number;
  notificationsEnabled: boolean;
  breakReminders: boolean;
  focusSessionAlerts: boolean;
  idleNotifications: boolean;
  idleTimeout: number;
  focusSessionLength: number;
  breakDuration: number;
  breakInterval: number;
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<Settings>({
    theme: 'dark',
    reduceMotion: false,
    dataRetentionDays: 30,
    autoExportEnabled: false,
    exportFormat: 'csv',
    exportFrequency: 24,
    notificationsEnabled: true,
    breakReminders: true,
    focusSessionAlerts: true,
    idleNotifications: false,
    idleTimeout: 5,
    focusSessionLength: 25,
    breakDuration: 5,
    breakInterval: 60
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch(`${config.API_URL}/api/config`);
      if (response.ok) {
        const data = await response.json();
        setSettings(prev => ({
          ...prev,
          idleTimeout: data.services?.idle_monitor?.timeout_seconds / 60 || 5,
          focusSessionLength: data.services?.focus_timer?.default_session_length / 60 || 25,
          breakReminders: data.services?.break_monitor?.enabled || true,
          breakInterval: data.services?.break_monitor?.min_break_duration / 60 || 60,
          breakDuration: data.services?.break_monitor?.max_break_duration / 60 || 15
        }));
      } else {
        throw new Error('Failed to load settings');
      }
    } catch (error) {
      // console.error('Error loading settings:', error);
      setMessage({ type: 'error', text: 'Failed to load settings' });
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setSaving(true);

    try {
      // Convert frontend settings to backend config format
      const configUpdates = {
        services: {
          idle_monitor: {
            timeout_seconds: settings.idleTimeout * 60
          },
          focus_timer: {
            default_session_length: settings.focusSessionLength * 60
          },
          break_monitor: {
            enabled: settings.breakReminders,
            min_break_duration: settings.breakInterval * 60,
            max_break_duration: settings.breakDuration * 60
          }
        }
      };

      const response = await fetch(`${config.API_URL}/api/config`, {
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
      // console.error('Error saving settings:', error);
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
      <div className="max-w-7xl mx-auto mt-4 p-4">
        <GlassCard>
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
            <span className="ml-3 text-text-muted">Loading settings...</span>
          </div>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto mt-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Settings</h1>
          <p className="text-text-muted mt-1">
            Customize your experience and preferences
          </p>
        </div>
        <div className="flex gap-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={fetchSettings}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-neutral-600/20 text-text-muted hover:bg-neutral-600/30 border border-neutral-600/40 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            <span className="text-sm font-medium">Reset</span>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={saveSettings}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand/20 text-brand hover:bg-brand/30 border border-brand/40 transition-colors"
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-brand"></div>
                <span className="text-sm font-medium">Saving...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span className="text-sm font-medium">Save Settings</span>
              </>
            )}
          </motion.button>
        </div>
      </div>

      {/* Settings Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Settings */}
        <div className="lg:col-span-2 space-y-6">

          {/* Theme Section */}
          <GlassCard>
            <SectionHeader
              title="Theme & Appearance"
              subtitle="Customize the visual appearance"
              tooltip="Configure theme, animations, and visual preferences"
              className="mb-4"
            />
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-text">Theme</label>
                  <p className="text-xs text-text-muted">Choose your preferred color scheme</p>
                </div>
                <Select value={settings.theme} onValueChange={(value) => handleInputChange('theme', value)}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="light">Light</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-text">Reduce Motion</label>
                  <p className="text-xs text-text-muted">Disable animations for accessibility</p>
                </div>
                <Switch
                  checked={settings.reduceMotion}
                  onCheckedChange={(checked) => handleInputChange('reduceMotion', checked)}
                />
              </div>
            </div>
          </GlassCard>

          {/* Data Retention Section */}
          <GlassCard>
            <SectionHeader
              title="Data Retention"
              subtitle="Manage data storage and exports"
              tooltip="Configure how long data is kept and automatic export settings"
              className="mb-4"
            />
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-text">Data Retention Period</label>
                <p className="text-xs text-text-muted mb-2">How long to keep your activity data</p>
                <Slider
                  value={[settings.dataRetentionDays]}
                  onValueChange={([value]) => handleInputChange('dataRetentionDays', value)}
                  max={365}
                  min={7}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-text-muted mt-1">
                  <span>7 days</span>
                  <span className="font-medium">{settings.dataRetentionDays} days</span>
                  <span>1 year</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-text">Auto Export</label>
                  <p className="text-xs text-text-muted">Automatically export data periodically</p>
                </div>
                <Switch
                  checked={settings.autoExportEnabled}
                  onCheckedChange={(checked) => handleInputChange('autoExportEnabled', checked)}
                />
              </div>

              {settings.autoExportEnabled && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-text">Export Format</label>
                    <Select value={settings.exportFormat} onValueChange={(value) => handleInputChange('exportFormat', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="csv">CSV</SelectItem>
                        <SelectItem value="json">JSON</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-text">Frequency (hours)</label>
                    <Slider
                      value={[settings.exportFrequency]}
                      onValueChange={([value]) => handleInputChange('exportFrequency', value)}
                      max={168}
                      min={1}
                      step={1}
                      className="w-full"
                    />
                    <div className="text-xs text-text-muted mt-1 text-center">
                      {settings.exportFrequency} hours
                    </div>
                  </div>
                </div>
              )}
            </div>
          </GlassCard>

          {/* Notifications Section */}
          <GlassCard>
            <SectionHeader
              title="Notifications"
              subtitle="Configure alert preferences"
              tooltip="Manage when and how you receive notifications"
              className="mb-4"
            />
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-text">Enable Notifications</label>
                  <p className="text-xs text-text-muted">Receive system notifications</p>
                </div>
                <Switch
                  checked={settings.notificationsEnabled}
                  onCheckedChange={(checked) => handleInputChange('notificationsEnabled', checked)}
                />
              </div>

              {settings.notificationsEnabled && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-text">Break Reminders</label>
                      <p className="text-xs text-text-muted">Get reminded to take breaks</p>
                    </div>
                    <Switch
                      checked={settings.breakReminders}
                      onCheckedChange={(checked) => handleInputChange('breakReminders', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-text">Focus Session Alerts</label>
                      <p className="text-xs text-text-muted">Notifications when focus sessions end</p>
                    </div>
                    <Switch
                      checked={settings.focusSessionAlerts}
                      onCheckedChange={(checked) => handleInputChange('focusSessionAlerts', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-text">Idle Notifications</label>
                      <p className="text-xs text-text-muted">Alert when you've been idle too long</p>
                    </div>
                    <Switch
                      checked={settings.idleNotifications}
                      onCheckedChange={(checked) => handleInputChange('idleNotifications', checked)}
                    />
                  </div>
                </div>
              )}
            </div>
          </GlassCard>

          {/* Performance Section */}
          <GlassCard>
            <SectionHeader
              title="Performance & Timing"
              subtitle="Configure tracking behavior"
              tooltip="Adjust timing settings for idle detection, focus sessions, and breaks"
              className="mb-4"
            />
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-text">Idle Timeout</label>
                <p className="text-xs text-text-muted mb-2">Time before considering you idle</p>
                <Slider
                  value={[settings.idleTimeout]}
                  onValueChange={([value]) => handleInputChange('idleTimeout', value)}
                  max={30}
                  min={1}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-text-muted mt-1">
                  <span>1 min</span>
                  <span className="font-medium">{settings.idleTimeout} min</span>
                  <span>30 min</span>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-text">Focus Session Length</label>
                <p className="text-xs text-text-muted mb-2">Default duration for focus sessions</p>
                <Slider
                  value={[settings.focusSessionLength]}
                  onValueChange={([value]) => handleInputChange('focusSessionLength', value)}
                  max={120}
                  min={5}
                  step={5}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-text-muted mt-1">
                  <span>5 min</span>
                  <span className="font-medium">{settings.focusSessionLength} min</span>
                  <span>2 hours</span>
                </div>
              </div>

              {settings.breakReminders && (
                <>
                  <div>
                    <label className="text-sm font-medium text-text">Break Interval</label>
                    <p className="text-xs text-text-muted mb-2">How often to remind you to take breaks</p>
                    <Slider
                      value={[settings.breakInterval]}
                      onValueChange={([value]) => handleInputChange('breakInterval', value)}
                      max={240}
                      min={15}
                      step={15}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-text-muted mt-1">
                      <span>15 min</span>
                      <span className="font-medium">{settings.breakInterval} min</span>
                      <span>4 hours</span>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-text">Break Duration</label>
                    <p className="text-xs text-text-muted mb-2">Recommended break length</p>
                    <Slider
                      value={[settings.breakDuration]}
                      onValueChange={([value]) => handleInputChange('breakDuration', value)}
                      max={60}
                      min={1}
                      step={1}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-text-muted mt-1">
                      <span>1 min</span>
                      <span className="font-medium">{settings.breakDuration} min</span>
                      <span>1 hour</span>
                    </div>
                  </div>
                </>
              )}
            </div>
          </GlassCard>
        </div>

        {/* Right Column - Live Preview */}
        <div className="lg:col-span-1">
          <LivePreview
            theme={settings.theme}
            reduceMotion={settings.reduceMotion}
            idleTimeout={settings.idleTimeout}
            focusSessionLength={settings.focusSessionLength}
            breakRemindersEnabled={settings.breakReminders}
            notificationsEnabled={settings.notificationsEnabled}
          />
        </div>
      </div>
    </div>
  );
};

export default Settings;
