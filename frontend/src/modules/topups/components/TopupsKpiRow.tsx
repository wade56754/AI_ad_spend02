/**
 * TopupsKpiRow - 充值模块 KPI 指标行
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { DollarSign, Clock, CheckCircle, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TopupsSummary {
  total: number;
  pending: number;
  approved: number;
  completed: number;
  total_amount: number;
}

interface TopupsKpiRowProps {
  summary: TopupsSummary;
  loading?: boolean;
  className?: string;
}

export function TopupsKpiRow({ summary, loading, className }: TopupsKpiRowProps) {
  const metrics = [
    {
      id: 'total',
      title: '总充值',
      value: summary.total.toString(),
      icon: DollarSign,
      priority: 'secondary' as const,
    },
    {
      id: 'pending',
      title: '待审批',
      value: summary.pending.toString(),
      icon: Clock,
      priority: 'primary' as const,
      color: 'warning',
      isAlert: summary.pending > 0,
    },
    {
      id: 'completed',
      title: '已完成',
      value: summary.completed.toString(),
      icon: CheckCircle,
      priority: 'primary' as const,
      color: 'success',
    },
    {
      id: 'total_amount',
      title: '总金额',
      value: `¥${(summary.total_amount / 100).toLocaleString()}`,
      icon: DollarSign,
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
              'hover:bg-elevated hover:border-border-muted hover:shadow-md',
              metric.isAlert && 'border-l-4 border-l-warning'
            )}
          >
            <div className="flex justify-between items-start mb-3">
              <div
                className={cn(
                  'p-2 rounded-lg',
                  metric.isAlert ? 'bg-warning/10' :
                  metric.color === 'success' ? 'bg-success/10' :
                  isPrimary ? 'bg-accent/10' : 'bg-elevated'
                )}
              >
                <IconComponent
                  className={cn(
                    'w-5 h-5',
                    metric.isAlert ? 'text-warning' :
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
              <span
                className={cn(
                  'font-bold tracking-tight',
                  isPrimary ? 'text-2xl' : 'text-xl',
                  'text-text-strong'
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

export default TopupsKpiRow;
