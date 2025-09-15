import React from 'react';
import { motion } from 'framer-motion';
import { CogIcon, CheckIcon } from '@heroicons/react/24/outline';

interface ProgressBarProps {
  currentStep: number;
  steps: string[];
  isVisible: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ currentStep, steps, isVisible }) => {
  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div className="bg-white dark:bg-gray-800 rounded-lg p-8 max-w-md w-full mx-4 shadow-2xl">
        <div className="text-center">
          {/* Animated Gear */}
          <div className="flex justify-center mb-6">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="w-16 h-16 text-blue-600"
            >
              <CogIcon className="w-full h-full" />
            </motion.div>
          </div>

          {/* Progress Steps */}
          <div className="space-y-4">
            {steps.map((step, index) => {
              const isCompleted = index < currentStep;
              const isCurrent = index === currentStep;
              const isPending = index > currentStep;

              return (
                <div
                  key={index}
                  className={`flex items-center justify-between p-3 rounded-lg transition-all duration-300 ${
                    isCompleted
                      ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                      : isCurrent
                      ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                      : 'bg-gray-50 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                  }`}
                >
                  <span className="font-medium">{step}</span>

                  <div className="flex items-center">
                    {isCompleted && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="w-5 h-5 text-green-600"
                      >
                        <CheckIcon className="w-full h-full" />
                      </motion.div>
                    )}

                    {isCurrent && (
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 1, repeat: Infinity }}
                        className="w-3 h-3 bg-blue-600 rounded-full"
                      />
                    )}

                    {isPending && (
                      <div className="w-3 h-3 bg-gray-300 dark:bg-gray-600 rounded-full" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Current Step Description */}
          {currentStep < steps.length && (
            <motion.p
              key={currentStep}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-4 text-sm text-gray-600 dark:text-gray-400"
            >
              {steps[currentStep]}...
            </motion.p>
          )}
        </div>
      </div>
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