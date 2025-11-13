"use client";

import React, { useState } from "react";

export type TrendType = 'up' | 'down' | 'neutral';
export type MetricColor = 'primary' | 'success' | 'warning' | 'error';

interface OptimizedMetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeType?: TrendType;
  icon: React.ReactNode;
  color?: MetricColor;
  loading?: boolean;
  description?: string;
  onClick?: () => void;
}

export const OptimizedMetricCard: React.FC<OptimizedMetricCardProps> = ({
  title,
  value,
  change,
  changeType = 'neutral',
  icon,
  color = 'primary',
  loading = false,
  description,
  onClick
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const colorClasses = {
    primary: 'metric-card-primary',
    success: 'metric-card-success',
    warning: 'metric-card-warning',
    error: 'metric-card-error',
  };

  const getTrendIcon = () => {
    switch (changeType) {
      case 'up':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        );
      case 'down':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
          </svg>
        );
      default:
        return null;
    }
  };

  const formatNumber = (num: string | number): string => {
    const n = typeof num === 'string' ? parseFloat(num) : num;
    if (isNaN(n)) return '0';

    if (n >= 1000000) {
      return `${(n / 1000000).toFixed(1)}M`;
    } else if (n >= 1000) {
      return `${(n / 1000).toFixed(1)}K`;
    }
    return n.toFixed(0);
  };

  const formatChange = (change: number): string => {
    const sign = change > 0 ? '+' : '';
    return `${sign}${change.toFixed(1)}%`;
  };

  const getChangeColor = () => {
    if (changeType === 'up') return 'text-green-500';
    if (changeType === 'down') return 'text-red-500';
    return 'text-gray-500';
  };

  const getChangeAriaLabel = () => {
    if (change === undefined) return '';
    const direction = changeType === 'up' ? '上升' : changeType === 'down' ? '下降' : '持平';
    return `变化趋势：${direction} ${Math.abs(change)}%`;
  };

  // 加载状态
  if (loading) {
    return (
      <div className="metric-card animate-pulse" role="status" aria-label="加载中">
        <div className="flex items-center justify-between mb-4">
          <div className="w-8 h-8 bg-gray-600 rounded-lg"></div>
          <div className="w-16 h-4 bg-gray-600 rounded"></div>
        </div>
        <div className="w-24 h-8 bg-gray-600 rounded mb-2"></div>
        <div className="w-32 h-4 bg-gray-600 rounded"></div>
      </div>
    );
  }

  return (
    <div
      className={`metric-card ${colorClasses[color]} ${onClick ? 'cursor-pointer' : ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
      role={onClick ? "button" : "article"}
      tabIndex={onClick ? 0 : undefined}
      aria-label={onClick ? `${title}: ${value}` : undefined}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="p-2 bg-white bg-opacity-10 rounded-lg">
          {icon}
        </div>
        {change !== undefined && (
          <div
            className={`flex items-center text-sm font-medium ${getChangeColor()}`}
            aria-label={getChangeAriaLabel()}
          >
            {getTrendIcon()}
            <span className="ml-1">{formatChange(change)}</span>
          </div>
        )}
      </div>

      <div className="space-y-1">
        <h3 className="text-2xl font-bold text-white">
          {formatNumber(value)}
        </h3>
        <p className="text-sm text-gray-300">{title}</p>
        {description && (
          <p className="text-xs text-gray-400 mt-2">{description}</p>
        )}
      </div>

      {/* 装饰性背景效果 */}
      {isHovered && (
        <div className="absolute inset-0 bg-gradient-to-br from-white to-transparent opacity-5 rounded-2xl pointer-events-none" />
      )}
    </div>
  );
};