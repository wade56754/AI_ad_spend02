'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { DollarSign, TrendingUp, Users, FileText, Activity, Target } from 'lucide-react';
import { cn } from '@/lib/utils';
import { MetricCard } from '@/components/ui/MetricCard';
import { DataStateManager } from '@/components/ui/data-state';

interface DashboardStatsProps {
  className?: string;
  loading?: boolean;
  error?: string;
  onRefresh?: () => void;
}

interface StatData {
  title: string;
  value: string;
  change: number;
  changeType: 'up' | 'down';
  description: string;
  icon: any;
  color: 'primary' | 'success' | 'warning' | 'error' | 'info';
}

export default function DashboardStats({
  className = '',
  loading: externalLoading,
  error,
  onRefresh
}: DashboardStatsProps) {
  const [stats, setStats] = useState<StatData[]>([]);
  const [loading, setLoading] = useState(false);
  const [internalError, setInternalError] = useState<string>();

  // 模拟数据加载
  const loadStatsData = useCallback(async () => {
    try {
      setLoading(true);
      setInternalError(undefined);

      // 模拟API调用延迟
      await new Promise(resolve => setTimeout(resolve, 1000));

      const statsData: StatData[] = [
        {
          title: '今日消耗',
          value: '￥12,845',
          change: 8.2,
          changeType: 'up',
          description: '相比昨日增长',
          icon: DollarSign,
          color: 'primary'
        },
        {
          title: '活跃项目',
          value: '24',
          change: 3,
          changeType: 'up',
          description: '本周新增项目',
          icon: Target,
          color: 'success'
        },
        {
          title: 'ROI',
          value: '3.24',
          change: 0.15,
          changeType: 'up',
          description: '投资回报率',
          icon: TrendingUp,
          color: 'info'
        },
        {
          title: '账户总数',
          value: '156',
          change: 12,
          changeType: 'up',
          description: '本月新增账户',
          icon: Users,
          color: 'warning'
        },
        {
          title: '待审日报',
          value: '18',
          change: -5,
          changeType: 'down',
          description: '需要审核',
          icon: FileText,
          color: 'error'
        },
        {
          title: '转化率',
          value: '2.8%',
          change: 0.3,
          changeType: 'up',
          description: '平均转化率',
          icon: Activity,
          color: 'success'
        }
      ];

      setStats(statsData);
    } catch (err) {
      setInternalError('加载统计数据失败');
      console.error('Failed to load dashboard stats:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 组件挂载时加载数据
  useEffect(() => {
    loadStatsData();
  }, [loadStatsData]);

  // 统一状态管理
  const isLoading = externalLoading ?? loading;
  const currentError = error ?? internalError;

  // 渲染统计指标内容
  const renderStatsContent = () => (
    <div className={cn('grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4', className)}>
      {stats.map((stat, index) => (
        <div key={index} style={{ animationDelay: `${index * 50}ms` }}>
          <MetricCard
            {...stat}
            size="sm"
            className="hover:shadow-lg transition-all duration-200 animate-fadeIn"
          />
        </div>
      ))}
    </div>
  );

  // 骨架屏加载内容
  const renderSkeletonContent = () => (
    <div className={cn('grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4', className)}>
      {Array.from({ length: 6 }, (_, index) => (
        <div
          key={index}
          className="animate-fadeIn"
          style={{ animationDelay: `${index * 50}ms` }}
        >
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="w-6 h-6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
              <div className="w-12 h-2 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            </div>
            <div className="space-y-2">
              <div className="h-6 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
              <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
              <div className="h-3 w-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <DataStateManager
      loading={isLoading}
      error={currentError}
      data={stats}
      loadingType="skeleton"
      skeletonCount={6}
      errorType="server"
      onRetry={onRefresh || loadStatsData}
      onRefresh={onRefresh || loadStatsData}
      loadingContent={renderSkeletonContent()}
      minHeight="200px"
    >
      {renderStatsContent()}
    </DataStateManager>
  );
}