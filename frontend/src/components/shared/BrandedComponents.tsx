import React from 'react';
import { motion } from 'framer-motion';

// Branded Button Component
interface BrandedButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const BrandedButton: React.FC<BrandedButtonProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  onClick,
  disabled = false,
  loading = false,
  className = '',
  type = 'button'
}) => {
  const getSizeClasses = () => {
    switch (size) {
      case 'sm': return 'px-3 py-2 text-sm';
      case 'md': return 'px-4 py-2.5 text-sm';
      case 'lg': return 'px-6 py-3 text-base';
      default: return 'px-4 py-2.5 text-sm';
    }
  };

  const getVariantClasses = () => {
    switch (variant) {
      case 'primary':
        return 'bg-gradient-to-r from-violet-500 to-indigo-600 text-white border border-violet-400/30 shadow-lg hover:from-violet-600 hover:to-indigo-700 hover:shadow-xl disabled:from-violet-300 disabled:to-indigo-400';
      case 'secondary':
        return 'bg-gradient-to-r from-violet-50 to-indigo-50 dark:from-violet-900/30 dark:to-indigo-900/30 text-violet-700 dark:text-violet-300 border border-violet-200/50 dark:border-violet-700/50 hover:from-violet-100 hover:to-indigo-100 dark:hover:from-violet-900/50 dark:hover:to-indigo-900/50';
      case 'outline':
        return 'bg-transparent text-violet-600 dark:text-violet-400 border border-violet-300 dark:border-violet-600 hover:bg-violet-50 dark:hover:bg-violet-900/20';
      case 'ghost':
        return 'bg-transparent text-violet-600 dark:text-violet-400 hover:bg-violet-50 dark:hover:bg-violet-900/20';
      default:
        return 'bg-gradient-to-r from-violet-500 to-indigo-600 text-white';
    }
  };

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      whileHover={{ scale: disabled ? 1 : 1.02 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      className={`
        ${getSizeClasses()}
        ${getVariantClasses()}
        font-semibold rounded-xl transition-all duration-200
        disabled:opacity-50 disabled:cursor-not-allowed
        focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2
        ${className}
      `}
    >
      {loading ? (
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
          <span>Loading...</span>
        </div>
      ) : (
        children
      )}
    </motion.button>
  );
};

// Branded Card Component
interface BrandedCardProps {
  children: React.ReactNode;
  variant?: 'default' | 'glass' | 'gradient';
  hover?: boolean;
  className?: string;
}

export const BrandedCard: React.FC<BrandedCardProps> = ({
  children,
  variant = 'default',
  hover = false,
  className = ''
}) => {
  const getVariantClasses = () => {
    switch (variant) {
      case 'glass':
        return 'bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-violet-200/30 dark:border-violet-800/30 shadow-lg';
      case 'gradient':
        return 'bg-gradient-to-br from-violet-50/80 to-indigo-50/80 dark:from-violet-900/20 dark:to-indigo-900/20 border border-violet-200/50 dark:border-violet-700/50 shadow-lg';
      default:
        return 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={hover ? { y: -2, scale: 1.01 } : {}}
      className={`
        ${getVariantClasses()}
        rounded-2xl p-6 transition-all duration-300
        ${hover ? 'hover:shadow-xl hover:shadow-violet-500/10' : ''}
        ${className}
      `}
    >
      {children}
    </motion.div>
  );
};

// Branded Badge Component
interface BrandedBadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const BrandedBadge: React.FC<BrandedBadgeProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className = ''
}) => {
  const getSizeClasses = () => {
    switch (size) {
      case 'sm': return 'px-2 py-1 text-xs';
      case 'md': return 'px-3 py-1.5 text-sm';
      case 'lg': return 'px-4 py-2 text-base';
      default: return 'px-3 py-1.5 text-sm';
    }
  };

  const getVariantClasses = () => {
    switch (variant) {
      case 'primary':
        return 'bg-gradient-to-r from-violet-500 to-indigo-600 text-white';
      case 'secondary':
        return 'bg-gradient-to-r from-violet-50 to-indigo-50 dark:from-violet-900/30 dark:to-indigo-900/30 text-violet-700 dark:text-violet-300 border border-violet-200/50 dark:border-violet-700/50';
      case 'success':
        return 'bg-gradient-to-r from-emerald-50 to-green-50 dark:from-emerald-900/30 dark:to-green-900/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200/50 dark:border-emerald-700/50';
      case 'warning':
        return 'bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/30 text-amber-700 dark:text-amber-300 border border-amber-200/50 dark:border-amber-700/50';
      case 'error':
        return 'bg-gradient-to-r from-red-50 to-rose-50 dark:from-red-900/30 dark:to-rose-900/30 text-red-700 dark:text-red-300 border border-red-200/50 dark:border-red-700/50';
      case 'info':
        return 'bg-gradient-to-r from-cyan-50 to-blue-50 dark:from-cyan-900/30 dark:to-blue-900/30 text-cyan-700 dark:text-cyan-300 border border-cyan-200/50 dark:border-cyan-700/50';
      default:
        return 'bg-gradient-to-r from-violet-500 to-indigo-600 text-white';
    }
  };

  return (
    <motion.span
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`
        ${getSizeClasses()}
        ${getVariantClasses()}
        inline-flex items-center font-semibold rounded-lg
        ${className}
      `}
    >
      {children}
    </motion.span>
  );
};

// Branded Status Indicator
interface BrandedStatusProps {
  status: 'online' | 'busy' | 'offline' | 'thinking';
  size?: 'sm' | 'md' | 'lg';
  showPulse?: boolean;
  className?: string;
}

export const BrandedStatus: React.FC<BrandedStatusProps> = ({
  status,
  size = 'md',
  showPulse = true,
  className = ''
}) => {
  const getSizeClasses = () => {
    switch (size) {
      case 'sm': return 'w-2 h-2';
      case 'md': return 'w-3 h-3';
      case 'lg': return 'w-4 h-4';
      default: return 'w-3 h-3';
    }
  };

  const getStatusClasses = () => {
    const baseClasses = 'rounded-full';
    const pulseClasses = showPulse ? 'animate-pulse' : '';

    switch (status) {
      case 'online':
        return `${baseClasses} av-status-online ${pulseClasses}`;
      case 'busy':
        return `${baseClasses} av-status-busy ${pulseClasses}`;
      case 'thinking':
        return `${baseClasses} av-status-thinking ${pulseClasses}`;
      case 'offline':
      default:
        return `${baseClasses} av-status-offline`;
    }
  };

  return (
    <div
      className={`
        ${getSizeClasses()}
        ${getStatusClasses()}
        ${className}
      `}
    />
  );
};