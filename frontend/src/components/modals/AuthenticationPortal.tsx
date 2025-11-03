import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  EnvelopeIcon,
  LockClosedIcon,
  UserIcon,
  BuildingOffice2Icon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
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
            className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md transition-opacity"
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.97 }}
            transition={{ type: 'spring', damping: 26, stiffness: 240 }}
            className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto px-4 py-10 sm:px-6 lg:py-16"
          >
            <div className="pointer-events-none absolute inset-0 brand-gradient-soft opacity-40" />
            <div className="relative w-full max-w-5xl">
              <div className="absolute -inset-x-16 -inset-y-12 bg-gradient-to-b from-white/10 via-transparent to-transparent blur-3xl dark:from-white/5" />
              <div className="relative flex w-full min-h-[640px] flex-col overflow-hidden rounded-[32px] brand-shell lg:flex-row lg:items-stretch">
                <div className="relative flex flex-1 flex-col justify-between overflow-hidden px-10 py-12 text-white sm:px-12">
                  <div className="absolute inset-0 bg-slate-950/88" />
                  <div className="absolute inset-0 brand-gradient opacity-85" />
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_12%_15%,_rgba(59,130,246,0.35),_transparent_55%)]" />
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_85%_88%,_rgba(236,72,153,0.28),_transparent_60%)]" />
                  <div className="relative z-10 flex flex-1 flex-col justify-between space-y-12">
                    <div className="space-y-6">
                      <BrandLogo
                        variant="horizontal"
                        size="lg"
                        className="drop-shadow-[0_18px_36px_rgba(79,70,229,0.45)]"
                      />
                      <div className="space-y-3 text-sm text-white/80">
                        <p className="text-xs font-semibold uppercase tracking-[0.4em] text-white/60">
                          Command Access
                        </p>
                        <h1 className="text-3xl font-semibold tracking-tight">
                          Authenticate your mission console
                        </h1>
                        <p className="leading-6 text-white/70">
                          Enter secure credentials to orchestrate cross-agent collaboration with full telemetry and
                          governance safeguards.
                        </p>
                      </div>
                      <div className="grid gap-4 text-left sm:grid-cols-2">
                        <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-md">
                          <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-white/60">
                            Orchestrate
                          </p>
                          <p className="mt-2 text-sm font-medium text-white opacity-90">
                            Deploy multi-agent task forces with zero-code lift.
                          </p>
                        </div>
                        <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-md">
                          <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-white/60">
                            Govern
                          </p>
                          <p className="mt-2 text-sm font-medium text-white opacity-90">
                            Role-aware policies with continuous audit visibility.
                          </p>
                        </div>
                        <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-md sm:col-span-2">
                          <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-white/60">
                            Collaborate
                          </p>
                          <p className="mt-2 text-sm font-medium text-white opacity-90">
                            Align human teams and AI cohorts under one shared mission view.
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="rounded-2xl border border-white/15 bg-white/10 p-4 text-xs text-white/75 backdrop-blur">
                      Access monitored. Unauthorized usage triggers automated containment.
                    </div>
                  </div>
                </div>

                <div className="relative flex flex-1 flex-col px-8 py-10 sm:px-12 lg:px-14 brand-surface backdrop-blur-xl lg:border-l lg:border-white/10 dark:lg:border-slate-700/40">
                  <div className="relative z-10 flex h-full flex-col gap-10 overflow-y-auto">
                    <div className="space-y-2 text-left">
                      <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500 dark:text-slate-400">
                        Autonomous Readiness
                      </p>
                      <h2 className="text-2xl font-semibold text-slate-900 dark:text-white">
                        Authenticate your command stack
                      </h2>
                      <p className="text-sm text-slate-500 dark:text-slate-300">
                        Choose your access mode and confirm workspace identity to proceed.
                      </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                      <div className="flex rounded-full brand-glass p-1 text-sm font-semibold">
                        <button
                          type="button"
                          onClick={() => setMode('login')}
                          className={clsx(
                            'flex-1 rounded-full px-4 py-2 transition-all duration-200',
                            mode === 'login'
                              ? 'brand-gradient text-white shadow-lg shadow-indigo-500/30'
                              : 'text-slate-500 hover:text-slate-800 dark:text-slate-300 dark:hover:text-white'
                          )}
                        >
                          Sign in
                        </button>
                        <button
                          type="button"
                          onClick={() => setMode('register')}
                          className={clsx(
                            'flex-1 rounded-full px-4 py-2 transition-all duration-200',
                            mode === 'register'
                              ? 'brand-gradient text-white shadow-lg shadow-indigo-500/30'
                              : 'text-slate-500 hover:text-slate-800 dark:text-slate-300 dark:hover:text-white'
                          )}
                        >
                          Request access
                        </button>
                      </div>

                      <div className="grid gap-3 sm:grid-cols-2">
                        <button
                          type="button"
                          onClick={() => handleAccountTypeChange('individual')}
                          className={clsx(
                            'group flex items-start gap-3 rounded-2xl border px-4 py-4 text-left transition-all duration-200',
                            accountType === 'individual'
                              ? 'border-transparent brand-gradient text-white shadow-xl shadow-indigo-500/30'
                              : 'border-slate-200 bg-white/70 text-slate-600 hover:border-slate-400 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-900/60 dark:text-slate-300 dark:hover:border-slate-500 dark:hover:text-white'
                          )}
                        >
                          <span
                            className={clsx(
                              'flex h-10 w-10 items-center justify-center rounded-xl text-base transition-colors',
                              accountType === 'individual'
                                ? 'bg-white/15 text-white'
                                : 'bg-slate-200/60 text-slate-600 dark:bg-slate-800 dark:text-slate-200'
                            )}
                          >
                            <UserIcon className="h-5 w-5" />
                          </span>
                          <span className="flex flex-col">
                            <span className="text-sm font-semibold">Individual</span>
                            <span className="text-xs opacity-80">Personal workspace with full visibility.</span>
                          </span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleAccountTypeChange('enterprise')}
                          className={clsx(
                            'group flex items-start gap-3 rounded-2xl border px-4 py-4 text-left transition-all duration-200',
                            accountType === 'enterprise'
                              ? 'border-transparent brand-gradient text-white shadow-xl shadow-indigo-500/30'
                              : 'border-slate-200 bg-white/70 text-slate-600 hover:border-slate-400 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-900/60 dark:text-slate-300 dark:hover:border-slate-500 dark:hover:text-white'
                          )}
                        >
                          <span
                            className={clsx(
                              'flex h-10 w-10 items-center justify-center rounded-xl text-base transition-colors',
                              accountType === 'enterprise'
                                ? 'bg-white/15 text-white'
                                : 'bg-slate-200/60 text-slate-600 dark:bg-slate-800 dark:text-slate-200'
                            )}
                          >
                            <BuildingOffice2Icon className="h-5 w-5" />
                          </span>
                          <span className="flex flex-col">
                            <span className="text-sm font-semibold">Enterprise</span>
                            <span className="text-xs opacity-80">Team-wide orchestration with audit controls.</span>
                          </span>
                        </button>
                      </div>

                      <div className="space-y-4">
                        <div className="space-y-2">
                          <label className="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500 dark:text-slate-400">
                            Work Email
                          </label>
                          <div className="brand-field flex items-center gap-3 rounded-2xl px-4 py-3">
                            <EnvelopeIcon className="h-5 w-5 text-indigo-400 dark:text-indigo-300" />
                            <input
                              type="email"
                              required
                              autoComplete="email"
                              value={email}
                              onChange={(event) => setEmail(event.target.value)}
                              placeholder="you@company.com"
                              className="flex-1 bg-transparent text-sm font-medium text-slate-700 placeholder:text-slate-400/70 outline-none dark:text-slate-100"
                            />
                          </div>
                        </div>

                        <div className="space-y-2">
                          <label className="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500 dark:text-slate-400">
                            Secure Passkey
                          </label>
                          <div className="brand-field flex items-center gap-3 rounded-2xl px-4 py-3">
                            <LockClosedIcon className="h-5 w-5 text-indigo-400 dark:text-indigo-300" />
                            <input
                              type="password"
                              required
                              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                              value={password}
                              onChange={(event) => setPassword(event.target.value)}
                              placeholder="••••••••"
                              className="flex-1 bg-transparent text-sm font-medium text-slate-700 placeholder:text-slate-400/70 outline-none dark:text-slate-100"
                            />
                          </div>
                        </div>

                        {accountType === 'enterprise' && (
                          <label className="flex items-center justify-between rounded-2xl border border-slate-200/70 bg-white/70 px-4 py-3 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-900/50 dark:text-slate-300 dark:hover:border-slate-500 dark:hover:text-white">
                            <span>Enable admin console</span>
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
                        className="brand-cta group relative flex w-full items-center justify-center gap-2 rounded-2xl px-5 py-3 text-sm font-semibold shadow-2xl transition-all duration-200 hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-500"
                      >
                        {mode === 'login' ? 'Enter command center' : 'Request activation'}
                        <span aria-hidden="true" className="text-base transition-transform duration-200 group-hover:translate-x-1">
                          →
                        </span>
                      </button>
                    </form>

                    <p className="text-center text-xs text-slate-500 dark:text-slate-400">
                      By continuing you acknowledge AgentVerse confidentiality protocols.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
