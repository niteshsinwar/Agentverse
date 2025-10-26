import { Fragment, ReactNode } from 'react';
import { motion } from 'framer-motion';
import { Menu, Transition } from '@headlessui/react';
import { CommandLineIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

export interface HeaderMenuItem {
  key: string;
  label: string;
  icon?: ReactNode;
  onClick: () => void;
}

export interface AppHeaderProps {
  title: string;
  subtitle?: string;
  leading?: ReactNode;
  onCommandPalette?: () => void;
  commandIcon?: ReactNode;
  commandHint?: string;
  menuItems?: HeaderMenuItem[];
  menuButtonIcon?: ReactNode;
  rightContent?: ReactNode;
  className?: string;
  innerClassName?: string;
  children?: ReactNode;
}

export const AppHeader = ({
  title,
  subtitle,
  leading,
  onCommandPalette,
  commandIcon = <CommandLineIcon className="w-4 h-4" />,
  commandHint = '⌘K',
  menuItems,
  menuButtonIcon = <Cog6ToothIcon className="w-5 h-5" />,
  rightContent,
  className,
  innerClassName,
  children,
}: AppHeaderProps) => {
  const hasMenu = Array.isArray(menuItems) && menuItems.length > 0;

  return (
    <div
      className={clsx(
        'relative bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-violet-200/30 dark:border-violet-800/30 shadow-lg shadow-violet-500/5',
        className,
      )}
    >
      <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-pink-500/5" />
      <div className={clsx('relative px-6 py-4', innerClassName)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              {leading}
              <div>
                <h1 className="text-xl font-semibold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">
                  {title}
                </h1>
                {subtitle ? (
                  <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">
                    {subtitle}
                  </p>
                ) : null}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {onCommandPalette ? (
              <motion.button
                onClick={onCommandPalette}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center space-x-2 px-4 py-2 text-sm text-slate-600 dark:text-slate-300 bg-white/60 dark:bg-slate-700/60 backdrop-blur-sm rounded-xl border border-violet-200/30 dark:border-violet-800/30 hover:bg-violet-50/80 dark:hover:bg-violet-900/20 transition-all duration-200 shadow-sm"
              >
                {commandIcon}
                {commandHint ? <span className="font-medium">{commandHint}</span> : null}
              </motion.button>
            ) : null}

            {hasMenu ? (
              <Menu as="div" className="relative">
                <Menu.Button className="p-2.5 text-slate-500 hover:text-violet-600 dark:text-slate-400 dark:hover:text-violet-400 bg-white/60 dark:bg-slate-700/60 backdrop-blur-sm rounded-xl border border-violet-200/30 dark:border-violet-800/30 hover:bg-violet-50/80 dark:hover:bg-violet-900/20 transition-all duration-200 shadow-sm">
                  {menuButtonIcon}
                </Menu.Button>
                <Transition
                  as={Fragment}
                  enter="transition duration-100 ease-out"
                  enterFrom="transform scale-95 opacity-0"
                  enterTo="transform scale-100 opacity-100"
                  leave="transition duration-75 ease-in"
                  leaveFrom="transform scale-100 opacity-100"
                  leaveTo="transform scale-95 opacity-0"
                >
                  <Menu.Items className="absolute right-0 top-full mt-2 w-56 bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-violet-200/30 dark:border-violet-800/30 z-[9999]">
                    <div className="py-1">
                      {menuItems?.map((item) => (
                        <Menu.Item key={item.key}>
                          {({ active }) => (
                            <button
                              onClick={item.onClick}
                              className={clsx(
                                'w-full text-left px-4 py-3 text-sm transition-all duration-200 rounded-xl mx-2 my-1',
                                active
                                  ? 'bg-gradient-to-r from-violet-50 to-indigo-50 dark:from-violet-900/30 dark:to-indigo-900/30 text-violet-700 dark:text-violet-300 shadow-sm'
                                  : 'text-slate-700 dark:text-slate-300 hover:bg-violet-50/50 dark:hover:bg-violet-900/20',
                              )}
                            >
                              <div className="flex items-center space-x-2">
                                {item.icon}
                                <span>{item.label}</span>
                              </div>
                            </button>
                          )}
                        </Menu.Item>
                      ))}
                    </div>
                  </Menu.Items>
                </Transition>
              </Menu>
            ) : null}

            {rightContent}
          </div>
        </div>
        {children}
      </div>
    </div>
  );
};

AppHeader.displayName = 'AppHeader';
