'use client';

import React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  FolderKanban,
  CreditCard,
  Users,
  FileText,
  DollarSign,
  BarChart3,
  Target,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';

// 从数据配置文件导入Module接口
import { Module } from '@/data/dashboardData';

interface ModuleGridProps {
  modules: Module[];
  className?: string;
}

// 数据驱动的统计信息格式化函数
const formatModuleStats = (module: Module) => {
  const { stats, statsLabel } = module;

  if (stats.active !== undefined && stats.total !== undefined) {
    return `${stats.active}/${stats.total} ${statsLabel}`;
  }

  if (stats.pending !== undefined) {
    return `${stats.pending} 个待处理`;
  }

  if (stats.completed !== undefined) {
    return `${stats.completed} 个已完成`;
  }

  if (stats.reports !== undefined) {
    return `${stats.reports} 个报告`;
  }

  return '暂无数据';
};

// 获取状态图标
const getStatusIcon = (status: Module['status']) => {
  switch (status) {
    case 'active':
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'warning':
      return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    case 'error':
      return <AlertCircle className="w-4 h-4 text-red-500" />;
    default:
      return null;
  }
};

// 获取状态文本
const getStatusText = (status: Module['status']) => {
  switch (status) {
    case 'active':
      return '正常';
    case 'warning':
      return '警告';
    case 'error':
      return '异常';
    default:
      return '';
  }
};

export default function ModuleGrid({ modules, className = '' }: ModuleGridProps) {
  return (
    <div className={cn('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8', className)}>
      {modules.map((module) => {
        const Icon = module.icon;
        return (
          <Link
            key={module.id}
            href={module.href}
            className={cn(
              'group relative bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6',
              'hover:shadow-lg hover:border-blue-200 dark:hover:border-blue-800',
              'transition-all duration-300 ease-in-out',
              'hover:-translate-y-1 hover:scale-[1.02]',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
              module.status === 'error' && 'border-red-200 dark:border-red-800',
              module.status === 'warning' && 'border-yellow-200 dark:border-yellow-800'
            )}
            aria-label={`${module.title} - ${module.description}`}
          >
            {/* 模块图标 */}
            <div className={cn(
              'w-12 h-12 rounded-xl flex items-center justify-center mb-4',
              module.gradient,
              'group-hover:scale-110 transition-transform duration-300'
            )}>
              {React.createElement(Icon, { className: "w-6 h-6 text-white" })}
            </div>

            {/* 状态指示器 */}
            <div className="absolute top-4 right-4 flex items-center space-x-1">
              {getStatusIcon(module.status)}
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {getStatusText(module.status)}
              </span>
            </div>

            {/* 模块标题和描述 */}
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
              {module.title}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
              {module.description}
            </p>

            {/* 统计信息 */}
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {formatModuleStats(module)}
              </span>
              {module.trend !== 0 && (
                <span className={cn(
                  'text-xs font-medium flex items-center',
                  module.trend > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                )}>
                  {module.trend > 0 ? '+' : ''}{module.trend}%
                </span>
              )}
            </div>

            {/* 悬停时的渐变背景 */}
            <div className={cn(
              'absolute inset-0 rounded-xl opacity-0 group-hover:opacity-5 transition-opacity duration-300',
              module.gradient
            )} />
          </Link>
        );
      })}
    </div>
  );
}