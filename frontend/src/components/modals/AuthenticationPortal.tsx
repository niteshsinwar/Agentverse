/**
 * Authentication Portal
 * Login/Register with Individual and Enterprise account types
 * Enterprise accounts can be marked as Admin
 * NON-FUNCTIONAL: UI demonstration only
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  UserIcon,
  BuildingOfficeIcon,
  EnvelopeIcon,
  LockClosedIcon,
  CheckCircleIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import { useAuthStore, type AccountType } from '@/lib/stores/auth';
import { BrandLogo } from '@/components/shared/BrandLogo';

interface AuthenticationPortalProps {
  isOpen: boolean;
  onClose: () => void;
}

type AuthMode = 'login' | 'register';

export const AuthenticationPortal: React.FC<AuthenticationPortalProps> = ({ isOpen, onClose }) => {
  const { login } = useAuthStore();
  
  const [authMode, setAuthMode] = useState<AuthMode>('login');
  const [selectedAccountType, setSelectedAccountType] = useState<AccountType>('individual');
  const [isAdmin, setIsAdmin] = useState(false);
  
  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [companyName, setCompanyName] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Mock authentication
    login(email, password, selectedAccountType, isAdmin);
    
    // Reset form
    setEmail('');
    setPassword('');
    setCompanyName('');
    setIsAdmin(false);
    onClose();
  };

  const handleAccountTypeChange = (type: AccountType) => {
    setSelectedAccountType(type);
    if (type === 'individual') {
      setIsAdmin(false); // Reset admin when switching to individual
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop - Don't close on click for required login */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Portal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto"
          >
            <div className="bg-white dark:bg-gray-900 rounded-3xl shadow-2xl w-full max-w-5xl my-8 overflow-hidden flex flex-col md:flex-row max-h-[90vh]">
              {/* Left Side - Branding */}
              <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-purple-600 via-pink-600 to-indigo-600 p-12 flex-col justify-between text-white relative overflow-hidden">
                {/* Decorative background patterns */}
                <div className="absolute inset-0 opacity-10">
                  <div className="absolute top-0 right-0 w-96 h-96 bg-white rounded-full blur-3xl -mr-48 -mt-48"></div>
                  <div className="absolute bottom-0 left-0 w-96 h-96 bg-white rounded-full blur-3xl -ml-48 -mb-48"></div>
                </div>

                <div className="relative z-10">
                  {/* Logo */}
                  <div className="mb-8 flex items-center justify-center lg:justify-start">
                    <BrandLogo variant="horizontal" size="xl" className="filter drop-shadow-2xl" />
                  </div>

                  <h1 className="text-4xl font-bold mb-4">Welcome to AgentVerse</h1>
                  <p className="text-white/90 text-lg mb-8">
                    Build unlimited AI agents without code. Join 10K+ developers and enterprises.
                  </p>
                  
                  <div className="space-y-4">
                    <div className="flex items-start space-x-3">
                      <CheckCircleIcon className="w-6 h-6 flex-shrink-0 mt-0.5" />
                      <div>
                        <h3 className="font-semibold mb-1">Individual Accounts</h3>
                        <p className="text-white/80 text-sm">Perfect for developers and freelancers</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <CheckCircleIcon className="w-6 h-6 flex-shrink-0 mt-0.5" />
                      <div>
                        <h3 className="font-semibold mb-1">Enterprise Teams</h3>
                        <p className="text-white/80 text-sm">Collaborate with advanced permissions</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <ShieldCheckIcon className="w-6 h-6 flex-shrink-0 mt-0.5" />
                      <div>
                        <h3 className="font-semibold mb-1">Admin Controls</h3>
                        <p className="text-white/80 text-sm">Manage team access and permissions</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="relative z-10 bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-xl">
                  <div className="flex items-start space-x-3 mb-4">
                    <svg className="w-8 h-8 text-white/80 flex-shrink-0" fill="currentColor" viewBox="0 0 32 32">
                      <path d="M9.352 4C4.456 7.456 1 13.12 1 19.36c0 5.088 3.072 8.064 6.624 8.064 3.36 0 5.856-2.688 5.856-5.856 0-3.168-2.208-5.472-5.088-5.472-.576 0-1.344.096-1.536.192.48-3.264 3.552-7.104 6.624-9.024L9.352 4zm16.512 0c-4.8 3.456-8.256 9.12-8.256 15.36 0 5.088 3.072 8.064 6.624 8.064 3.264 0 5.856-2.688 5.856-5.856 0-3.168-2.304-5.472-5.184-5.472-.576 0-1.248.096-1.44.192.48-3.264 3.456-7.104 6.528-9.024L25.864 4z" />
                    </svg>
                  </div>
                  <p className="text-base text-white/95 italic leading-relaxed mb-4">
                    "AgentVerse transformed how our team builds AI solutions. The enterprise admin controls are game-changing!"
                  </p>
                  <div className="flex items-center space-x-3 pt-4 border-t border-white/20">
                    <div className="w-12 h-12 bg-gradient-to-br from-white/30 to-white/10 rounded-full flex items-center justify-center font-bold text-lg backdrop-blur-sm border border-white/30">
                      JS
                    </div>
                    <div>
                      <div className="font-semibold text-white">John Smith</div>
                      <div className="text-white/70 text-sm">CTO, TechCorp</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Side - Form */}
              <div className="w-full lg:w-1/2 p-8 lg:p-12 flex flex-col overflow-y-auto">
                {/* Demo Credentials Banner */}
                <div className="mb-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                  <p className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-2">
                    🎭 Demo Mode - Try These:
                  </p>
                  <div className="space-y-1 text-xs text-blue-800 dark:text-blue-400">
                    <p>• <strong>Individual:</strong> Any email, select Individual</p>
                    <p>• <strong>Enterprise User:</strong> Any email, select Enterprise</p>
                    <p>• <strong>Enterprise Admin:</strong> Any email, select Enterprise + check "I am an Administrator"</p>
                  </div>
                </div>

                {/* Mode Toggle */}
                <div className="flex space-x-2 mb-8 bg-gray-100 dark:bg-gray-800 p-1 rounded-xl">
                  <button
                    onClick={() => setAuthMode('login')}
                    className={`flex-1 py-3 rounded-lg font-medium transition-all ${
                      authMode === 'login'
                        ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                        : 'text-gray-600 dark:text-gray-400'
                    }`}
                  >
                    Login
                  </button>
                  <button
                    onClick={() => setAuthMode('register')}
                    className={`flex-1 py-3 rounded-lg font-medium transition-all ${
                      authMode === 'register'
                        ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                        : 'text-gray-600 dark:text-gray-400'
                    }`}
                  >
                    Register
                  </button>
                </div>

                {/* Title */}
                <div className="mb-8">
                  <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                    {authMode === 'login' ? 'Welcome Back' : 'Create Account'}
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400">
                    {authMode === 'login'
                      ? 'Enter your credentials to continue'
                      : 'Choose your account type to get started'}
                  </p>
                </div>

                {/* Account Type Selection */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Account Type
                  </label>
                  <div className="grid grid-cols-2 gap-4">
                    {/* Individual */}
                    <button
                      onClick={() => handleAccountTypeChange('individual')}
                      className={`p-4 rounded-xl border-2 transition-all ${
                        selectedAccountType === 'individual'
                          ? 'border-purple-600 bg-purple-50 dark:bg-purple-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                    >
                      <UserIcon className={`w-8 h-8 mx-auto mb-2 ${
                        selectedAccountType === 'individual'
                          ? 'text-purple-600'
                          : 'text-gray-400'
                      }`} />
                      <div className="font-medium text-gray-900 dark:text-white">Individual</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        For personal use
                      </div>
                      <div className="text-xs font-semibold text-purple-600 mt-2">
                        $29/month
                      </div>
                    </button>

                    {/* Enterprise */}
                    <button
                      onClick={() => handleAccountTypeChange('enterprise')}
                      className={`p-4 rounded-xl border-2 transition-all ${
                        selectedAccountType === 'enterprise'
                          ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                    >
                      <BuildingOfficeIcon className={`w-8 h-8 mx-auto mb-2 ${
                        selectedAccountType === 'enterprise'
                          ? 'text-indigo-600'
                          : 'text-gray-400'
                      }`} />
                      <div className="font-medium text-gray-900 dark:text-white">Enterprise</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        For teams
                      </div>
                      <div className="text-xs font-semibold text-indigo-600 mt-2">
                        $199/month
                      </div>
                    </button>
                  </div>
                </div>

                {/* Enterprise Admin Checkbox - Moved here for visibility */}
                {selectedAccountType === 'enterprise' && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                    className="mb-6"
                  >
                    <div className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 border-2 border-amber-300 dark:border-amber-700 rounded-xl p-5 shadow-md">
                      <label className="flex items-start space-x-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={isAdmin}
                          onChange={(e) => setIsAdmin(e.target.checked)}
                          className="mt-1 w-6 h-6 text-amber-600 border-gray-300 rounded focus:ring-amber-500 cursor-pointer"
                        />
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <ShieldCheckIcon className="w-6 h-6 text-amber-600" />
                            <span className="font-bold text-gray-900 dark:text-white text-base">
                              ✅ I am an Administrator
                            </span>
                          </div>
                          <p className="text-sm text-gray-700 dark:text-gray-300">
                            Admins can manage team members, control group access, and configure enterprise settings. 
                            <span className="font-semibold text-amber-700 dark:text-amber-400"> Check this box to access the Admin Dashboard.</span>
                          </p>
                        </div>
                      </label>
                    </div>
                  </motion.div>
                )}

                {/* Plan Details */}
                <motion.div
                  key={selectedAccountType}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-6 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-xl p-4 border border-gray-200 dark:border-gray-600"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                        {selectedAccountType === 'individual' ? 'Individual Plan' : 'Enterprise Plan'}
                      </h3>
                      <p className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                        {selectedAccountType === 'individual' ? '$29' : '$199'}
                        <span className="text-sm text-gray-500 dark:text-gray-400 font-normal">/month</span>
                      </p>
                    </div>
                    {selectedAccountType === 'individual' && (
                      <button
                        type="button"
                        onClick={() => handleAccountTypeChange('enterprise')}
                        className="text-xs font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 underline"
                      >
                        Upgrade to Enterprise →
                      </button>
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    {selectedAccountType === 'individual' ? (
                      <>
                        <div className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                          <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                          <span>Unlimited agents & workflows</span>
                        </div>
                        <div className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                          <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                          <span>Access to ∞ community marketplace</span>
                        </div>
                        <div className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                          <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                          <span>500+ pre-built MCPs & tools</span>
                        </div>
                        <div className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                          <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                          <span>API access & integrations</span>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                          <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                          <span><strong>Everything in Individual</strong> plus:</span>
                        </div>
                        <div className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                          <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                          <span>Team collaboration & workspaces</span>
                        </div>
                        <div className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                          <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                          <span>Admin controls & user management</span>
                        </div>
                        <div className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                          <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                          <span>Advanced permissions & group access</span>
                        </div>
                        <div className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                          <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                          <span>Priority support & dedicated account manager</span>
                        </div>
                      </>
                    )}
                  </div>
                </motion.div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-4 flex-1">
                  {/* Email */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Email
                    </label>
                    <div className="relative">
                      <EnvelopeIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@example.com"
                        required
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  {/* Password */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Password
                    </label>
                    <div className="relative">
                      <LockClosedIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        required
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  {/* Company Name (Enterprise only) */}
                  <AnimatePresence>
                    {selectedAccountType === 'enterprise' && authMode === 'register' && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                      >
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Company Name
                        </label>
                        <div className="relative">
                          <BuildingOfficeIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                          <input
                            type="text"
                            value={companyName}
                            onChange={(e) => setCompanyName(e.target.value)}
                            placeholder="Your Company"
                            className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                          />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    className="w-full py-4 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-semibold transition-all transform hover:scale-105 shadow-lg"
                  >
                    {authMode === 'login' ? 'Sign In' : 'Create Account'}
                  </button>

                  {/* Additional Links */}
                  <div className="text-center text-sm text-gray-600 dark:text-gray-400 pt-4">
                    {authMode === 'login' ? (
                      <p>
                        Don't have an account?{' '}
                        <button
                          type="button"
                          onClick={() => setAuthMode('register')}
                          className="text-purple-600 hover:text-purple-700 font-medium"
                        >
                          Register
                        </button>
                      </p>
                    ) : (
                      <p>
                        Already have an account?{' '}
                        <button
                          type="button"
                          onClick={() => setAuthMode('login')}
                          className="text-purple-600 hover:text-purple-700 font-medium"
                        >
                          Login
                        </button>
                      </p>
                    )}
                  </div>
                </form>

                {/* Demo Note */}
                <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                  <p className="text-sm text-blue-900 dark:text-blue-300">
                    <strong>Demo Mode:</strong> This is a UI demonstration. Try selecting "Enterprise" and checking "Administrator" to see admin controls in settings!
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
