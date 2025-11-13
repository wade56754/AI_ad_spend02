import React from 'react';

export type StatusType = 'success' | 'warning' | 'error' | 'info' | 'pending' | 'active' | 'inactive';

export interface StatusBadgeProps {
  status: StatusType;
  children: React.ReactNode;
  dot?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'solid' | 'outline';
  className?: string;
  ariaLabel?: string;
}

/**
 * 状态标签组件
 *
 * 用于显示各种状态信息，支持多种样式和尺寸
 * 符合WCAG 2.1 AA级可访问性标准
 */
export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  children,
  dot = true,
  size = 'md',
  variant = 'solid',
  className = '',
  ariaLabel
}) => {
  // 获取状态配置
  const getStatusConfig = () => {
    switch (status) {
      case 'success':
        return {
          text: 'text-green-700 dark:text-green-300',
          bg: variant === 'solid'
            ? 'bg-green-100 dark:bg-green-900/50 border-green-200 dark:border-green-700'
            : 'bg-transparent border-green-200 dark:border-green-700',
          border: 'border-green-200 dark:border-green-700',
          dot: 'bg-green-500',
          ariaLabel: '成功状态'
        };
      case 'warning':
        return {
          text: 'text-amber-700 dark:text-amber-300',
          bg: variant === 'solid'
            ? 'bg-amber-100 dark:bg-amber-900/50 border-amber-200 dark:border-amber-700'
            : 'bg-transparent border-amber-200 dark:border-amber-700',
          border: 'border-amber-200 dark:border-amber-700',
          dot: 'bg-amber-500',
          ariaLabel: '警告状态'
        };
      case 'error':
        return {
          text: 'text-red-700 dark:text-red-300',
          bg: variant === 'solid'
            ? 'bg-red-100 dark:bg-red-900/50 border-red-200 dark:border-red-700'
            : 'bg-transparent border-red-200 dark:border-red-700',
          border: 'border-red-200 dark:border-red-700',
          dot: 'bg-red-500',
          ariaLabel: '错误状态'
        };
      case 'info':
        return {
          text: 'text-blue-700 dark:text-blue-300',
          bg: variant === 'solid'
            ? 'bg-blue-100 dark:bg-blue-900/50 border-blue-200 dark:border-blue-700'
            : 'bg-transparent border-blue-200 dark:border-blue-700',
          border: 'border-blue-200 dark:border-blue-700',
          dot: 'bg-blue-500',
          ariaLabel: '信息状态'
        };
      case 'pending':
        return {
          text: 'text-gray-700 dark:text-gray-300',
          bg: variant === 'solid'
            ? 'bg-gray-100 dark:bg-gray-900/50 border-gray-200 dark:border-gray-700'
            : 'bg-transparent border-gray-200 dark:border-gray-700',
          border: 'border-gray-200 dark:border-gray-700',
          dot: 'bg-gray-500',
          ariaLabel: '等待状态'
        };
      case 'active':
        return {
          text: 'text-green-700 dark:text-green-300',
          bg: variant === 'solid'
            ? 'bg-green-100 dark:bg-green-900/50 border-green-200 dark:border-green-700'
            : 'bg-transparent border-green-200 dark:border-green-700',
          border: 'border-green-200 dark:border-green-700',
          dot: 'bg-green-500',
          ariaLabel: '活跃状态'
        };
      case 'inactive':
        return {
          text: 'text-gray-500 dark:text-gray-400',
          bg: variant === 'solid'
            ? 'bg-gray-100 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
            : 'bg-transparent border-gray-300 dark:border-gray-600',
          border: 'border-gray-300 dark:border-gray-600',
          dot: 'bg-gray-400',
          ariaLabel: '非活跃状态'
        };
      default:
        return {
          text: 'text-gray-700 dark:text-gray-300',
          bg: variant === 'solid'
            ? 'bg-gray-100 dark:bg-gray-900/50 border-gray-200 dark:border-gray-700'
            : 'bg-transparent border-gray-200 dark:border-gray-700',
          border: 'border-gray-200 dark:border-gray-700',
          dot: 'bg-gray-500',
          ariaLabel: '默认状态'
        };
    }
  };

  // 获取尺寸配置
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          container: 'px-2 py-1 text-xs',
          dot: 'w-1.5 h-1.5'
        };
      case 'lg':
        return {
          container: 'px-4 py-2 text-base',
          dot: 'w-2.5 h-2.5'
        };
      default:
        return {
          container: 'px-3 py-1.5 text-sm',
          dot: 'w-2 h-2'
        };
    }
  };

  const statusConfig = getStatusConfig();
  const sizeClasses = getSizeClasses();

  return (
    <span
      className={`
        inline-flex items-center font-medium
        border rounded-full
        transition-all duration-200 ease-in-out
        ${statusConfig.bg} ${statusConfig.text} ${statusConfig.border}
        ${sizeClasses.container}
        ${className}
      `}
      role="status"
      aria-label={ariaLabel || statusConfig.ariaLabel}
    >
      {dot && (
        <span
          className={`
            ${statusConfig.dot}
            ${sizeClasses.dot}
            rounded-full mr-2
            ${variant === 'outline' ? 'opacity-60' : 'opacity-100'}
          `}
          aria-hidden="true"
        />
      )}
      {children}
    </span>
  );
};

export default StatusBadge;