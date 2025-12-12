'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import {
  RefreshCw,
  TrendingUp,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign,
  Activity as ActivityIcon,
  Target,
  Plus
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DataStateManager } from '@/components/ui/data-state';

// 从数据配置文件导入接口
import type { Activity, QuickAction } from '@/data/dashboardData';

interface RightColumnProps {
  activities?: Activity[];
  quickActions?: QuickAction[];
  className?: string;
  loading?: boolean;
  error?: string;
  onRefresh?: () => void;
}

// 获取活动图标
const getActivityIcon = (type: Activity['type']) => {
  const iconClass = "w-4 h-4";
  switch (type) {
    case "project":
      return <Target className={`${iconClass} text-blue-600 dark:text-blue-400`} />;
    case "account":
      return <DollarSign className={`${iconClass} text-green-600 dark:text-green-400`} />;
    case "report":
      return <FileText className={`${iconClass} text-purple-600 dark:text-purple-400`} />;
    case "payment":
      return <ActivityIcon className={`${iconClass} text-yellow-600 dark:text-yellow-400`} />;
    case "approval":
      return <CheckCircle className={`${iconClass} text-indigo-600 dark:text-indigo-400`} />;
    default:
      return <ActivityIcon className={`${iconClass} text-gray-600 dark:text-gray-400`} />;
  }
};

// 获取状态图标
const getStatusIcon = (status: Activity['status']) => {
  const iconClass = "w-4 h-4";
  switch (status) {
    case 'success':
      return <CheckCircle className={`${iconClass} text-green-500`} />;
    case 'warning':
      return <AlertTriangle className={`${iconClass} text-yellow-500`} />;
    case 'error':
      return <AlertTriangle className={`${iconClass} text-red-500`} />;
    case 'pending':
      return <Clock className={`${iconClass} text-blue-500`} />;
    default:
      return null;
  }
};

// 格式化时间
const formatTime = (timestamp: string) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return `${diffMins}分钟前`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}小时前`;
  return `${Math.floor(diffMins / 1440)}天前`;
};

export default function RightColumn({
  activities: externalActivities,
  quickActions: externalQuickActions,
  className = '',
  loading: externalLoading,
  error: externalError,
  onRefresh
}: RightColumnProps) {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [quickActions, setQuickActions] = useState<QuickAction[]>([]);
  const [loading, setLoading] = useState(false);
  const [internalError, setInternalError] = useState<string>();

  // 模拟数据加载
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setInternalError(undefined);

      // 模拟API调用延迟
      await new Promise(resolve => setTimeout(resolve, 600));

      // 如果外部已提供数据，直接使用
      if (externalActivities !== undefined) {
        setActivities(externalActivities);
      } else {
        // 否则使用默认数据（从dashboardData导入）
        const { activityData } = await import('@/data/dashboardData');
        setActivities(activityData);
      }

      if (externalQuickActions !== undefined) {
        setQuickActions(externalQuickActions);
      } else {
        const { quickActionData } = await import('@/data/dashboardData');
        setQuickActions(quickActionData);
      }
    } catch (err) {
      setInternalError('加载侧边栏数据失败');
      console.error('Failed to load right column data:', err);
    } finally {
      setLoading(false);
    }
  }, [externalActivities, externalQuickActions]);

  // 组件挂载时加载数据（仅在没有外部数据时）
  // 合并两个 useEffect 为一个，避免重复同步逻辑
  useEffect(() => {
    // 如果有外部数据，直接使用
    if (externalActivities !== undefined) {
      setActivities(externalActivities);
    }
    if (externalQuickActions !== undefined) {
      setQuickActions(externalQuickActions);
    }
    // 只有当没有外部数据时才加载内部数据
    if (externalActivities === undefined || externalQuickActions === undefined) {
      loadData();
    }
  }, [externalActivities, externalQuickActions, loadData]);

  // 统一状态管理
  const isLoading = externalLoading ?? loading;
  const currentError = externalError ?? internalError;

  // 渲染快速操作部分
  const renderQuickActions = () => (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 animate-fadeIn">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">快速操作</h3>
        <Plus className="w-5 h-5 text-gray-400" />
      </div>
      <div className="space-y-3">
        {quickActions.map((action) => {
          const Icon = action.icon;
          return (
            <Link
              key={action.id}
              href={action.href}
              className={cn(
                'flex items-center space-x-3 p-3 rounded-lg',
                'hover:bg-gray-50 dark:hover:bg-gray-700',
                'transition-colors duration-200',
                'group'
              )}
            >
              <div className={cn(
                'w-10 h-10 rounded-lg flex items-center justify-center',
                action.color,
                'group-hover:scale-110 transition-transform duration-200'
              )}>
                {React.createElement(Icon, { className: "w-5 h-5 text-white" })}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {action.title}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {action.description}
                </p>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );

  // 渲染最近活动部分
  const renderRecentActivities = () => (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 animate-fadeIn">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">最近活动</h3>
        <div className="flex items-center space-x-2">
          <Link href="/activities" className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
            查看全部
          </Link>
          {onRefresh && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onRefresh}
              className="h-6 px-2 text-gray-400 hover:text-gray-600"
            >
              <RefreshCw className="w-3 h-3" />
            </Button>
          )}
        </div>
      </div>
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {activities.map((activity, index) => (
          <div
            key={activity.id}
            className="flex items-start space-x-3 animate-fadeIn"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="flex-shrink-0 mt-0.5">
              {getActivityIcon(activity.type)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <p className="text-sm text-gray-900 dark:text-white">
                  {activity.title}
                </p>
                {getStatusIcon(activity.status)}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                {activity.description}
              </p>
              {activity.amount && (
                <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
                  ￥{activity.amount.toLocaleString()}
                </p>
              )}
              {activity.user && (
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  {activity.user}
                </p>
              )}
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                {formatTime(activity.timestamp)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // 渲染系统状态部分
  const renderSystemStatus = () => (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 animate-fadeIn">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">系统状态</h3>
        <CheckCircle className="w-5 h-5 text-green-500" />
      </div>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600 dark:text-gray-400">API状态</span>
          <span className="text-sm font-medium text-green-600 dark:text-green-400">正常</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600 dark:text-gray-400">数据库</span>
          <span className="text-sm font-medium text-green-600 dark:text-green-400">连接</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600 dark:text-gray-400">响应时间</span>
          <span className="text-sm font-medium text-blue-600 dark:text-blue-400">120ms</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600 dark:text-gray-400">CPU使用率</span>
          <span className="text-sm font-medium text-yellow-600 dark:text-yellow-400">45%</span>
        </div>
      </div>
    </div>
  );

  // 渲染主要内容
  const renderContent = () => (
    <div className={cn('space-y-6', className)}>
      {renderQuickActions()}
      {renderRecentActivities()}
      {renderSystemStatus()}
    </div>
  );

  // 空状态内容
  const renderEmptyState = () => (
    <div className={cn('text-center py-8', className)}>
      <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
        <Clock className="w-8 h-8 text-gray-400" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        暂无活动
      </h3>
      <p className="text-gray-600 dark:text-gray-400 mb-4">
        系统还没有任何活动记录
      </p>
      <Button variant="outline" onClick={onRefresh || loadData} className="gap-2">
        <RefreshCw className="w-4 h-4" />
        刷新数据
      </Button>
    </div>
  );

  return (
    <DataStateManager
      loading={isLoading}
      error={currentError}
      data={activities}
      emptyType="no-items"
      errorType="server"
      onRetry={onRefresh || loadData}
      onRefresh={onRefresh || loadData}
      emptyContent={renderEmptyState()}
      minHeight="400px"
    >
      {renderContent()}
    </DataStateManager>
  );
}