import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ParticleEffectProps {
  trigger: boolean;
  onComplete?: () => void;
}

interface Particle {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  maxLife: number;
  size: number;
  color: string;
}

export default function ParticleEffect({ trigger, onComplete }: ParticleEffectProps) {
  const [particles, setParticles] = useState<Particle[]>([]);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    if (trigger) {
      setIsActive(true);
      createParticles();
      
      // Auto-cleanup after animation
      const timer = setTimeout(() => {
        setIsActive(false);
        setParticles([]);
        onComplete?.();
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [trigger, onComplete]);

  const createParticles = () => {
    const newParticles: Particle[] = [];
    const particleCount = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 8 : 16;
    
    for (let i = 0; i < particleCount; i++) {
      const angle = (i / particleCount) * Math.PI * 2;
      const speed = 2 + Math.random() * 3;
      const size = 2 + Math.random() * 3;
      
      newParticles.push({
        id: i,
        x: 50, // Center of container
        y: 50,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 0,
        maxLife: 60 + Math.random() * 40, // 1-1.67 seconds at 60fps
        size,
        color: getRandomColor(),
      });
    }
    
    setParticles(newParticles);
  };

  const getRandomColor = (): string => {
    const colors = [
      '#3b82f6', // brand blue
      '#10b981', // success green
      '#f59e0b', // warning orange
      '#ef4444', // danger red
      '#8b5cf6', // purple
      '#06b6d4', // cyan
    ];
    return colors[Math.floor(Math.random() * colors.length)];
  };

  const updateParticles = () => {
    setParticles(prev => 
      prev
        .map(particle => ({
          ...particle,
          x: particle.x + particle.vx,
          y: particle.y + particle.vy,
          life: particle.life + 1,
          vy: particle.vy + 0.1, // gravity
        }))
        .filter(particle => particle.life < particle.maxLife)
    );
  };

  useEffect(() => {
    if (particles.length === 0) return;

    const interval = setInterval(updateParticles, 16); // ~60fps
    return () => clearInterval(interval);
  }, [particles.length]);

  return (
    <AnimatePresence>
      {isActive && (
        <motion.div
          className="fixed inset-0 pointer-events-none z-50"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <div className="relative w-full h-full">
            {particles.map((particle) => {
              const progress = particle.life / particle.maxLife;
              const opacity = 1 - progress;
              const scale = 1 - progress * 0.5;
              
              return (
                <motion.div
                  key={particle.id}
                  className="absolute rounded-full"
                  style={{
                    left: `${particle.x}%`,
                    top: `${particle.y}%`,
                    width: `${particle.size}px`,
                    height: `${particle.size}px`,
                    backgroundColor: particle.color,
                    opacity,
                    transform: `scale(${scale})`,
                    boxShadow: `0 0 ${particle.size * 2}px ${particle.color}`,
                  }}
                  initial={{ scale: 0, opacity: 1 }}
                  animate={{ 
                    scale: [0, 1, scale],
                    opacity: [1, 1, opacity],
                  }}
                  transition={{
                    duration: 0.3,
                    ease: "easeOut",
                  }}
                />
              );
            })}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
