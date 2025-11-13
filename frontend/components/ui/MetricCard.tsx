import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeType?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  description?: string;
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info';
  loading?: boolean;
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  className?: string;
}

/**
 * 指标卡片组件
 *
 * 用于展示关键业务指标，支持趋势显示和多种状态
 * 符合WCAG 2.1 AA级可访问性标准
 */
export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  changeType,
  icon,
  description,
  color = 'primary',
  loading = false,
  size = 'md',
  onClick,
  className = ''
}) => {
  // 获取颜色配置
  const getColorClasses = () => {
    switch (color) {
      case 'success':
        return {
          bg: 'bg-green-100 dark:bg-green-900/30',
          icon: 'text-green-600 dark:text-green-400',
          border: 'border-green-200 dark:border-green-800'
        };
      case 'warning':
        return {
          bg: 'bg-amber-100 dark:bg-amber-900/30',
          icon: 'text-amber-600 dark:text-amber-400',
          border: 'border-amber-200 dark:border-amber-800'
        };
      case 'error':
        return {
          bg: 'bg-red-100 dark:bg-red-900/30',
          icon: 'text-red-600 dark:text-red-400',
          border: 'border-red-200 dark:border-red-800'
        };
      case 'info':
        return {
          bg: 'bg-blue-100 dark:bg-blue-900/30',
          icon: 'text-blue-600 dark:text-blue-400',
          border: 'border-blue-200 dark:border-blue-800'
        };
      default:
        return {
          bg: 'bg-blue-100 dark:bg-blue-900/30',
          icon: 'text-blue-600 dark:text-blue-400',
          border: 'border-blue-200 dark:border-blue-800'
        };
    }
  };

  // 获取尺寸配置
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          container: 'p-4',
          title: 'text-sm',
          value: 'text-xl',
          description: 'text-xs'
        };
      case 'lg':
        return {
          container: 'p-8',
          title: 'text-lg',
          value: 'text-4xl',
          description: 'text-base'
        };
      default:
        return {
          container: 'p-6',
          title: 'text-sm',
          value: 'text-2xl',
          description: 'text-sm'
        };
    }
  };

  // 获取趋势配置
  const getTrendClasses = () => {
    if (!change || changeType === 'neutral') {
      return {
        bg: 'bg-gray-100 dark:bg-gray-900/30',
        text: 'text-gray-600 dark:text-gray-400',
        icon: Minus
      };
    }

    const isUp = changeType === 'up';
    return {
      bg: isUp ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30',
      text: isUp ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400',
      icon: isUp ? TrendingUp : TrendingDown
    };
  };

  const colorClasses = getColorClasses();
  const sizeClasses = getSizeClasses();
  const trendClasses = getTrendClasses();
  const TrendIcon = trendClasses.icon;

  // 加载状态
  if (loading) {
    return (
      <div
        className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 ${sizeClasses.container} ${className}`}
        role="status"
        aria-label="加载中"
      >
        <div className="animate-pulse space-y-4">
          <div className="flex items-center justify-between">
            <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
            <div className="w-16 h-6 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
          </div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          </div>
        </div>
        <span className="sr-only">正在加载指标数据</span>
      </div>
    );
  }

  return (
    <div
      className={`
        bg-white dark:bg-gray-800
        rounded-xl
        border border-gray-200 dark:border-gray-700
        shadow-sm hover:shadow-md
        transition-all duration-200 ease-in-out
        ${onClick ? 'cursor-pointer hover:scale-[1.02]' : ''}
        ${sizeClasses.container}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? 'button' : 'region'}
      tabIndex={onClick ? 0 : undefined}
      aria-label={title}
      onKeyDown={onClick ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      } : undefined}
    >
      {/* 头部区域 */}
      <div className="flex items-center justify-between mb-4">
        {/* 图标 */}
        {icon && (
          <div
            className={`p-3 rounded-lg ${colorClasses.bg}`}
            aria-hidden="true"
          >
            <div className={`w-6 h-6 ${colorClasses.icon}`}>
              {React.createElement(icon as React.ComponentType<any>, { className: 'w-6 h-6' })}
            </div>
          </div>
        )}

        {/* 趋势指标 */}
        {change !== undefined && (
          <div
            className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${trendClasses.bg} ${trendClasses.text}`}
            aria-label={`变化趋势: ${change > 0 ? '上升' : change < 0 ? '下降' : '持平'} ${Math.abs(change)}%`}
          >
            <TrendIcon className="w-3 h-3 mr-1" aria-hidden="true" />
            {Math.abs(change)}%
          </div>
        )}
      </div>

      {/* 主要内容 */}
      <div className="space-y-2">
        {/* 标题 */}
        <h3 className={`font-medium ${sizeClasses.title} text-gray-600 dark:text-gray-400`}>
          {title}
        </h3>

        {/* 数值 */}
        <div
          className={`font-bold ${sizeClasses.value} text-gray-900 dark:text-white`}
          aria-label={`当前值: ${value}`}
        >
          {value}
        </div>

        {/* 描述 */}
        {description && (
          <p className={`${sizeClasses.description} text-gray-500 dark:text-gray-400`}>
            {description}
          </p>
        )}
      </div>

      {/* 可访问性提示 */}
      {onClick && (
        <span className="sr-only">
          点击查看{title}详情
        </span>
      )}
    </div>
  );
};

export default MetricCard;