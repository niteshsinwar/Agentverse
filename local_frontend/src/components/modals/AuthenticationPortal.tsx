import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  EnvelopeIcon,
  LockClosedIcon,
  BuildingOffice2Icon,
} from '@heroicons/react/24/outline';
import { BrandLogo } from '@/components/shared/BrandLogo';
import { useAuthStore } from '@/lib/stores/auth';

interface AuthenticationPortalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AuthenticationPortal: React.FC<AuthenticationPortalProps> = ({ isOpen, onClose }) => {
  const { login } = useAuthStore();

  const [tenantId, setTenantId] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const resetForm = () => {
    setTenantId('');
    setEmail('');
    setPassword('');
    setError('');
    setIsLoading(false);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(tenantId, email, password);
      resetForm();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setIsLoading(false);
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
                        Secure Access
                      </p>
                      <h2 className="text-2xl font-semibold text-slate-900 dark:text-white">
                        Sign in to your workspace
                      </h2>
                      <p className="text-sm text-slate-500 dark:text-slate-300">
                        Enter your tenant credentials to access your command center.
                      </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">

                      {error && (
                        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
                          {error}
                        </div>
                      )}

                      <div className="space-y-4">
                        <div className="space-y-2">
                          <label className="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500 dark:text-slate-400">
                            Tenant ID
                          </label>
                          <div className="brand-field flex items-center gap-3 rounded-2xl px-4 py-3">
                            <BuildingOffice2Icon className="h-5 w-5 text-indigo-400 dark:text-indigo-300" />
                            <input
                              type="text"
                              required
                              value={tenantId}
                              onChange={(event) => setTenantId(event.target.value)}
                              placeholder="acme"
                              className="flex-1 bg-transparent text-sm font-medium text-slate-700 placeholder:text-slate-400/70 outline-none dark:text-slate-100"
                            />
                          </div>
                          <p className="text-xs text-slate-400 dark:text-slate-500">
                            Your organization's unique identifier (e.g., acme, techstart)
                          </p>
                        </div>

                        <div className="space-y-2">
                          <label className="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500 dark:text-slate-400">
                            Email
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
                            Password
                          </label>
                          <div className="brand-field flex items-center gap-3 rounded-2xl px-4 py-3">
                            <LockClosedIcon className="h-5 w-5 text-indigo-400 dark:text-indigo-300" />
                            <input
                              type="password"
                              required
                              autoComplete="current-password"
                              value={password}
                              onChange={(event) => setPassword(event.target.value)}
                              placeholder="••••••••"
                              className="flex-1 bg-transparent text-sm font-medium text-slate-700 placeholder:text-slate-400/70 outline-none dark:text-slate-100"
                            />
                          </div>
                        </div>
                      </div>

                      <button
                        type="submit"
                        disabled={isLoading || !tenantId || !email || !password}
                        className="brand-cta group relative flex w-full items-center justify-center gap-2 rounded-2xl px-5 py-3 text-sm font-semibold shadow-2xl transition-all duration-200 hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
                      >
                        {isLoading ? (
                          <>
                            <span className="animate-spin">⏳</span>
                            Signing in...
                          </>
                        ) : (
                          <>
                            Sign in
                            <span aria-hidden="true" className="text-base transition-transform duration-200 group-hover:translate-x-1">
                              →
                            </span>
                          </>
                        )}
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
