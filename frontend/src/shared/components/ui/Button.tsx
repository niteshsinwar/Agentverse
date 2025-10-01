/**
 * Button Component
 * Professional, accessible button component with AgentVerse branding
 */

import React from 'react';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';
import type { BaseComponentProps } from '../../types/common';

export interface ButtonProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ComponentType<{ className?: string }>;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'submit' | 'reset';
}

const buttonVariants = {
  primary: 'av-btn-primary text-white shadow-lg hover:shadow-xl',
  secondary: 'av-btn-secondary',
  outline: 'border border-violet-300 text-violet-600 bg-transparent hover:bg-violet-50 dark:border-violet-600 dark:text-violet-400 dark:hover:bg-violet-950',
  ghost: 'text-violet-600 bg-transparent hover:bg-violet-50 dark:text-violet-400 dark:hover:bg-violet-950',
  danger: 'bg-red-500 text-white border-red-500 hover:bg-red-600 dark:bg-red-600 dark:hover:bg-red-700',
};

const sizeVariants = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      disabled = false,
      loading = false,
      icon: Icon,
      iconPosition = 'left',
      fullWidth = false,
      children,
      className,
      onClick,
      type = 'button',
      testId,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
      if (!isDisabled && onClick) {
        onClick(event);
      }
    };

    return (
      <motion.button
        ref={ref}
        type={type}
        disabled={isDisabled}
        onClick={handleClick}
        data-testid={testId}
        whileTap={!isDisabled ? { scale: 0.98 } : undefined}
        className={clsx(
          // Base styles
          'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900',

          // Variant styles
          buttonVariants[variant],

          // Size styles
          sizeVariants[size],

          // State styles
          {
            'w-full': fullWidth,
            'opacity-50 cursor-not-allowed': isDisabled,
            'cursor-pointer': !isDisabled,
          },

          className
        )}
        {...props}
      >
        {loading ? (
          <>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="w-4 h-4 border-2 border-current border-t-transparent rounded-full"
            />
            {children && <span>Loading...</span>}
          </>
        ) : (
          <>
            {Icon && iconPosition === 'left' && (
              <Icon className={clsx('flex-shrink-0', size === 'sm' ? 'w-3 h-3' : 'w-4 h-4')} />
            )}
            {children}
            {Icon && iconPosition === 'right' && (
              <Icon className={clsx('flex-shrink-0', size === 'sm' ? 'w-3 h-3' : 'w-4 h-4')} />
            )}
          </>
        )}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';