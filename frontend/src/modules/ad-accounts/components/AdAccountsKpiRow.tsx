/**
 * AdAccountsKpiRow - 广告账户模块 KPI 指标行
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { Users, Activity, Wallet, TrendingUp, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatMoney } from '@/lib/utils/formatters';
import type { AdAccountSummary } from '../types';

interface AdAccountsKpiRowProps {
  summary: AdAccountSummary;
  loading?: boolean;
  className?: string;
}

export function AdAccountsKpiRow({ summary, loading, className }: AdAccountsKpiRowProps) {
  const metrics = [
    {
      id: 'total_accounts',
      title: '总账户数',
      value: summary.total_accounts.toString(),
      icon: Users,
      priority: 'secondary' as const,
    },
    {
      id: 'active_accounts',
      title: '活跃账户',
      value: summary.active_accounts.toString(),
      icon: Activity,
      priority: 'primary' as const,
      color: 'success',
    },
    {
      id: 'total_balance',
      title: '总余额',
      value: `¥${formatMoney(summary.total_balance)}`,
      icon: Wallet,
      priority: 'primary' as const,
    },
    {
      id: 'spent_today',
      title: '今日消耗',
      value: `¥${formatMoney(summary.total_spent_today)}`,
      icon: TrendingUp,
      priority: 'primary' as const,
    },
    {
      id: 'high_risk',
      title: '高风险',
      value: summary.high_risk_count.toString(),
      icon: AlertTriangle,
      priority: 'secondary' as const,
      isAlert: summary.high_risk_count > 0,
    },
  ];

  if (loading) {
    return (
      <div className={cn('grid grid-cols-12 gap-4', className)}>
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className={cn(
              'col-span-12 sm:col-span-6 h-24 rounded-lg bg-card-bg border border-border-default animate-pulse',
              i <= 2 ? 'lg:col-span-2' : i === 5 ? 'lg:col-span-2' : 'lg:col-span-3'
            )}
          />
        ))}
      </div>
    );
  }

  return (
    <div className={cn('grid grid-cols-12 gap-4', className)}>
      {metrics.map((metric, index) => {
        const IconComponent = metric.icon;
        const isPrimary = metric.priority === 'primary';
        // First 2 cards: col-span-2, last card: col-span-2, middle 2: col-span-3
        const lgColSpan = index < 2 ? 2 : index === 4 ? 2 : 3;

        return (
          <div
            key={metric.id}
            className={cn(
              'col-span-12 sm:col-span-6',
              `lg:col-span-${lgColSpan}`,
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
                  isPrimary ? 'bg-accent/10' : 'bg-elevated'
                )}
              >
                <IconComponent
                  className={cn(
                    'w-5 h-5',
                    metric.isAlert ? 'text-danger' :
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

export default AdAccountsKpiRow;
