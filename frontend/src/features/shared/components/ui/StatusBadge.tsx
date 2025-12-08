/**
 * StatusBadge Component
 *
 * Reusable status badge for displaying entity states
 * Aligned with UI_DESIGN_SYSTEM.md v0.1
 */

import React from 'react';

export type StatusVariant = 'default' | 'success' | 'warning' | 'error' | 'info';

export interface StatusBadgeProps {
  label: string;
  variant?: StatusVariant;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const variantStyles: Record<StatusVariant, string> = {
  default: 'bg-gray-100 text-gray-800 border-gray-200',
  success: 'bg-green-100 text-green-800 border-green-200',
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  error: 'bg-red-100 text-red-800 border-red-200',
  info: 'bg-blue-100 text-blue-800 border-blue-200',
};

const sizeStyles: Record<'sm' | 'md' | 'lg', string> = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-base',
};

export function StatusBadge({
  label,
  variant = 'default',
  size = 'md',
  className = '',
}: StatusBadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center justify-center
        font-medium rounded-full border
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `.trim()}
    >
      {label}
    </span>
  );
}

export default StatusBadge;
