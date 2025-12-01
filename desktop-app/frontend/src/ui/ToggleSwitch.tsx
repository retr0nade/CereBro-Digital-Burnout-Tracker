import React from 'react';
import { motion } from 'framer-motion';
import { Sun, Moon } from 'lucide-react';

interface ToggleSwitchProps {
    checked: boolean;
    onChange: () => void;
    iconOn?: React.ReactNode;
    iconOff?: React.ReactNode;
}

export default function ToggleSwitch({ checked, onChange, iconOn, iconOff }: ToggleSwitchProps) {
    return (
        <button
            onClick={onChange}
            className={`relative w-14 h-7 rounded-full p-1 transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-focus ${checked ? 'bg-surface-hover border border-border' : 'bg-surface-hover border border-border'
                }`}
            aria-pressed={checked}
        >
            <motion.div
                className="w-5 h-5 rounded-full bg-brand shadow-sm flex items-center justify-center text-white"
                layout
                transition={{ type: "spring", stiffness: 700, damping: 30 }}
                style={{
                    marginLeft: checked ? 'auto' : 0,
                    marginRight: checked ? 0 : 'auto'
                }}
            >
                {checked ? (iconOn || <Moon size={12} />) : (iconOff || <Sun size={12} />)}
            </motion.div>
        </button>
    );
}
