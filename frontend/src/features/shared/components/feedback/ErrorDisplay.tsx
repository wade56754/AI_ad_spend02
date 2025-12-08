/**
 * ErrorDisplay Component
 *
 * Displays API errors with user-friendly messages
 * Aligned with ERROR_CODES_SOT.md v2.1
 */

import React from 'react';
import type { ApiError } from '@/lib/api';

// Type guard for ApiError-like objects
function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    'message' in error
  );
}

export interface ErrorDisplayProps {
  error: Error | ApiError | null;
  onRetry?: () => void;
  className?: string;
}

export function ErrorDisplay({ error, onRetry, className = '' }: ErrorDisplayProps) {
  if (!error) return null;

  // Get user-friendly message
  let message = error.message;
  let code: string | undefined;

  if (isApiError(error)) {
    code = error.code;
    message = error.message;
  }

  return (
    <div
      className={`
        rounded-lg border border-red-200 bg-red-50 p-4
        ${className}
      `.trim()}
      role="alert"
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-red-400"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">
            {code ? `Error ${code}` : 'Error'}
          </h3>
          <p className="mt-1 text-sm text-red-700">{message}</p>
        </div>
        {onRetry && (
          <div className="ml-auto pl-3">
            <button
              type="button"
              onClick={onRetry}
              className="
                inline-flex rounded-md bg-red-50 p-1.5
                text-red-500 hover:bg-red-100
                focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2 focus:ring-offset-red-50
              "
            >
              <span className="sr-only">Retry</span>
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ErrorDisplay;
