import { SparklesIcon, QuestionMarkCircleIcon } from '@heroicons/react/24/outline';
import { useAppStore } from '@/lib/stores/app';

const currentYear = new Date().getFullYear();

export const AppFooter = () => {
  const { setCommunityCenterOpen, setHelpOpen } = useAppStore();

  return (
    <footer className="border-t border-violet-200/30 dark:border-violet-800/30 bg-white/70 dark:bg-slate-900/70 backdrop-blur-md py-2">
      <div className="flex items-center justify-between px-4">
        <span className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
          © {currentYear} AInovate Labs. All rights reserved.
        </span>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setHelpOpen(true)}
            className="flex items-center space-x-2 px-3 py-1.5 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white rounded-lg text-xs font-medium transition-all transform hover:scale-105"
          >
            <QuestionMarkCircleIcon className="w-4 h-4" />
            <span>Help & Docs</span>
          </button>
          <button
            onClick={() => setCommunityCenterOpen(true)}
            className="flex items-center space-x-2 px-3 py-1.5 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-lg text-xs font-medium transition-all transform hover:scale-105"
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
