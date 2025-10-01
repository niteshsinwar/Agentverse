/**
 * Loading Component
 * Professional loading indicators with AgentVerse branding
 */

import React from 'react';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';
import type { BaseComponentProps } from '../../types/common';

export interface LoadingProps extends BaseComponentProps {
  variant?: 'spinner' | 'dots' | 'pulse' | 'skeleton';
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  fullScreen?: boolean;
}

const Spinner: React.FC<{ size: LoadingProps['size'] }> = ({ size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      className={clsx(
        'border-2 border-violet-200 border-t-violet-500 rounded-full dark:border-violet-800 dark:border-t-violet-400',
        sizeClasses[size]
      )}
    />
  );
};

const Dots: React.FC<{ size: LoadingProps['size'] }> = ({ size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-1 h-1',
    md: 'w-2 h-2',
    lg: 'w-3 h-3',
  };

  const dotVariants = {
    initial: { scale: 0.8, opacity: 0.5 },
    animate: { scale: 1.2, opacity: 1 },
  };

  return (
    <div className="flex space-x-1">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          variants={dotVariants}
          initial="initial"
          animate="animate"
          transition={{
            duration: 0.6,
            repeat: Infinity,
            repeatType: 'reverse',
            delay: i * 0.15,
          }}
          className={clsx(
            'bg-violet-500 rounded-full dark:bg-violet-400',
            sizeClasses[size]
          )}
        />
      ))}
    </div>
  );
};

const Pulse: React.FC<{ size: LoadingProps['size'] }> = ({ size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <motion.div
      animate={{
        scale: [1, 1.2, 1],
        opacity: [0.5, 1, 0.5],
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
      className={clsx(
        'bg-violet-500 rounded-full dark:bg-violet-400',
        sizeClasses[size]
      )}
    />
  );
};

const Skeleton: React.FC<{ size: LoadingProps['size'] }> = ({ size = 'md' }) => {
  const heightClasses = {
    sm: 'h-4',
    md: 'h-6',
    lg: 'h-8',
  };

  return (
    <div className="space-y-2 w-full">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          animate={{
            opacity: [0.3, 0.6, 0.3],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            delay: i * 0.2,
          }}
          className={clsx(
            'bg-slate-200 rounded dark:bg-slate-700',
            heightClasses[size],
            i === 2 ? 'w-3/4' : 'w-full'
          )}
        />
      ))}
    </div>
  );
};

export const Loading: React.FC<LoadingProps> = ({
  variant = 'spinner',
  size = 'md',
  text,
  fullScreen = false,
  className,
  children,
  testId,
}) => {
  const content = (
    <div
      className={clsx(
        'flex flex-col items-center justify-center gap-3',
        className
      )}
      data-testid={testId}
    >
      {variant === 'spinner' && <Spinner size={size} />}
      {variant === 'dots' && <Dots size={size} />}
      {variant === 'pulse' && <Pulse size={size} />}
      {variant === 'skeleton' && <Skeleton size={size} />}

      {text && (
        <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">
          {text}
        </p>
      )}

      {children}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm flex items-center justify-center">
        {content}
      </div>
    );
  }

  return content;
};