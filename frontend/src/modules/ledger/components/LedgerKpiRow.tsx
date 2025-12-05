/**
 * LedgerKpiRow - 账本模块 KPI 指标行
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { BookOpen, ArrowUpCircle, ArrowDownCircle, Wallet } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LedgerSummary {
  total_entries: number;
  total_credit: number;
  total_debit: number;
  balance: number;
}

interface LedgerKpiRowProps {
  summary: LedgerSummary;
  loading?: boolean;
  className?: string;
}

export function LedgerKpiRow({ summary, loading, className }: LedgerKpiRowProps) {
  const metrics = [
    {
      id: 'total_entries',
      title: '总流水',
      value: summary.total_entries.toString(),
      icon: BookOpen,
      priority: 'secondary' as const,
    },
    {
      id: 'total_credit',
      title: '总收入',
      value: `¥${(summary.total_credit / 100).toLocaleString()}`,
      icon: ArrowUpCircle,
      priority: 'primary' as const,
      color: 'success',
    },
    {
      id: 'total_debit',
      title: '总支出',
      value: `¥${(summary.total_debit / 100).toLocaleString()}`,
      icon: ArrowDownCircle,
      priority: 'primary' as const,
      color: 'danger',
    },
    {
      id: 'balance',
      title: '当前余额',
      value: `¥${(summary.balance / 100).toLocaleString()}`,
      icon: Wallet,
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
                  metric.color === 'success' ? 'bg-success/10' :
                  metric.color === 'danger' ? 'bg-danger/10' :
                  isPrimary ? 'bg-accent/10' : 'bg-elevated'
                )}
              >
                <IconComponent
                  className={cn(
                    'w-5 h-5',
                    metric.color === 'success' ? 'text-success' :
                    metric.color === 'danger' ? 'text-danger' :
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
                  metric.color === 'success' ? 'text-success' :
                  metric.color === 'danger' ? 'text-danger' :
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

export default LedgerKpiRow;
