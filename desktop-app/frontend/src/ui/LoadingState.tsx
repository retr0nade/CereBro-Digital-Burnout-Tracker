import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, CheckCircle2 } from 'lucide-react';

interface LoadingStateProps {
    steps?: string[];
    onComplete?: () => void;
    autoAdvance?: boolean;
    duration?: number;
}

const defaultSteps = [
    "Initializing application...",
    "Connecting to local services...",
    "Loading user preferences...",
    "Fetching analytics data...",
    "Preparing dashboard..."
];

export default function LoadingState({
    steps = defaultSteps,
    onComplete,
    autoAdvance = true,
    duration = 800
}: LoadingStateProps) {
    const [currentStep, setCurrentStep] = useState(0);

    useEffect(() => {
        if (!autoAdvance) return;

        if (currentStep < steps.length) {
            const timer = setTimeout(() => {
                setCurrentStep(prev => prev + 1);
            }, duration);
            return () => clearTimeout(timer);
        } else {
            if (onComplete) {
                // Small delay before completion to show 100%
                const timer = setTimeout(onComplete, 500);
                return () => clearTimeout(timer);
            }
        }
    }, [currentStep, steps.length, autoAdvance, duration, onComplete]);

    const progress = Math.min(((currentStep) / (steps.length - 1)) * 100, 100);

    return (
        <div className="w-full h-[60vh] flex flex-col items-center justify-center p-8">
            <div className="max-w-md w-full space-y-8">
                {/* Icon Animation */}
                <div className="flex justify-center relative">
                    <div className="absolute inset-0 bg-brand/20 blur-xl rounded-full animate-pulse" />
                    <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        className="relative z-10 bg-surface p-4 rounded-2xl border border-border shadow-soft"
                    >
                        <Loader2 className="w-8 h-8 text-brand" />
                    </motion.div>
                </div>

                {/* Progress Section */}
                <div className="space-y-4">
                    <div className="flex justify-between text-sm font-medium text-text-muted">
                        <span>Loading...</span>
                        <span>{Math.round(progress)}%</span>
                    </div>

                    {/* Progress Bar */}
                    <div className="h-2 bg-surface-hover rounded-full overflow-hidden">
                        <motion.div
                            className="h-full bg-gradient-to-r from-brand to-brand-hover"
                            initial={{ width: 0 }}
                            animate={{ width: `${progress}%` }}
                            transition={{ duration: 0.5 }}
                        />
                    </div>

                    {/* Steps Display */}
                    <div className="h-8 relative overflow-hidden">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={currentStep}
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                exit={{ y: -20, opacity: 0 }}
                                transition={{ duration: 0.3 }}
                                className="absolute inset-0 flex items-center justify-center text-sm text-text font-medium"
                            >
                                {currentStep < steps.length ? steps[currentStep] : "Ready!"}
                            </motion.div>
                        </AnimatePresence>
                    </div>
                </div>

                {/* Completed Steps List (Optional visual flair) */}
                <div className="space-y-2 pt-4 border-t border-border/50">
                    {steps.map((step, index) => (
                        <motion.div
                            key={index}
                            initial={false}
                            animate={{
                                opacity: index < currentStep ? 0.5 : index === currentStep ? 1 : 0.2,
                                x: index === currentStep ? 10 : 0
                            }}
                            className="flex items-center gap-3 text-xs"
                        >
                            <div className={`w-4 h-4 rounded-full flex items-center justify-center border ${index < currentStep
                                    ? "bg-ok/10 border-ok text-ok"
                                    : index === currentStep
                                        ? "bg-brand/10 border-brand text-brand"
                                        : "border-border text-text-muted"
                                }`}>
                                {index < currentStep ? (
                                    <CheckCircle2 className="w-2.5 h-2.5" />
                                ) : (
                                    <div className={`w-1.5 h-1.5 rounded-full ${index === currentStep ? "bg-brand animate-pulse" : "bg-transparent"}`} />
                                )}
                            </div>
                            <span className={index === currentStep ? "text-brand font-medium" : "text-text-muted"}>
                                {step}
                            </span>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
}
