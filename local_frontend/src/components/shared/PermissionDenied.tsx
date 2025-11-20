/**
 * Permission Denied Component
 *
 * Displays a user-friendly message when access is denied due to insufficient permissions.
 * Used throughout the app to enforce permission-based access control.
 */

import { ShieldExclamationIcon } from '@heroicons/react/24/outline';

interface PermissionDeniedProps {
  message?: string;
  action?: string;
  showIcon?: boolean;
}

export function PermissionDenied({
  message = "You don't have permission to access this feature",
  action = 'access this feature',
  showIcon = true,
}: PermissionDeniedProps) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      {showIcon && (
        <div className="mb-6 rounded-full bg-red-100 p-6 dark:bg-red-900/20">
          <ShieldExclamationIcon className="h-16 w-16 text-red-600 dark:text-red-400" />
        </div>
      )}

      <h2 className="mb-2 text-2xl font-bold text-slate-900 dark:text-slate-100">
        Access Denied
      </h2>

      <p className="mb-6 max-w-md text-slate-600 dark:text-slate-400">
        {message}
      </p>

      <div className="rounded-lg bg-slate-100 p-4 dark:bg-slate-800">
        <p className="text-sm text-slate-600 dark:text-slate-400">
          <span className="font-semibold">Required Permission:</span> {action}
        </p>
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-500">
          Contact your administrator to request access.
        </p>
      </div>
    </div>
  );
}

/**
 * Inline Permission Denied (for smaller UI areas)
 */
export function InlinePermissionDenied({ message = 'Access denied' }: { message?: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-900/20 dark:text-red-400">
      <ShieldExclamationIcon className="h-5 w-5 flex-shrink-0" />
      <span>{message}</span>
    </div>
  );
}
