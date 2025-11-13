"use client";

import React, { useState, forwardRef, ButtonHTMLAttributes, ReactNode } from "react";

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg' | 'xl';

interface OptimizedButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'size'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  children: ReactNode;
}

export const OptimizedButton = forwardRef<HTMLButtonElement, OptimizedButtonProps>(
  ({
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled = false,
    fullWidth = false,
    icon,
    iconPosition = 'left',
    children,
    className = '',
    onClick,
    ...props
  }, ref) => {
    const [isPressed, setIsPressed] = useState(false);

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (loading || disabled) return;
      onClick?.(e);
    };

    const handleMouseDown = () => setIsPressed(true);
    const handleMouseUp = () => setIsPressed(false);
    const handleMouseLeave = () => setIsPressed(false);

    // 基础样式
    const baseClasses = 'inline-flex items-center justify-center font-medium transition-all duration-200 focus-visible:outline-none disabled:cursor-not-allowed focus-ring';

    // 变体样式
    const variantClasses = {
      primary: 'btn-primary text-white border-0 shadow-md hover:shadow-lg',
      secondary: 'btn-secondary bg-transparent border-2 border-current',
      ghost: 'btn-ghost bg-transparent border-0',
      danger: 'btn-danger bg-gradient-to-r from-red-500 to-red-600 text-white border-0 hover:from-red-600 hover:to-red-700',
    };

    // 尺寸样式
    const sizeClasses = {
      sm: 'px-3 py-1.5 text-xs rounded-lg',
      md: 'px-6 py-3 text-sm rounded-xl',
      lg: 'px-8 py-4 text-base rounded-xl',
      xl: 'px-10 py-5 text-lg rounded-2xl',
    };

    // 状态样式
    const stateClasses = loading
      ? 'opacity-70 pointer-events-none'
      : disabled
      ? 'opacity-50 cursor-not-allowed'
      : isPressed
      ? 'transform scale-95'
      : 'hover:scale-105 active:scale-95';

    // 宽度样式
    const widthClass = fullWidth ? 'w-full' : '';

    const classes = [
      baseClasses,
      variantClasses[variant],
      sizeClasses[size],
      stateClasses,
      widthClass,
      className
    ].filter(Boolean).join(' ');

    const renderIcon = () => {
      if (!icon) return null;
      return (
        <span className={`flex items-center ${iconPosition === 'right' ? 'ml-2' : 'mr-2'}`}>
          {icon}
        </span>
      );
    };

    return (
      <button
        ref={ref}
        className={classes}
        disabled={disabled || loading}
        onClick={handleClick}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        aria-disabled={disabled || loading}
        aria-busy={loading}
        {...props}
      >
        {loading && (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24" aria-hidden="true">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )}
        {iconPosition === 'left' && renderIcon()}
        <span className={loading ? 'opacity-0' : ''}>{children}</span>
        {iconPosition === 'right' && renderIcon()}
      </button>
    );
  }
);

OptimizedButton.displayName = 'OptimizedButton';