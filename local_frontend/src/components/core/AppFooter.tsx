import { SparklesIcon, QuestionMarkCircleIcon } from '@heroicons/react/24/outline';
import { useAppStore } from '@/lib/stores/app';

const currentYear = new Date().getFullYear();

export const AppFooter = () => {
  const { setCommunityCenterOpen, setHelpOpen } = useAppStore();

  return (
    <footer className="border-t border-transparent brand-surface backdrop-blur-xl py-3">
      <div className="flex items-center justify-between px-4">
        <span className="text-xs sm:text-sm text-slate-500 dark:text-slate-300">
          © {currentYear} AInovate Labs. All rights reserved.
        </span>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setHelpOpen(true)}
            className="flex items-center space-x-2 rounded-lg px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 brand-glass transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
          >
            <QuestionMarkCircleIcon className="w-4 h-4" />
            <span>Help & Docs</span>
          </button>
          <button
            onClick={() => setCommunityCenterOpen(true)}
            className="flex items-center space-x-2 rounded-lg px-3 py-1.5 text-xs font-medium brand-cta transition-all duration-200 hover:-translate-y-0.5"
          >
            <SparklesIcon className="w-4 h-4" />
            <span>Community Center</span>
          </button>
        </div>
      </div>
    </footer>
  );
};

AppFooter.displayName = 'AppFooter';
