import React from 'react';
import { motion } from 'framer-motion';
import { CheckIcon } from '@heroicons/react/24/outline';
import { BrandLogo } from './BrandLogo';

interface ProgressBarProps {
  currentStep: number;
  steps: string[];
  isVisible: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ currentStep, steps, isVisible }) => {
  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/70 dark:bg-slate-950/75 backdrop-blur-[10px]"
    >
      <div className="pointer-events-none absolute inset-0 z-0">
        {[...Array(36)].map((_, index) => (
          <motion.span
            key={index}
            className="absolute rounded-full"
            style={{
              width: `${Math.random() * 4 + 1.5}px`,
              height: `${Math.random() * 4 + 1.5}px`,
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              background: `rgba(var(--brand-secondary-rgb), ${0.35 + Math.random() * 0.5})`,
              boxShadow: `0 0 ${6 + Math.random() * 10}px rgba(var(--brand-accent-rgb), 0.8)`,
              opacity: 0.8,
            }}
            animate={{
              y: [0, Math.random() * 16 - 8, 0],
              x: [0, Math.random() * 24 - 12, 0],
              opacity: [0.65, 1, 0.65],
            }}
            transition={{
              duration: 5 + Math.random() * 5,
              repeat: Infinity,
              ease: 'easeInOut',
              delay: Math.random() * 3,
            }}
          />
        ))}
      </div>

      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="relative z-10 max-w-lg w-full mx-6 p-8 rounded-3xl border border-slate-200/50 dark:border-slate-800/40 bg-white/82 dark:bg-slate-900/78 backdrop-blur-3xl shadow-[0_30px_80px_-35px_rgba(15,23,42,0.45)] pointer-events-auto"
      >
        <div className="text-center">
          {/* Branded Logo Animation */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="flex justify-center mb-8"
          >
            <motion.div
              animate={{
                scale: [1, 1.05, 1],
                rotateY: [0, 5, -5, 0]
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              <BrandLogo variant="icon" size="lg" />
            </motion.div>
          </motion.div>

          {/* Progress Title */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="mb-8"
          >
            <h3 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent mb-2">
              AgentVerse Processing
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">
              Please wait while we orchestrate your agents...
            </p>
          </motion.div>

          {/* Progress Steps */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="space-y-3"
          >
            {steps.map((step, index) => {
              const isCompleted = index < currentStep;
              const isCurrent = index === currentStep;
              const isPending = index > currentStep;

              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + index * 0.1, duration: 0.4 }}
                  className={`flex items-center justify-between p-4 rounded-2xl transition-all duration-300 border backdrop-blur-sm ${
                    isCompleted
                      ? 'bg-gradient-to-r from-emerald-50 to-green-50 dark:from-emerald-900/30 dark:to-green-900/30 text-emerald-700 dark:text-emerald-300 border-emerald-200/50 dark:border-emerald-700/50 shadow-sm'
                      : isCurrent
                      ? 'bg-white/85 dark:bg-slate-900/70 text-slate-800 dark:text-slate-200 shadow-lg'
                      : 'bg-slate-50/80 dark:bg-slate-700/50 text-slate-500 dark:text-slate-400 border-slate-200/30 dark:border-slate-600/30'
                  }`}
                  style={
                    isCurrent
                      ? {
                          borderColor: 'rgba(var(--brand-primary-rgb),0.35)',
                          boxShadow: '0 20px 45px -25px rgba(var(--brand-primary-rgb),0.4)',
                          background: 'linear-gradient(135deg, rgba(var(--brand-primary-rgb),0.15) 0%, rgba(var(--brand-secondary-rgb),0.12) 100%)',
                        }
                      : undefined
                  }
                >
                  <span className="font-semibold text-sm">{step}</span>

                  <div className="flex items-center">
                    {isCompleted && (
                      <motion.div
                        initial={{ scale: 0, rotate: -180 }}
                        animate={{ scale: 1, rotate: 0 }}
                        transition={{ type: "spring", stiffness: 200, damping: 10 }}
                        className="w-6 h-6 bg-gradient-to-br from-emerald-500 to-green-600 rounded-full flex items-center justify-center shadow-lg"
                      >
                        <CheckIcon className="w-4 h-4 text-white" />
                      </motion.div>
                    )}

                    {isCurrent && (
                      <motion.div
                        animate={{
                          scale: [1, 1.3, 1],
                          rotate: [0, 180, 360]
                        }}
                        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                        className="w-5 h-5 rounded-full shadow-lg"
                        style={{ background: 'linear-gradient(135deg, rgba(var(--brand-primary-rgb),0.95) 0%, rgba(var(--brand-secondary-rgb),0.95) 100%)' }}
                      />
                    )}

                    {isPending && (
                      <div className="w-4 h-4 bg-slate-300 dark:bg-slate-600 rounded-full opacity-50" />
                    )}
                  </div>
                </motion.div>
              );
            })}
          </motion.div>

          {/* Current Step Description */}
          {currentStep < steps.length && (
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="mt-6 p-4 rounded-2xl border backdrop-blur-sm"
              style={{
                background: 'linear-gradient(135deg, rgba(var(--brand-primary-rgb),0.16) 0%, rgba(var(--brand-secondary-rgb),0.14) 100%)',
                borderColor: 'rgba(var(--brand-primary-rgb),0.28)',
              }}
            >
              <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">
                <span className="font-semibold" style={{ color: 'var(--brand-primary)' }}>Processing:</span> {steps[currentStep]}...
              </p>

              {/* Progress Bar */}
              <div className="mt-3 w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: '100%' }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                  className="h-full rounded-full"
                  style={{ background: 'linear-gradient(135deg, rgba(var(--brand-primary-rgb),1) 0%, rgba(var(--brand-secondary-rgb),1) 100%)' }}
                />
              </div>
            </motion.div>
          )}

          {/* Completion Message */}
          {currentStep >= steps.length && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="mt-6 p-4 bg-gradient-to-r from-emerald-50 to-green-50 dark:from-emerald-900/30 dark:to-green-900/30 rounded-2xl border border-emerald-200/50 dark:border-emerald-700/50"
            >
              <div className="flex items-center justify-center space-x-2">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 200, damping: 10 }}
                  className="w-6 h-6 bg-gradient-to-br from-emerald-500 to-green-600 rounded-full flex items-center justify-center"
                >
                  <CheckIcon className="w-4 h-4 text-white" />
                </motion.div>
                <span className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">
                  Process completed successfully!
                </span>
              </div>
            </motion.div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

// Hook for managing progress steps
export const useProgressSteps = (steps: string[]) => {
  const [currentStep, setCurrentStep] = React.useState(-1);
  const [isVisible, setIsVisible] = React.useState(false);

  const startProgress = () => {
    setCurrentStep(0);
    setIsVisible(true);
  };

  const nextStep = () => {
    setCurrentStep(prev => Math.min(prev + 1, steps.length - 1));
  };

  const completeProgress = () => {
    setCurrentStep(steps.length);
    setTimeout(() => {
      setIsVisible(false);
      setCurrentStep(-1);
    }, 1000); // Show completion for 1 second
  };

  const hideProgress = () => {
    setIsVisible(false);
    setCurrentStep(-1);
  };

  return {
    currentStep,
    isVisible,
    startProgress,
    nextStep,
    completeProgress,
    hideProgress,
  };
};
