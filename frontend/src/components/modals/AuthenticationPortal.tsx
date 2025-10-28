import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  EnvelopeIcon,
  LockClosedIcon,
  UserIcon,
  BuildingOffice2Icon,
} from '@heroicons/react/24/outline';
import { BrandLogo } from '@/components/shared/BrandLogo';
import { useAuthStore, type AccountType } from '@/lib/stores/auth';

interface AuthenticationPortalProps {
  isOpen: boolean;
  onClose: () => void;
}

type AuthMode = 'login' | 'register';

export const AuthenticationPortal: React.FC<AuthenticationPortalProps> = ({ isOpen, onClose }) => {
  const { login } = useAuthStore();

  const [mode, setMode] = useState<AuthMode>('login');
  const [accountType, setAccountType] = useState<AccountType>('individual');
  const [isAdmin, setIsAdmin] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setIsAdmin(false);
    setAccountType('individual');
    setMode('login');
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    login(email, password, accountType, accountType === 'enterprise' && isAdmin);
    resetForm();
    onClose();
  };

  const handleAccountTypeChange = (type: AccountType) => {
    setAccountType(type);
    if (type !== 'enterprise') {
      setIsAdmin(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm"
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            transition={{ type: 'spring', damping: 24, stiffness: 240 }}
            className="fixed inset-0 z-50 flex items-center justify-center px-4 py-10"
          >
            <div className="relative flex w-full max-w-5xl min-h-[640px] flex-col overflow-hidden rounded-[32px] bg-white/92 shadow-[0_40px_160px_rgba(15,23,42,0.35)] ring-1 ring-black/5 backdrop-blur-xl dark:bg-slate-950/90 dark:ring-white/10 lg:flex-row lg:items-stretch">
              <div className="relative flex flex-1 flex-col justify-between overflow-hidden bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 px-10 py-12 text-white">
                <div className="pointer-events-none absolute inset-0 opacity-30">
                  <div className="absolute -left-32 top-12 h-72 w-72 rounded-full bg-cyan-400/50 blur-3xl" />
                  <div className="absolute bottom-12 right-12 h-96 w-96 rounded-full bg-violet-500/40 blur-3xl" />
                </div>

                <div className="relative z-10 flex flex-1 flex-col justify-between">
                  <div className="space-y-5">
                    <BrandLogo variant="horizontal" size="lg" className="drop-shadow-[0_18px_36px_rgba(79,70,229,0.45)]" />
                    <div className="space-y-2 text-sm text-white/80">
                      <p className="text-xs uppercase tracking-[0.35em] text-white/60">Command Access</p>
                      <h1 className="text-3xl font-semibold tracking-tight">Authenticate to continue</h1>
                      <p className="text-xs leading-5 text-white/65">
                        Use your workspace credentials to enter the AgentVerse control console.
                      </p>
                    </div>
                  </div>

                  <div className="mt-8 rounded-2xl border border-white/15 bg-white/10 p-4 text-xs text-white/70 backdrop-blur">
                    Access monitored. Unauthorized usage triggers automated containment.
                  </div>
                </div>
              </div>

              <div className="relative flex flex-1 flex-col justify-between px-10 py-12 sm:px-14">
                <div className="space-y-8">
                  <div className="flex items-center gap-4">
                    <BrandLogo variant="icon" size="md" />
                    <div>
                      <p className="text-xs uppercase tracking-[0.35em] text-slate-500 dark:text-slate-400">Autonomous Readiness</p>
                      <h2 className="text-2xl font-semibold text-slate-900 dark:text-white">Authenticate your command stack</h2>
                    </div>
                  </div>

                  <div className="flex rounded-full bg-slate-100 p-1 text-sm font-medium dark:bg-slate-900">
                    <button
                      type="button"
                      onClick={() => setMode('login')}
                      className={`flex-1 rounded-full px-4 py-2 transition ${
                        mode === 'login'
                          ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white'
                          : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
                      }`}
                    >
                      Sign in
                    </button>
                    <button
                      type="button"
                      onClick={() => setMode('register')}
                      className={`flex-1 rounded-full px-4 py-2 transition ${
                        mode === 'register'
                          ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white'
                          : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
                      }`}
                    >
                      Request access
                    </button>
                  </div>

                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-3">
                      <label className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Credentials</label>
                      <div className="relative">
                        <EnvelopeIcon className="pointer-events-none absolute left-3 top-2.5 h-5 w-5 text-slate-400 dark:text-slate-500" />
                        <input
                          type="email"
                          required
                          autoComplete="email"
                          value={email}
                          onChange={(event) => setEmail(event.target.value)}
                          className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-11 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-indigo-400"
                          placeholder="you@organization.com"
                        />
                      </div>
                      <div className="relative">
                        <LockClosedIcon className="pointer-events-none absolute left-3 top-2.5 h-5 w-5 text-slate-400 dark:text-slate-500" />
                        <input
                          type="password"
                          required
                          autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                          value={password}
                          onChange={(event) => setPassword(event.target.value)}
                          className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-11 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-indigo-400"
                          placeholder="Enter secure passphrase"
                        />
                      </div>
                    </div>

                    <div className="space-y-3">
                      <label className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Access scope</label>
                      <div className="grid grid-cols-2 gap-3">
                        <button
                          type="button"
                          onClick={() => handleAccountTypeChange('individual')}
                          className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-left transition ${
                            accountType === 'individual'
                              ? 'border-indigo-500 bg-indigo-500/10 text-indigo-600 dark:border-indigo-400 dark:bg-indigo-500/10 dark:text-indigo-200'
                              : 'border-slate-200 text-slate-600 hover:border-slate-300 dark:border-slate-700 dark:text-slate-300 dark:hover:border-slate-600'
                          }`}
                        >
                          <UserIcon className="h-5 w-5" />
                          <div>
                            <p className="text-sm font-semibold">Individual</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400">Solo builder workspace</p>
                          </div>
                        </button>

                        <button
                          type="button"
                          onClick={() => handleAccountTypeChange('enterprise')}
                          className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-left transition ${
                            accountType === 'enterprise'
                              ? 'border-indigo-500 bg-indigo-500/10 text-indigo-600 dark:border-indigo-400 dark:bg-indigo-500/10 dark:text-indigo-200'
                              : 'border-slate-200 text-slate-600 hover:border-slate-300 dark:border-slate-700 dark:text-slate-300 dark:hover:border-slate-600'
                          }`}
                        >
                          <BuildingOffice2Icon className="h-5 w-5" />
                          <div>
                            <p className="text-sm font-semibold">Enterprise</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400">Multi-team fleet management</p>
                          </div>
                        </button>
                      </div>

                      {accountType === 'enterprise' && (
                        <label className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 transition hover:border-indigo-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
                          <div className="flex flex-col">
                            <span className="font-semibold text-slate-800 dark:text-white">Administrator privileges</span>
                            <span className="text-xs text-slate-500 dark:text-slate-400">Full access to agent registry, tools, telemetry</span>
                          </div>
                          <input
                            type="checkbox"
                            checked={isAdmin}
                            onChange={(event) => setIsAdmin(event.target.checked)}
                            className="h-4 w-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800"
                          />
                        </label>
                      )}
                    </div>

                    <button
                      type="submit"
                      className="group relative flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/30 transition hover:shadow-indigo-500/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-500"
                    >
                      {mode === 'login' ? 'Enter command center' : 'Request activation'}
                      <span aria-hidden="true" className="transition-transform group-hover:translate-x-1">
                        →
                      </span>
                    </button>
                  </form>
                </div>

                <p className="mt-10 text-xs text-slate-500 dark:text-slate-400 text-center">
                  By continuing you acknowledge AgentVerse confidentiality protocols.
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
