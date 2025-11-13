'use client';

import React from 'react';
import { DollarSign, TrendingUp, Users, FileText, Activity, Target } from 'lucide-react';
import { cn } from '@/lib/utils';
import { MetricCard } from '@/components/ui/MetricCard';

interface DashboardStatsProps {
  className?: string;
}

export default function DashboardStats({ className = '' }: DashboardStatsProps) {
  const stats = [
    {
      title: '今日消耗',
      value: '￥12,845',
      change: '+8.2%',
      changeType: 'up' as const,
      description: '相比昨日增长',
      icon: DollarSign,
      color: 'primary' as const
    },
    {
      title: '活跃项目',
      value: '24',
      change: '+3',
      changeType: 'up' as const,
      description: '本周新增项目',
      icon: Target,
      color: 'success' as const
    },
    {
      title: 'ROI',
      value: '3.24',
      change: '+0.15',
      changeType: 'up' as const,
      description: '投资回报率',
      icon: TrendingUp,
      color: 'info' as const
    },
    {
      title: '账户总数',
      value: '156',
      change: '+12',
      changeType: 'up' as const,
      description: '本月新增账户',
      icon: Users,
      color: 'warning' as const
    },
    {
      title: '待审日报',
      value: '18',
      change: '-5',
      changeType: 'down' as const,
      description: '需要审核',
      icon: FileText,
      color: 'error' as const
    },
    {
      title: '转化率',
      value: '2.8%',
      change: '+0.3%',
      changeType: 'up' as const,
      description: '平均转化率',
      icon: Activity,
      color: 'success' as const
    }
  ];

  return (
    <div className={cn('grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6', className)}>
      {stats.map((stat, index) => (
        <MetricCard
          key={index}
          {...stat}
          size="sm"
          className="hover:shadow-lg transition-all duration-200"
        />
      ))}
    </div>
  );
}