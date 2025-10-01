/**
 * Input Component
 * Professional, accessible input component with AgentVerse branding
 */

import React from 'react';
import { clsx } from 'clsx';
import type { InputProps } from '../../types/common';

export interface ExtendedInputProps extends InputProps {
  icon?: React.ComponentType<{ className?: string }>;
  iconPosition?: 'left' | 'right';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
}

const sizeVariants = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-4 py-3 text-base',
};

export const Input = React.forwardRef<HTMLInputElement, ExtendedInputProps>(
  (
    {
      label,
      placeholder,
      value,
      onChange,
      error,
      disabled = false,
      required = false,
      type = 'text',
      icon: Icon,
      iconPosition = 'left',
      size = 'md',
      fullWidth = true,
      className,
      testId,
      ...props
    },
    ref
  ) => {
    const inputId = React.useId();

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      if (onChange) {
        onChange(event.target.value);
      }
    };

    return (
      <div className={clsx('flex flex-col', { 'w-full': fullWidth }, className)}>
        {label && (
          <label
            htmlFor={inputId}
            className="mb-1.5 text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}

        <div className="relative">
          {Icon && iconPosition === 'left' && (
            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <Icon className="w-4 h-4 text-slate-400 dark:text-slate-500" />
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            type={type}
            value={value}
            onChange={handleChange}
            placeholder={placeholder}
            disabled={disabled}
            required={required}
            data-testid={testId}
            className={clsx(
              // Base styles
              'block w-full rounded-lg border transition-all duration-200 placeholder:text-slate-400 dark:placeholder:text-slate-500',

              // Size styles
              sizeVariants[size],

              // Icon padding
              {
                'pl-10': Icon && iconPosition === 'left',
                'pr-10': Icon && iconPosition === 'right',
              },

              // State styles
              {
                // Normal state
                'border-slate-300 bg-white text-slate-900 shadow-sm focus:border-violet-500 focus:ring-1 focus:ring-violet-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:focus:border-violet-400':
                  !error && !disabled,

                // Error state
                'border-red-300 bg-red-50 text-red-900 placeholder:text-red-400 focus:border-red-500 focus:ring-1 focus:ring-red-500 dark:border-red-600 dark:bg-red-950/20 dark:text-red-100':
                  error && !disabled,

                // Disabled state
                'border-slate-200 bg-slate-50 text-slate-500 cursor-not-allowed dark:border-slate-700 dark:bg-slate-900 dark:text-slate-600':
                  disabled,
              }
            )}
            {...props}
          />

          {Icon && iconPosition === 'right' && (
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
              <Icon className="w-4 h-4 text-slate-400 dark:text-slate-500" />
            </div>
          )}
        </div>

        {error && (
          <p className="mt-1.5 text-sm text-red-600 dark:text-red-400" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';