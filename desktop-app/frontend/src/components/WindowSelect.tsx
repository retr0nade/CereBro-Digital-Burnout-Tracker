import React, { useState } from 'react';
import { Clock, ChevronDown } from 'lucide-react';

interface WindowSelectProps {
  value: number; // minutes
  onChange: (minutes: number) => void;
  className?: string;
}

const WINDOW_OPTIONS = [
  { label: '5 min', value: 5 },
  { label: '10 min', value: 10 },
  { label: '15 min', value: 15 },
];

export const WindowSelect = React.memo<WindowSelectProps>(({ 
  value, 
  onChange, 
  className = '' 
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleSelect = (minutes: number) => {
    onChange(minutes);
    setIsOpen(false);
  };

  const currentLabel = WINDOW_OPTIONS.find(opt => opt.value === value)?.label || `${value} min`;

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 bg-surface border border-border rounded-full hover:bg-surface-hover transition-colors"
      >
        <Clock className="w-3 h-3 text-text-muted" />
        <span className="text-xs text-text">Window: {currentLabel}</span>
        <ChevronDown className="w-3 h-3 text-text-muted" />
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-2 w-32 bg-surface border border-border rounded-lg shadow-pop z-50">
          <div className="p-1">
            {WINDOW_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => handleSelect(option.value)}
                className={`w-full text-left px-3 py-2 text-xs rounded hover:bg-surface-hover transition-colors ${
                  value === option.value ? 'text-brand' : 'text-text'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
});

WindowSelect.displayName = 'WindowSelect';

export default WindowSelect;
