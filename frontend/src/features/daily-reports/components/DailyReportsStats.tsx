/**
 * DailyReportsStats Component
 *
 * KPI 卡片 - 从 DailyReportsPage.tsx 提取
 * v3.0 去边框+投影+色块图标
 *
 * SoT: docs/10.module-specs/B2-daily-report-review.md
 */

'use client';

import React from 'react';
import { FileText, Clock, AlertTriangle, Lock } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { DailyReportStatus } from '../types';

// ============ Color Config ============

const colorConfig = {
  slate: { iconBg: 'bg-slate-100', iconColor: 'text-slate-600' },
  blue: { iconBg: 'bg-blue-50', iconColor: 'text-blue-600' },
  amber: { iconBg: 'bg-amber-50', iconColor: 'text-amber-600' },
  red: { iconBg: 'bg-red-50', iconColor: 'text-red-600' },
  green: { iconBg: 'bg-green-50', iconColor: 'text-green-600' },
};

type StatColor = keyof typeof colorConfig;

// ============ StatCard Component ============

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  color: StatColor;
  isActive?: boolean;
  onClick?: () => void;
}

function StatCard({ title, value, icon: Icon, color, isActive, onClick }: StatCardProps) {
  const colors = colorConfig[color];

  return (
    <div
      className={cn(
        'bg-white rounded-xl p-5 cursor-pointer transition-all duration-200',
        'shadow-sm hover:shadow-md',
        isActive && 'ring-2 ring-primary ring-offset-2'
      )}
      onClick={onClick}
      data-testid={`stat-card-${title}`}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">
            {title}
          </p>
          <p className="text-3xl font-bold text-gray-900 tabular-nums tracking-tight">
            {value.toLocaleString()}
          </p>
        </div>
        <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center', colors.iconBg)}>
          <Icon className={cn('h-5 w-5', colors.iconColor)} />
        </div>
      </div>
    </div>
  );
}

// ============ DailyReportsStats Component ============

interface DailyReportsStatsProps {
  totalReports: number;
  pendingCount: number;
  flaggedCount: number;
  lockedCount: number;
  statusFilter: DailyReportStatus | 'all';
  onStatusFilter: (status: DailyReportStatus | 'all') => void;
  className?: string;
}

export function DailyReportsStats({
  totalReports,
  pendingCount,
  flaggedCount,
  lockedCount,
  statusFilter,
  onStatusFilter,
  className,
}: DailyReportsStatsProps) {
  return (
    <div className={cn('grid grid-cols-2 lg:grid-cols-4 gap-4', className)} data-testid="daily-reports-stats">
      <StatCard
        title="总日报"
        value={totalReports}
        icon={FileText}
        color="slate"
        isActive={statusFilter === 'all'}
        onClick={() => onStatusFilter('all')}
      />
      <StatCard
        title="待审核"
        value={pendingCount}
        icon={Clock}
        color="amber"
        isActive={statusFilter === 'trend_pending' || statusFilter === 'final_pending'}
        onClick={() => onStatusFilter('trend_pending')}
      />
      <StatCard
        title="异常待处理"
        value={flaggedCount}
        icon={AlertTriangle}
        color="red"
        isActive={statusFilter === 'trend_flagged'}
        onClick={() => onStatusFilter('trend_flagged')}
      />
      <StatCard
        title="已锁定"
        value={lockedCount}
        icon={Lock}
        color="green"
        isActive={statusFilter === 'final_locked'}
        onClick={() => onStatusFilter('final_locked')}
      />
    </div>
  );
}

export default DailyReportsStats;
