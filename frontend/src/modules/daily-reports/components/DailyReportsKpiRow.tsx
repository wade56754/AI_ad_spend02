/**
 * DailyReportsKpiRow - 日报模块 KPI 指标行
 *
 * 显示各状态日报数量
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { FileText, Clock, AlertTriangle, CheckCircle, Lock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DailyReportsSummary {
  total: number;
  raw_submitted: number;
  trend_pending: number;
  trend_flagged: number;
  final_pending: number;
  final_confirmed: number;
  final_locked: number;
}

interface DailyReportsKpiRowProps {
  summary: DailyReportsSummary;
  loading?: boolean;
  className?: string;
}

export function DailyReportsKpiRow({ summary, loading, className }: DailyReportsKpiRowProps) {
  const metrics = [
    {
      id: 'total',
      title: '总日报',
      value: summary.total.toString(),
      icon: FileText,
      priority: 'secondary' as const,
    },
    {
      id: 'pending',
      title: '待审核',
      value: (summary.trend_pending + summary.final_pending).toString(),
      icon: Clock,
      priority: 'primary' as const,
      color: 'warning',
    },
    {
      id: 'flagged',
      title: '异常待处理',
      value: summary.trend_flagged.toString(),
      icon: AlertTriangle,
      priority: 'primary' as const,
      isAlert: summary.trend_flagged > 0,
    },
    {
      id: 'confirmed',
      title: '已确认',
      value: summary.final_confirmed.toString(),
      icon: CheckCircle,
      priority: 'primary' as const,
      color: 'success',
    },
    {
      id: 'locked',
      title: '已锁定',
      value: summary.final_locked.toString(),
      icon: Lock,
      priority: 'secondary' as const,
    },
  ];

  if (loading) {
    return (
      <div className={cn('grid grid-cols-12 gap-4', className)}>
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="col-span-12 sm:col-span-6 lg:col-span-2 h-24 rounded-lg bg-card-bg border border-border-default animate-pulse"
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
              'col-span-12 sm:col-span-6 lg:col-span-2',
              'rounded-lg border p-4 transition-all duration-200',
              'bg-card-bg border-border-default',
              'hover:bg-elevated hover:border-border-muted hover:shadow-md',
              metric.isAlert && 'border-l-4 border-l-danger'
            )}
          >
            <div className="flex justify-between items-start mb-3">
              <div
                className={cn(
                  'p-2 rounded-lg',
                  metric.isAlert ? 'bg-danger/10' :
                  metric.color === 'success' ? 'bg-success/10' :
                  metric.color === 'warning' ? 'bg-warning/10' :
                  isPrimary ? 'bg-accent/10' : 'bg-elevated'
                )}
              >
                <IconComponent
                  className={cn(
                    'w-5 h-5',
                    metric.isAlert ? 'text-danger' :
                    metric.color === 'success' ? 'text-success' :
                    metric.color === 'warning' ? 'text-warning' :
                    isPrimary ? 'text-accent' : 'text-text-muted'
                  )}
                />
              </div>
            </div>

            <div>
              <div className="text-text-muted text-xs font-medium uppercase tracking-wider mb-1.5">
                {metric.title}
              </div>
              <span
                className={cn(
                  'font-bold tracking-tight',
                  isPrimary ? 'text-2xl' : 'text-xl',
                  metric.isAlert ? 'text-danger' : 'text-text-strong'
                )}
              >
                {metric.value}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default DailyReportsKpiRow;
