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
        return 'brand-gradient text-white border border-transparent shadow-lg hover:opacity-95 hover:shadow-xl disabled:opacity-60 disabled:cursor-not-allowed';
      case 'secondary':
        return 'bg-gradient-to-r from-slate-100/90 via-sky-100/80 to-cyan-100/80 dark:from-slate-900/40 dark:via-sky-900/35 dark:to-cyan-900/35 text-slate-800 dark:text-slate-200 border border-slate-200/60 dark:border-sky-800/40 hover:from-slate-100 hover:to-sky-100 dark:hover:from-slate-900/55 dark:hover:to-sky-900/45';
      case 'outline':
        return 'bg-transparent text-sky-600 dark:text-sky-300 border border-sky-400/70 dark:border-sky-600 hover:bg-sky-50 dark:hover:bg-sky-900/20';
      case 'ghost':
        return 'bg-transparent text-sky-600 dark:text-sky-300 hover:bg-sky-50 dark:hover:bg-sky-900/20';
      default:
        return 'brand-gradient text-white';
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
        focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2
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
        return 'brand-surface backdrop-blur-xl border border-transparent shadow-lg';
      case 'gradient':
        return 'bg-gradient-to-br from-slate-100/85 via-sky-100/70 to-cyan-100/70 dark:from-slate-900/35 dark:via-sky-900/30 dark:to-cyan-900/30 border border-slate-200/50 dark:border-sky-800/40 shadow-lg';
      default:
        return 'brand-shell shadow-sm';
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
        ${hover ? 'hover:shadow-xl hover:shadow-sky-500/10' : ''}
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
        return 'brand-gradient text-white';
      case 'secondary':
        return 'bg-gradient-to-r from-slate-100 to-sky-100 dark:from-slate-900/40 dark:to-sky-900/35 text-slate-800 dark:text-slate-200 border border-slate-200/60 dark:border-sky-700/40';
      case 'success':
        return 'bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/30 dark:to-teal-900/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200/50 dark:border-emerald-700/50';
      case 'warning':
        return 'bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/30 text-amber-700 dark:text-amber-300 border border-amber-200/50 dark:border-amber-700/50';
      case 'error':
        return 'bg-gradient-to-r from-red-50 to-rose-50 dark:from-red-900/30 dark:to-rose-900/30 text-red-700 dark:text-rose-300 border border-red-200/50 dark:border-rose-700/50';
      case 'info':
        return 'bg-gradient-to-r from-sky-50 to-cyan-50 dark:from-sky-900/30 dark:to-cyan-900/30 text-sky-700 dark:text-cyan-300 border border-sky-200/50 dark:border-cyan-700/50';
      default:
        return 'brand-gradient text-white';
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
