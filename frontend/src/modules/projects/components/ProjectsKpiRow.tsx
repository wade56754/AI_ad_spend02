/**
 * ProjectsKpiRow - 项目模块 KPI 指标行
 *
 * 显示项目关键指标：总项目数、活跃项目、总预算、总消耗
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { Briefcase, TrendingUp, DollarSign, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ProjectSummary } from '../types';

interface ProjectsKpiRowProps {
  summary: ProjectSummary;
  loading?: boolean;
  className?: string;
}

export function ProjectsKpiRow({ summary, loading, className }: ProjectsKpiRowProps) {
  const metrics = [
    {
      id: 'total_projects',
      title: '总项目数',
      value: summary.total_projects.toString(),
      icon: Briefcase,
      priority: 'secondary' as const,
    },
    {
      id: 'active_projects',
      title: '活跃项目',
      value: summary.active_projects.toString(),
      icon: Activity,
      priority: 'primary' as const,
      color: 'success',
    },
    {
      id: 'total_budget',
      title: '总预算',
      value: `¥${(summary.total_budget / 100).toLocaleString()}`,
      icon: DollarSign,
      priority: 'primary' as const,
    },
    {
      id: 'total_spent',
      title: '总消耗',
      value: `¥${(summary.total_spent / 100).toLocaleString()}`,
      description: `今日: ¥${(summary.today_spent / 100).toLocaleString()}`,
      icon: TrendingUp,
      priority: 'primary' as const,
    },
  ];

  if (loading) {
    return (
      <div className={cn('grid grid-cols-12 gap-4', className)}>
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="col-span-12 sm:col-span-6 lg:col-span-3 h-24 rounded-lg bg-card-bg border border-border-default animate-pulse"
          />
        ))}
      </div>
    );
  }

  return (
    <div className={cn('grid grid-cols-12 gap-4', className)}>
      {metrics.map((metric) => {
        const IconComponent = metric.icon;
        const isPrimary = metric.priority === 'primary';

        return (
          <div
            key={metric.id}
            className={cn(
              'col-span-12 sm:col-span-6 lg:col-span-3',
              'rounded-lg border p-4 transition-all duration-200',
              'bg-card-bg border-border-default',
              'hover:bg-elevated hover:border-border-muted hover:shadow-md'
            )}
          >
            <div className="flex justify-between items-start mb-3">
              <div
                className={cn(
                  'p-2 rounded-lg',
                  isPrimary ? 'bg-accent/10' : 'bg-elevated'
                )}
              >
                <IconComponent
                  className={cn(
                    'w-5 h-5',
                    metric.color === 'success' ? 'text-success' :
                    isPrimary ? 'text-accent' : 'text-text-muted'
                  )}
                />
              </div>
            </div>

            <div>
              <div className="text-text-muted text-xs font-medium uppercase tracking-wider mb-1.5">
                {metric.title}
              </div>
              <div className="flex items-baseline gap-2">
                <span
                  className={cn(
                    'font-bold tracking-tight text-text-strong',
                    isPrimary ? 'text-2xl' : 'text-xl'
                  )}
                >
                  {metric.value}
                </span>
                {metric.description && (
                  <span className="text-xs text-text-muted">{metric.description}</span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default ProjectsKpiRow;
