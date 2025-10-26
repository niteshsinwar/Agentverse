import { ReactNode } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { PanelSize, getPanelSize } from './SlidingPanel.sizes';

interface SlidingPanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  meta?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  size?: PanelSize; // Use predefined sizes from PANEL_SIZES
  overlayClassName?: string;
  containerClassName?: string;
  maxWidthClassName?: string; // Overrides size preset if provided
  heightClassName?: string; // Overrides size preset if provided
  headerClassName?: string;
  headerBackgroundClassName?: string | null;
  contentClassName?: string;
  showCloseButton?: boolean;
  closeButtonClassName?: string;
  disableBackdropClose?: boolean;
}

const overlayBase =
  'fixed inset-0 bg-gradient-to-br from-slate-900/80 via-violet-900/50 to-cyan-900/30 backdrop-blur-sm flex items-center justify-center p-4 z-[60]';

const containerBase =
  'relative bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl rounded-3xl border border-violet-200/30 dark:border-violet-800/30 flex flex-col shadow-2xl';

const headerBase =
  'relative flex items-center justify-between px-6 py-4 border-b border-violet-200/30 dark:border-violet-800/30';

const defaultHeaderBackground =
  'absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-pink-500/5 rounded-t-3xl';

const closeButtonBase =
  'p-2 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 transition-colors';

export const SlidingPanel = ({
  isOpen,
  onClose,
  title,
  subtitle,
  icon,
  meta,
  actions,
  children,
  size,
  overlayClassName,
  containerClassName,
  maxWidthClassName,
  heightClassName,
  headerClassName,
  headerBackgroundClassName = defaultHeaderBackground,
  contentClassName,
  showCloseButton = true,
  closeButtonClassName,
  disableBackdropClose = false,
}: SlidingPanelProps) => {
  // Apply size preset if provided, otherwise use explicit props or defaults
  const sizeConfig = size ? getPanelSize(size) : undefined;
  const finalMaxWidth = maxWidthClassName || sizeConfig?.maxWidthClassName || 'w-[95vw] max-w-[1600px]';
  const finalHeight = heightClassName || sizeConfig?.heightClassName || 'h-[90vh]';

  const handleOverlayClick = () => {
    if (disableBackdropClose) {
      return;
    }
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          key="panel-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className={clsx(overlayBase, overlayClassName)}
          onClick={handleOverlayClick}
        >
          <motion.div
            key="panel-container"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            onClick={(event) => event.stopPropagation()}
            className={clsx(containerBase, finalMaxWidth, finalHeight, containerClassName)}
          >
            <div className={clsx(headerBase, headerClassName)}>
              {headerBackgroundClassName ? (
                <div className={clsx(headerBackgroundClassName)} aria-hidden />
              ) : null}

              <div className="relative flex items-center space-x-4">
                {icon ? <div className="flex-shrink-0">{icon}</div> : null}
                <div>
                  <h2 className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">
                    {title}
                  </h2>
                  {subtitle ? (
                    <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">{subtitle}</p>
                  ) : null}
                </div>
                {meta ? <div className="ml-3">{meta}</div> : null}
              </div>

              <div className="relative flex items-center gap-2">
                {actions}
                {showCloseButton ? (
                  <button
                    type="button"
                    onClick={onClose}
                    className={clsx(closeButtonBase, closeButtonClassName)}
                    aria-label="Close panel"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                ) : null}
              </div>
            </div>

            <div className={clsx('relative flex-1 min-h-0', contentClassName)}>{children}</div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

SlidingPanel.displayName = 'SlidingPanel';
