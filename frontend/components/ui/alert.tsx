'use client';

import { ReactNode } from 'react';
import { X, AlertCircle, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';

export type AlertVariant = 'default' | 'destructive' | 'warning' | 'success' | 'info';

interface AlertProps {
  variant?: AlertVariant;
  title?: string;
  description?: string;
  children?: ReactNode;
  className?: string;
  showIcon?: boolean;
  dismissible?: boolean;
  onDismiss?: () => void;
}

const alertVariants = {
  default: {
    container: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    icon: 'text-blue-600 dark:text-blue-400',
    title: 'text-blue-800 dark:text-blue-200',
    description: 'text-blue-700 dark:text-blue-300',
    Icon: Info
  },
  destructive: {
    container: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
    icon: 'text-red-600 dark:text-red-400',
    title: 'text-red-800 dark:text-red-200',
    description: 'text-red-700 dark:text-red-300',
    Icon: AlertCircle
  },
  warning: {
    container: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800',
    icon: 'text-yellow-600 dark:text-yellow-400',
    title: 'text-yellow-800 dark:text-yellow-200',
    description: 'text-yellow-700 dark:text-yellow-300',
    Icon: AlertTriangle
  },
  success: {
    container: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    icon: 'text-green-600 dark:text-green-400',
    title: 'text-green-800 dark:text-green-200',
    description: 'text-green-700 dark:text-green-300',
    Icon: CheckCircle
  },
  info: {
    container: 'bg-cyan-50 dark:bg-cyan-900/20 border-cyan-200 dark:border-cyan-800',
    icon: 'text-cyan-600 dark:text-cyan-400',
    title: 'text-cyan-800 dark:text-cyan-200',
    description: 'text-cyan-700 dark:text-cyan-300',
    Icon: Info
  }
};

export default function Alert({
  variant = 'default',
  title,
  description,
  children,
  className = '',
  showIcon = true,
  dismissible = false,
  onDismiss
}: AlertProps) {
  const config = alertVariants[variant];
  const Icon = config.Icon;

  return (
    <div
      role="alert"
      className={cn(
        'relative w-full rounded-lg border p-4',
        config.container,
        className
      )}
    >
      {/* Dismiss Button */}
      {dismissible && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onDismiss}
          className="absolute right-2 top-2 h-6 w-6 p-0 hover:bg-black/10 dark:hover:bg-white/10"
          aria-label="关闭提示"
        >
          <X className="h-4 w-4" />
        </Button>
      )}

      {/* Content */}
      <div className="flex items-start space-x-3">
        {/* Icon */}
        {showIcon && (
          <Icon className={cn('h-5 w-5 flex-shrink-0 mt-0.5', config.icon)} aria-hidden="true" />
        )}

        {/* Text Content */}
        <div className="flex-1 min-w-0">
          {title && (
            <h3 className={cn('font-medium text-sm', config.title)}>
              {title}
            </h3>
          )}

          {(description || children) && (
            <div className={cn('text-sm mt-1', config.description)}>
              {description || children}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Alert Components for Different Variants
export const AlertDestructive = (props: Omit<AlertProps, 'variant'>) => (
  <Alert {...props} variant="destructive" />
);

export const AlertWarning = (props: Omit<AlertProps, 'variant'>) => (
  <Alert {...props} variant="warning" />
);

export const AlertSuccess = (props: Omit<AlertProps, 'variant'>) => (
  <Alert {...props} variant="success" />
);

export const AlertInfo = (props: Omit<AlertProps, 'variant'>) => (
  <Alert {...props} variant="info" />
);

// Alert Title Component
export const AlertTitle = ({
  children,
  className = '',
  ...props
}: {
  children: ReactNode;
  className?: string;
}) => (
  <h5
    className={cn('mb-1 font-medium leading-none tracking-tight', className)}
    {...props}
  >
    {children}
  </h5>
);

// Alert Description Component
export const AlertDescription = ({
  children,
  className = '',
  ...props
}: {
  children: ReactNode;
  className?: string;
}) => (
  <div
    className={cn('text-sm [&_p]:leading-relaxed', className)}
    {...props}
  >
    {children}
  </div>
);