'use client';

import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

// 骨架屏组件样式
export interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
  width?: string | number;
  height?: string | number;
  lines?: number;
  animation?: 'pulse' | 'wave' | 'none';
}

/**
 * 骨架屏组件
 * 用于显示内容加载占位符
 */
export function Skeleton({
  className,
  variant = 'rectangular',
  width,
  height,
  lines = 1,
  animation = 'pulse'
}: SkeletonProps) {
  const getVariantStyles = () => {
    switch (variant) {
      case 'text':
        return 'h-4 rounded';
      case 'circular':
        return 'rounded-full';
      case 'rectangular':
        return 'rounded-none';
      case 'rounded':
        return 'rounded-md';
      default:
        return 'rounded';
    }
  };

  const getAnimationClass = () => {
    switch (animation) {
      case 'pulse':
        return 'animate-pulse';
      case 'wave':
        return 'animate-shimmer bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 bg-[length:200%_100%]';
      case 'none':
        return '';
      default:
        return 'animate-pulse';
    }
  };

  const style: React.CSSProperties = {
    width: width || '100%',
    height: height || (variant === 'text' ? '1rem' : 'auto')
  };

  if (variant === 'text' && lines > 1) {
    return (
      <div className={cn('space-y-2', className)}>
        {Array.from({ length: lines }, (_, i) => (
          <div
            key={i}
            className={cn(
              'h-4 bg-gray-200 dark:bg-gray-700 rounded',
              getAnimationClass(),
              i === lines - 1 && 'w-3/4' // 最后一行短一些
            )}
            style={i === lines - 1 ? { width: '75%' } : style}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={cn(
        'bg-gray-200 dark:bg-gray-700',
        getVariantStyles(),
        getAnimationClass(),
        className
      )}
      style={style}
    />
  );
}

// 加载状态组件 Props
export interface LoadingStateProps {
  type?: 'spinner' | 'skeleton' | 'dots' | 'progress';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  message?: string;
  className?: string;
  overlay?: boolean;
  transparent?: boolean;
  progress?: number; // 0-100
  showPercentage?: boolean;
}

/**
 * 通用加载状态组件
 * 支持多种加载动画样式
 */
export function LoadingState({
  type = 'spinner',
  size = 'md',
  message,
  className,
  overlay = false,
  transparent = false,
  progress,
  showPercentage = false
}: LoadingStateProps) {
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'w-4 h-4';
      case 'md':
        return 'w-6 h-6';
      case 'lg':
        return 'w-8 h-8';
      case 'xl':
        return 'w-12 h-12';
      default:
        return 'w-6 h-6';
    }
  };

  const getTextSize = () => {
    switch (size) {
      case 'sm':
        return 'text-sm';
      case 'md':
        return 'text-base';
      case 'lg':
        return 'text-lg';
      case 'xl':
        return 'text-xl';
      default:
        return 'text-base';
    }
  };

  const renderLoadingIcon = () => {
    switch (type) {
      case 'spinner':
        return (
          <Loader2 className={cn('animate-spin', getSizeClasses())} />
        );

      case 'dots':
        return (
          <div className="flex space-x-1">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className={cn(
                  'bg-blue-600 dark:bg-blue-400 rounded-full animate-bounce',
                  size === 'sm' ? 'w-1 h-1' :
                  size === 'md' ? 'w-2 h-2' :
                  size === 'lg' ? 'w-3 h-3' : 'w-4 h-4'
                )}
                style={{
                  animationDelay: `${i * 0.1}s`,
                  animationDuration: '0.6s'
                }}
              />
            ))}
          </div>
        );

      case 'progress':
        return (
          <div className="w-full max-w-md">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {message || '加载中...'}
              </span>
              {showPercentage && progress !== undefined && (
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {Math.round(progress)}%
                </span>
              )}
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-600 dark:bg-blue-400 h-2 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${progress || 0}%` }}
              />
            </div>
          </div>
        );

      case 'skeleton':
        return (
          <div className="space-y-3 w-full">
            <Skeleton variant="text" lines={3} />
            <Skeleton variant="rectangular" height={120} />
            <div className="grid grid-cols-2 gap-4">
              <Skeleton variant="rectangular" height={80} />
              <Skeleton variant="rectangular" height={80} />
            </div>
          </div>
        );

      default:
        return <Loader2 className={cn('animate-spin', getSizeClasses())} />;
    }
  };

  const content = (
    <div className={cn(
      'flex flex-col items-center justify-center',
      type !== 'skeleton' && 'space-y-3',
      className
    )}>
      {renderLoadingIcon()}
      {message && type !== 'progress' && type !== 'skeleton' && (
        <p className={cn(
          'text-gray-600 dark:text-gray-400 text-center',
          getTextSize()
        )}>
          {message}
        </p>
      )}
    </div>
  );

  if (overlay) {
    return (
      <div className={cn(
        'fixed inset-0 z-50 flex items-center justify-center',
        transparent ? 'bg-black bg-opacity-0' : 'bg-black bg-opacity-50'
      )}>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          {content}
        </div>
      </div>
    );
  }

  return content;
}

// 预设的骨架屏组件
export function CardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 space-y-4', className)}>
      <div className="flex items-center space-x-4">
        <Skeleton variant="circular" width={48} height={48} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="40%" />
        </div>
      </div>
      <Skeleton variant="text" lines={2} />
      <div className="flex justify-between items-center">
        <Skeleton variant="rectangular" width={80} height={24} />
        <Skeleton variant="rectangular" width={60} height={24} />
      </div>
    </div>
  );
}

export function MetricCardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6', className)}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <Skeleton variant="text" width="40%" height={16} />
          <Skeleton variant="text" width="60%" height={24} className="mt-2" />
          <Skeleton variant="text" width="30%" height={16} className="mt-2" />
        </div>
        <Skeleton variant="circular" width={48} height={48} />
      </div>
    </div>
  );
}

export function TableSkeleton({ rows = 5, columns = 4, className }: {
  rows?: number;
  columns?: number;
  className?: string;
}) {
  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden', className)}>
      <div className="border-b border-gray-200 dark:border-gray-700 p-4">
        <Skeleton variant="text" width="30%" height={20} />
      </div>
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {Array.from({ length: rows }, (_, i) => (
          <div key={i} className="p-4">
            <div className="grid grid-cols-4 gap-4">
              {Array.from({ length: columns }, (_, j) => (
                <Skeleton key={j} variant="text" />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}