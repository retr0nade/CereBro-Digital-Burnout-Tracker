import React, { useState } from 'react';
import { Calendar, ChevronDown } from 'lucide-react';
import { DashRange } from '../state/analyticsStore';

interface RangeControlProps {
  value: DashRange;
  onChange: (range: DashRange) => void;
  className?: string;
}

const PRESETS = [
  { label: 'Today', value: 'today' as const },
  { label: '7 Days', value: 'week' as const },
  { label: '30 Days', value: 'month' as const },
];

export const RangeControl = React.memo<RangeControlProps>(({ 
  value, 
  onChange, 
  className = '' 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [showCalendar, setShowCalendar] = useState(false);

  const handlePresetSelect = (preset: typeof PRESETS[0]['value']) => {
    const now = Date.now();
    let from: number | null = null;
    let to: number | null = null;

    switch (preset) {
      case 'today':
        const startOfDay = new Date();
        startOfDay.setHours(0, 0, 0, 0);
        from = startOfDay.getTime();
        to = now;
        break;
      case 'week':
        from = now - (7 * 24 * 60 * 60 * 1000);
        to = now;
        break;
      case 'month':
        from = now - (30 * 24 * 60 * 60 * 1000);
        to = now;
        break;
    }

    onChange({
      from,
      to,
      preset
    });
    setIsOpen(false);
  };

  const handleCustomRange = (from: number, to: number) => {
    onChange({
      from,
      to,
      preset: 'today' // Custom ranges use 'today' as fallback
    });
    setShowCalendar(false);
  };

  const formatRange = () => {
    if (!value.from || !value.to) return 'Select Range';
    
    const fromDate = new Date(value.from);
    const toDate = new Date(value.to);
    
    if (value.preset === 'today') {
      return 'Today';
    } else if (value.preset === 'week') {
      return 'Last 7 Days';
    } else if (value.preset === 'month') {
      return 'Last 30 Days';
    } else {
      // Custom range
      return `${fromDate.toLocaleDateString()} - ${toDate.toLocaleDateString()}`;
    }
  };

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-surface border border-border rounded-lg hover:bg-surface-hover transition-colors"
      >
        <Calendar className="w-4 h-4 text-text-muted" />
        <span className="text-sm text-text">{formatRange()}</span>
        <ChevronDown className="w-4 h-4 text-text-muted" />
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-2 w-48 bg-surface border border-border rounded-lg shadow-pop z-50">
          <div className="p-2">
            {PRESETS.map((preset) => (
              <button
                key={preset.value}
                onClick={() => handlePresetSelect(preset.value)}
                className={`w-full text-left px-3 py-2 text-sm rounded hover:bg-surface-hover transition-colors ${
                  value.preset === preset.value ? 'text-brand' : 'text-text'
                }`}
              >
                {preset.label}
              </button>
            ))}
            <div className="border-t border-border my-2"></div>
            <button
              onClick={() => {
                setShowCalendar(true);
                setIsOpen(false);
              }}
              className="w-full text-left px-3 py-2 text-sm text-text rounded hover:bg-surface-hover transition-colors"
            >
              Custom Range...
            </button>
          </div>
        </div>
      )}

      {showCalendar && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-surface border border-border rounded-lg shadow-pop z-50 p-4">
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-text">Select Custom Range</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-text-muted mb-1">From</label>
                <input
                  type="date"
                  className="w-full px-2 py-1 text-sm bg-surface border border-border rounded"
                  onChange={(e) => {
                    // Handle date input
                  }}
                />
              </div>
              <div>
                <label className="block text-xs text-text-muted mb-1">To</label>
                <input
                  type="date"
                  className="w-full px-2 py-1 text-sm bg-surface border border-border rounded"
                  onChange={(e) => {
                    // Handle date input
                  }}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  const from = new Date().getTime() - (7 * 24 * 60 * 60 * 1000);
                  const to = new Date().getTime();
                  handleCustomRange(from, to);
                }}
                className="flex-1 px-3 py-2 text-sm bg-brand text-white rounded hover:bg-brand-hover transition-colors"
              >
                Apply
              </button>
              <button
                onClick={() => setShowCalendar(false)}
                className="flex-1 px-3 py-2 text-sm bg-surface border border-border text-text rounded hover:bg-surface-hover transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

RangeControl.displayName = 'RangeControl';

export default RangeControl;
