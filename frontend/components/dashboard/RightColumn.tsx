'use client';

import React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import {
  TrendingUp,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign,
  Activity as ActivityIcon,
  Target,
  ArrowUpRight,
  ArrowDownRight,
  Plus
} from 'lucide-react';

// 从数据配置文件导入接口
import type { Activity, QuickAction } from '@/data/dashboardData';

interface RightColumnProps {
  activities: Activity[];
  quickActions: QuickAction[];
  className?: string;
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

export default function RightColumn({ activities, quickActions, className = '' }: RightColumnProps) {
  return (
    <div className={cn('space-y-6', className)}>
      {/* 快速操作 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
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

      {/* 最近活动 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">最近活动</h3>
          <Link href="/activities" className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
            查看全部
          </Link>
        </div>
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {activities.map((activity) => (
            <div key={activity.id} className="flex items-start space-x-3">
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

      {/* 系统状态 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
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
    </div>
  );
}