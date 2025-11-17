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
  // 获取颜色配置 - 使用更简洁的灰度和淡色系
  const getColorClasses = () => {
    switch (color) {
      case 'success':
        return {
          bg: 'bg-slate-100',
          icon: 'text-slate-600',
          border: 'border-slate-200'
        };
      case 'warning':
        return {
          bg: 'bg-slate-100',
          icon: 'text-slate-600',
          border: 'border-slate-200'
        };
      case 'error':
        return {
          bg: 'bg-slate-100',
          icon: 'text-slate-600',
          border: 'border-slate-200'
        };
      case 'info':
        return {
          bg: 'bg-slate-100',
          icon: 'text-slate-600',
          border: 'border-slate-200'
        };
      default:
        return {
          bg: 'bg-slate-100',
          icon: 'text-slate-600',
          border: 'border-slate-200'
        };
    }
  };

  // 获取尺寸配置 - 优化高度和字体大小
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          container: 'p-3',
          title: 'text-xs',
          value: 'text-2xl font-bold',
          description: 'text-xs'
        };
      case 'lg':
        return {
          container: 'p-6',
          title: 'text-sm',
          value: 'text-4xl font-bold',
          description: 'text-sm'
        };
      default:
        return {
          container: 'p-4',
          title: 'text-xs',
          value: 'text-3xl font-bold',
          description: 'text-xs'
        };
    }
  };

  // 获取趋势配置 - 简化颜色
  const getTrendClasses = () => {
    if (!change || changeType === 'neutral') {
      return {
        bg: 'bg-slate-100',
        text: 'text-slate-500',
        icon: Minus
      };
    }

    const isUp = changeType === 'up';
    return {
      bg: 'bg-slate-100',
      text: 'text-slate-600',
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
        bg-white rounded-xl border border-slate-200/60 shadow-sm
        transition-all duration-200 ease-in-out
        ${onClick ? 'cursor-pointer hover:shadow-md' : ''}
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
      {/* 简化的结构：标题 + 图标 */}
      <div className="flex items-center justify-between mb-2">
        <h3 className={`font-medium ${sizeClasses.title} text-slate-600`}>
          {title}
        </h3>
        {icon && (
          <div className={`w-5 h-5 ${colorClasses.icon}`} aria-hidden="true">
            {React.createElement(icon as React.ComponentType<any>, { className: 'w-5 h-5' })}
          </div>
        )}
      </div>

      {/* 数值 */}
      <div
        className={`${sizeClasses.value} text-slate-900 mb-2`}
        aria-label={`当前值: ${value}`}
      >
        {value}
      </div>

      {/* 环比信息：一行简洁显示 */}
      {change !== undefined && (
        <div className={`flex items-center text-xs ${trendClasses.text}`}>
          <TrendIcon className="w-3 h-3 mr-1" aria-hidden="true" />
          环比 {change > 0 ? '+' : ''}{Math.abs(change)}%
          {description && <span className="ml-2 text-slate-400">· {description}</span>}
        </div>
      )}

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