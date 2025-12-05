/**
 * ReconciliationKpiRow - 对账模块 KPI 指标行
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { CheckSquare, Clock, CheckCircle, AlertTriangle, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ReconciliationSummary {
  total: number;
  pending: number;
  matched: number;
  has_diff: number;
  resolved: number;
}

interface ReconciliationKpiRowProps {
  summary: ReconciliationSummary;
  loading?: boolean;
  className?: string;
}

export function ReconciliationKpiRow({ summary, loading, className }: ReconciliationKpiRowProps) {
  const metrics = [
    {
      id: 'total',
      title: '总批次',
      value: summary.total.toString(),
      icon: CheckSquare,
      priority: 'secondary' as const,
    },
    {
      id: 'pending',
      title: '待对账',
      value: summary.pending.toString(),
      icon: Clock,
      priority: 'primary' as const,
      color: 'warning',
    },
    {
      id: 'has_diff',
      title: '有差异',
      value: summary.has_diff.toString(),
      icon: AlertTriangle,
      priority: 'primary' as const,
      isAlert: summary.has_diff > 0,
    },
    {
      id: 'matched',
      title: '已匹配',
      value: summary.matched.toString(),
      icon: CheckCircle,
      priority: 'primary' as const,
      color: 'success',
    },
    {
      id: 'resolved',
      title: '已解决',
      value: summary.resolved.toString(),
      icon: Check,
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

export default ReconciliationKpiRow;
