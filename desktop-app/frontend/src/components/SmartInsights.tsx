import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, BrainCircuit, Coffee, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface SmartInsightsProps {
    focusScore: number;
    appSwitches: number;
    idleEvents: number;
    totalMinutes: number;
}

export default function SmartInsights({ focusScore, appSwitches, idleEvents, totalMinutes }: SmartInsightsProps) {
    // Determine user state
    const isHighBurnout = focusScore < 40 && appSwitches > 100;
    const isFlowState = focusScore > 75 && totalMinutes > 60;
    const isFatigued = totalMinutes > 240 && idleEvents < 2; // > 4 hours with few breaks
    const isDistracted = appSwitches > 150;

    const getInsightContent = () => {
        if (isHighBurnout) {
            return {
                icon: <AlertTriangle className="w-6 h-6 text-danger" />,
                title: "High Burnout Risk Detected",
                message: "Your focus is low and you're switching apps frequently. This often indicates cognitive overload.",
                tips: [
                    "Take a 15-minute break away from screens.",
                    "Try the Pomodoro technique: 25m work, 5m break.",
                    "Close unnecessary browser tabs to reduce distractions."
                ],
                tone: "danger"
            };
        } else if (isFatigued) {
            return {
                icon: <Coffee className="w-6 h-6 text-warning" />,
                title: "Extended Session Detected",
                message: "You've been active for a long time without enough breaks. Fatigue kills productivity.",
                tips: [
                    "Stand up and stretch for 2 minutes.",
                    "Hydrate! Drink a glass of water.",
                    "Look at something 20 feet away for 20 seconds."
                ],
                tone: "warning"
            };
        } else if (isFlowState) {
            return {
                icon: <Sparkles className="w-6 h-6 text-brand" />,
                title: "You're in the Flow!",
                message: "Excellent focus score and sustained activity. You are crushing it today!",
                tips: [
                    "Keep this momentum going, but don't forget to rest eventually.",
                    "This is a great time to tackle your hardest tasks."
                ],
                tone: "brand"
            };
        } else if (isDistracted) {
            return {
                icon: <BrainCircuit className="w-6 h-6 text-orange-400" />,
                title: "High Distraction Level",
                message: "You're multitasking heavily. Context switching can reduce IQ by up to 10 points.",
                tips: [
                    "Focus on one single task for the next 20 minutes.",
                    "Turn off non-essential notifications.",
                    "Group similar tasks together."
                ],
                tone: "warning"
            };
        } else if (totalMinutes < 5) {
            return {
                icon: <Sparkles className="w-6 h-6 text-brand" />,
                title: "Gathering Insights",
                message: "We're collecting data to provide personalized recommendations. Keep working naturally.",
                tips: [],
                tone: "brand"
            };
        } else {
            return {
                icon: <CheckCircle2 className="w-6 h-6 text-ok" />,
                title: "Steady Progress",
                message: "You're maintaining a balanced workflow. Keep up the good work.",
                tips: [], // No tips needed for normal state
                tone: "ok"
            };
        }
    };

    const content = getInsightContent();

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-2xl p-6 border ${content.tone === 'danger' ? 'bg-danger/5 border-danger/20' :
                    content.tone === 'warning' ? 'bg-yellow-500/5 border-yellow-500/20' :
                        content.tone === 'brand' ? 'bg-brand/5 border-brand/20' :
                            'bg-surface border-border'
                }`}
        >
            <div className="flex items-start gap-4">
                <div className={`p-3 rounded-xl ${content.tone === 'danger' ? 'bg-danger/10' :
                        content.tone === 'warning' ? 'bg-yellow-500/10' :
                            content.tone === 'brand' ? 'bg-brand/10' :
                                'bg-surface-hover'
                    }`}>
                    {content.icon}
                </div>
                <div className="flex-1 space-y-2">
                    <h3 className={`text-lg font-semibold ${content.tone === 'danger' ? 'text-danger' :
                            content.tone === 'warning' ? 'text-yellow-500' :
                                content.tone === 'brand' ? 'text-brand' :
                                    'text-text'
                        }`}>
                        {content.title}
                    </h3>
                    <p className="text-text-muted leading-relaxed">
                        {content.message}
                    </p>

                    {content.tips.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-border/50">
                            <h4 className="text-sm font-medium text-text mb-2">Recommended Actions:</h4>
                            <ul className="space-y-2">
                                {content.tips.map((tip, i) => (
                                    <li key={i} className="flex items-center gap-2 text-sm text-text-muted">
                                        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-50" />
                                        {tip}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
}
