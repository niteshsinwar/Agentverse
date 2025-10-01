import React from 'react';

interface BrandLogoProps {
  variant?: 'full' | 'icon' | 'horizontal';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  showText?: boolean;
  theme?: 'light' | 'dark' | 'auto';
}

export const BrandLogo: React.FC<BrandLogoProps> = ({
  variant = 'horizontal',
  size = 'md',
  className = '',
  showText = true,
  theme = 'auto'
}) => {
  const getSizeClasses = () => {
    switch (size) {
      case 'sm': return variant === 'horizontal' ? 'h-8' : 'h-8 w-8';
      case 'md': return variant === 'horizontal' ? 'h-10' : 'h-10 w-10';
      case 'lg': return variant === 'horizontal' ? 'h-12' : 'h-12 w-12';
      case 'xl': return variant === 'horizontal' ? 'h-16' : 'h-16 w-16';
      default: return variant === 'horizontal' ? 'h-10' : 'h-10 w-10';
    }
  };

  const getTextSize = () => {
    switch (size) {
      case 'sm': return 'text-lg';
      case 'md': return 'text-xl';
      case 'lg': return 'text-2xl';
      case 'xl': return 'text-3xl';
      default: return 'text-xl';
    }
  };

  // AgentVerse Icon SVG Component
  const AgentVerseIcon = ({ className: iconClassName = '' }: { className?: string }) => (
    <svg
      viewBox="0 0 200 200"
      className={`${iconClassName}`}
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="primaryGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#6366f1" stopOpacity="1" />
          <stop offset="35%" stopColor="#8b5cf6" stopOpacity="1" />
          <stop offset="70%" stopColor="#ec4899" stopOpacity="1" />
          <stop offset="100%" stopColor="#f97316" stopOpacity="1" />
        </linearGradient>
        <linearGradient id="accentGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#06b6d4" stopOpacity="1" />
          <stop offset="50%" stopColor="#3b82f6" stopOpacity="1" />
          <stop offset="100%" stopColor="#6366f1" stopOpacity="1" />
        </linearGradient>
        <linearGradient id="networkGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#10b981" stopOpacity="0.9" />
          <stop offset="50%" stopColor="#06b6d4" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.9" />
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      {/* Background circle */}
      <circle cx="100" cy="100" r="95" fill="url(#primaryGradient)" opacity="0.05" />

      {/* Outer rings */}
      <circle cx="100" cy="100" r="85" stroke="url(#primaryGradient)" strokeWidth="2" fill="none" opacity="0.3" />
      <circle cx="100" cy="100" r="75" stroke="url(#accentGradient)" strokeWidth="1.5" fill="none" opacity="0.2" />

      {/* Central hub */}
      <circle cx="100" cy="100" r="18" fill="url(#primaryGradient)" />
      <circle cx="100" cy="100" r="14" fill="white" opacity="0.9" />
      <circle cx="100" cy="100" r="10" fill="url(#primaryGradient)" />

      {/* Agent nodes */}
      <g transform="translate(100, 50)">
        <circle r="12" fill="url(#accentGradient)" />
        <circle r="9" fill="white" opacity="0.9" />
        <circle r="5" fill="url(#accentGradient)" />
      </g>

      <g transform="translate(135, 65)">
        <circle r="10" fill="url(#networkGradient)" />
        <circle r="7" fill="white" opacity="0.9" />
        <circle r="4" fill="url(#networkGradient)" />
      </g>

      <g transform="translate(150, 100)">
        <circle r="11" fill="url(#primaryGradient)" />
        <circle r="8" fill="white" opacity="0.9" />
        <circle r="5" fill="url(#primaryGradient)" />
      </g>

      <g transform="translate(135, 135)">
        <circle r="9" fill="url(#accentGradient)" />
        <circle r="6" fill="white" opacity="0.9" />
        <circle r="3" fill="url(#accentGradient)" />
      </g>

      <g transform="translate(100, 150)">
        <circle r="10" fill="url(#networkGradient)" />
        <circle r="7" fill="white" opacity="0.9" />
        <circle r="4" fill="url(#networkGradient)" />
      </g>

      <g transform="translate(65, 135)">
        <circle r="11" fill="url(#primaryGradient)" />
        <circle r="8" fill="white" opacity="0.9" />
        <circle r="5" fill="url(#primaryGradient)" />
      </g>

      <g transform="translate(50, 100)">
        <circle r="9" fill="url(#accentGradient)" />
        <circle r="6" fill="white" opacity="0.9" />
        <circle r="3" fill="url(#accentGradient)" />
      </g>

      <g transform="translate(65, 65)">
        <circle r="10" fill="url(#networkGradient)" />
        <circle r="7" fill="white" opacity="0.9" />
        <circle r="4" fill="url(#networkGradient)" />
      </g>

      {/* Connection lines */}
      <g stroke="url(#networkGradient)" strokeWidth="1.5" opacity="0.4" filter="url(#glow)">
        <line x1="100" y1="100" x2="100" y2="62" />
        <line x1="100" y1="100" x2="125" y2="75" />
        <line x1="100" y1="100" x2="139" y2="100" />
        <line x1="100" y1="100" x2="125" y2="125" />
        <line x1="100" y1="100" x2="100" y2="138" />
        <line x1="100" y1="100" x2="75" y2="125" />
        <line x1="100" y1="100" x2="61" y2="100" />
        <line x1="100" y1="100" x2="75" y2="75" />
      </g>
    </svg>
  );

  if (variant === 'icon') {
    return (
      <div className={`flex items-center justify-center ${getSizeClasses()} ${className}`}>
        <AgentVerseIcon className="w-full h-full" />
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className={getSizeClasses()}>
        <AgentVerseIcon className="w-full h-full" />
      </div>
      {showText && (
        <div className="flex flex-col">
          <span className={`font-bold bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent ${getTextSize()}`}>
            AgentVerse
          </span>
          {size !== 'sm' && (
            <span className="text-xs text-gray-500 dark:text-gray-400 font-medium tracking-wider uppercase">
              Multiverse of Agents
            </span>
          )}
        </div>
      )}
    </div>
  );
};