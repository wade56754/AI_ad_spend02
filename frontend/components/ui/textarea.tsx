'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
  showCharCount?: boolean;
  maxLength?: number;
  resize?: 'none' | 'both' | 'horizontal' | 'vertical';
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      className,
      label,
      error,
      helperText,
      showCharCount = false,
      maxLength,
      resize = 'vertical',
      value,
      onChange,
      ...props
    },
    ref
  ) => {
    const [internalValue, setInternalValue] = React.useState(value || '');
    const currentValue = value ?? internalValue;

    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      if (maxLength && e.target.value.length > maxLength) {
        e.target.value = e.target.value.slice(0, maxLength);
      }

      if (onChange) {
        onChange(e);
      }

      if (value === undefined) {
        setInternalValue(e.target.value);
      }
    };

    const getResizeClass = () => {
      switch (resize) {
        case 'none':
          return 'resize-none';
        case 'both':
          return 'resize';
        case 'horizontal':
          return 'resize-x';
        case 'vertical':
          return 'resize-y';
        default:
          return 'resize-y';
      }
    };

    const charCount = typeof currentValue === 'string' ? currentValue.length : 0;
    const isCharCountExceeded = maxLength && charCount >= maxLength;

    return (
      <div className="w-full">
        {label && (
          <label
            className={cn(
              'block text-sm font-medium mb-2',
              error
                ? 'text-red-700 dark:text-red-400'
                : 'text-gray-700 dark:text-gray-300'
            )}
          >
            {label}
          </label>
        )}

        <div className="relative">
          <textarea
            className={cn(
              'flex min-h-[80px] w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:ring-offset-gray-950 dark:placeholder:text-gray-400',
              getResizeClass(),
              error
                ? 'border-red-500 focus-visible:ring-red-500 dark:border-red-500'
                : 'border-gray-300 dark:border-gray-600',
              className
            )}
            ref={ref}
            value={currentValue}
            onChange={handleInputChange}
            maxLength={maxLength}
            aria-invalid={!!error}
            aria-describedby={error ? `${props.id || 'textarea'}-error` : helperText ? `${props.id || 'textarea'}-helper` : undefined}
            {...props}
          />

          {showCharCount && maxLength && (
            <div className="absolute bottom-2 right-2 text-xs text-gray-500 dark:text-gray-400">
              {charCount}/{maxLength}
            </div>
          )}
        </div>

        {/* Error message */}
        {error && (
          <p
            id={`${props.id || 'textarea'}-error`}
            className={cn(
              'mt-2 text-sm',
              'text-red-600 dark:text-red-400'
            )}
          >
            {error}
          </p>
        )}

        {/* Helper text */}
        {helperText && !error && (
          <p
            id={`${props.id || 'textarea'}-helper`}
            className={cn(
              'mt-2 text-sm',
              'text-gray-600 dark:text-gray-400'
            )}
          >
            {helperText}
          </p>
        )}

        {/* Character count warning */}
        {showCharCount && isCharCountExceeded && (
          <p className="mt-2 text-sm text-yellow-600 dark:text-yellow-400">
            已达到最大字符数限制
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

export default Textarea;