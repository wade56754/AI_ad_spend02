'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { Plus, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { DataStateManager } from '@/components/ui/data-state';

// 从数据配置文件导入Module接口和数据
import { Module, moduleData } from '@/data/dashboardData';

interface ModuleGridProps {
  modules?: Module[];
  className?: string;
  loading?: boolean;
  error?: string;
  onRefresh?: () => void;
  onCreateModule?: () => void;
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

export default function ModuleGrid({
  modules: externalModules,
  className = '',
  loading: externalLoading,
  error: externalError,
  onRefresh,
  onCreateModule
}: ModuleGridProps) {
  const [modules, setModules] = useState<Module[]>([]);
  const [loading, setLoading] = useState(false);
  const [internalError, setInternalError] = useState<string>();

  // 模拟数据加载
  const loadModulesData = useCallback(async () => {
    try {
      setLoading(true);
      setInternalError(undefined);

      // 模拟API调用延迟
      await new Promise(resolve => setTimeout(resolve, 800));

      // 如果外部已提供模块数据，直接使用
      if (externalModules) {
        setModules(externalModules);
        return;
      }

      // 否则使用默认模块数据（从静态导入获取）
      setModules(moduleData);
    } catch (err) {
      setInternalError('加载模块列表失败');
      console.error('Failed to load modules:', err);
    } finally {
      setLoading(false);
    }
  }, [externalModules]);

  // 组件挂载时加载数据（仅在没有外部数据时）
  // 移除了重复的 useEffect 同步，因为 loadModulesData 已经处理了 externalModules
  useEffect(() => {
    // 如果有外部数据，直接使用，不需要加载
    if (externalModules !== undefined) {
      setModules(externalModules);
    } else {
      loadModulesData();
    }
  }, [externalModules, loadModulesData]);

  // 统一状态管理
  const isLoading = externalLoading ?? loading;
  const currentError = externalError ?? internalError;

  // 渲染模块网格内容
  const renderModulesGrid = () => (
    <div className={cn('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6', className)}>
      {modules.map((module, index) => {
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
              'animate-fadeIn',
              module.status === 'error' && 'border-red-200 dark:border-red-800',
              module.status === 'warning' && 'border-yellow-200 dark:border-yellow-800'
            )}
            style={{ animationDelay: `${index * 100}ms` }}
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

      {/* 创建新模块卡片 */}
      {onCreateModule && (
        <div className={cn(
          'bg-white dark:bg-gray-800 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600 p-6',
          'flex flex-col items-center justify-center min-h-[200px]',
          'hover:border-blue-400 dark:hover:border-blue-600 hover:bg-gray-50 dark:hover:bg-gray-750',
          'transition-all duration-300 cursor-pointer animate-fadeIn',
          'group'
        )}
        style={{ animationDelay: `${modules.length * 100}ms` }}
        onClick={onCreateModule}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onCreateModule();
          }
        }}
        >
          <Plus className="w-12 h-12 text-gray-400 group-hover:text-blue-500 transition-colors mb-3" />
          <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors mb-2">
            创建模块
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
            添加新的功能模块
          </p>
        </div>
      )}
    </div>
  );

  // 空状态内容
  const renderEmptyState = () => (
    <div className={cn('text-center py-16', className)}>
      <div className="w-20 h-20 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
        <Plus className="w-10 h-10 text-gray-400" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
        还没有模块
      </h3>
      <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
        创建第一个模块开始使用系统功能，或联系管理员为您分配模块权限。
      </p>
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-center">
        {onCreateModule && (
          <Button onClick={onCreateModule} className="gap-2">
            <Plus className="w-4 h-4" />
            创建模块
          </Button>
        )}
        <Button variant="outline" onClick={onRefresh || loadModulesData} className="gap-2">
          <RefreshCw className="w-4 h-4" />
          刷新列表
        </Button>
      </div>
    </div>
  );

  return (
    <DataStateManager
      loading={isLoading}
      error={currentError}
      data={modules}
      emptyType="no-items"
      errorType="server"
      onRetry={onRefresh || loadModulesData}
      onRefresh={onRefresh || loadModulesData}
      emptyContent={renderEmptyState()}
      minHeight="300px"
    >
      {renderModulesGrid()}
    </DataStateManager>
  );
}