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
        'relative brand-surface backdrop-blur-xl border border-transparent shadow-lg',
        className,
      )}
    >
      <div className="pointer-events-none absolute inset-0 brand-gradient-soft opacity-35" />
      <div className={clsx('relative px-6 py-4', innerClassName)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              {leading}
              <div>
                <h1 className="text-xl font-semibold text-slate-900 dark:text-white">
                  {title}
                </h1>
                {subtitle ? (
                  <p className="text-sm font-medium text-slate-500 dark:text-slate-300">
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
                className="flex items-center space-x-2 rounded-xl px-4 py-2 text-sm font-semibold text-slate-600 dark:text-slate-200 brand-glass transition-all duration-200 shadow-sm hover:-translate-y-0.5 hover:shadow-md"
              >
                {commandIcon}
                {commandHint ? <span className="font-medium">{commandHint}</span> : null}
              </motion.button>
            ) : null}

            {hasMenu ? (
              <Menu as="div" className="relative">
                <Menu.Button className="brand-glass p-2.5 text-slate-500 hover:text-sky-600 dark:text-slate-300 dark:hover:text-sky-300 rounded-xl transition-all duration-200 shadow-sm hover:-translate-y-0.5">
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
                  <Menu.Items className="absolute right-0 top-full mt-2 w-56 brand-surface backdrop-blur-xl rounded-2xl shadow-2xl border border-transparent z-[9999]">
                    <div className="py-1">
                      {menuItems?.map((item) => (
                        <Menu.Item key={item.key}>
                          {({ active }) => (
                            <button
                              onClick={item.onClick}
                              className={clsx(
                                'w-full text-left px-4 py-3 text-sm transition-all duration-200 rounded-xl mx-2 my-1',
                                active
                                  ? 'brand-gradient text-white shadow-md shadow-sky-500/25'
                                  : 'text-slate-700 dark:text-slate-200 hover:bg-slate-100/70 dark:hover:bg-slate-800/60',
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
