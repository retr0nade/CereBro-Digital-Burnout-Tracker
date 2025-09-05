import React from 'react';
import { motion } from 'framer-motion';
import { Sun, Moon } from 'lucide-react';
import { clsx } from 'clsx';

interface SegmentedControlProps {
  value: 'light' | 'dark';
  onChange: (value: 'light' | 'dark') => void;
  className?: string;
}

export default function SegmentedControl({ 
  value, 
  onChange, 
  className = '' 
}: SegmentedControlProps) {
  const options = [
    { value: 'light' as const, label: 'Light', icon: Sun },
    { value: 'dark' as const, label: 'Dark', icon: Moon },
  ];

  return (
    <div className={clsx(
      "relative inline-flex items-center p-1 rounded-lg",
      "bg-surface border border-border",
      "shadow-soft",
      className
    )}>
      {/* Background indicator */}
      <motion.div
        className="absolute inset-1 bg-surface-alt rounded-md shadow-sm"
        layoutId="theme-segment-bg"
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 30,
        }}
      />
      
      {options.map((option) => {
        const Icon = option.icon;
        const isSelected = value === option.value;
        
        return (
          <motion.button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={clsx(
              "relative flex items-center gap-1.5 px-3 py-1.5 rounded-md",
              "text-sm font-medium transition-colors duration-200",
              "focus:outline-none focus:ring-2 focus:ring-focus focus:ring-offset-1",
              "z-10",
              isSelected
                ? "text-text"
                : "text-text-muted hover:text-text"
            )}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            aria-pressed={isSelected}
            aria-label={`Switch to ${option.label} theme`}
          >
            <Icon 
              className="w-3.5 h-3.5" 
              aria-hidden="true"
            />
            <span className="hidden sm:inline">
              {option.label}
            </span>
          </motion.button>
        );
      })}
    </div>
  );
}
