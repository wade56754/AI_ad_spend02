/**
 * DailyReportsStatusTabs Component
 *
 * 状态 Tab - Segmented Control 风格
 * 从 DailyReportsPage.tsx 提取
 *
 * SoT: docs/10.module-specs/B2-daily-report-review.md
 * SoT: STATE_MACHINE.md v2.6 Section 8 (日报 8 状态机)
 */

'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import type { DailyReportStatus } from '../types';

interface StatusTabsProps {
  value: DailyReportStatus | 'all';
  onChange: (status: DailyReportStatus | 'all') => void;
  stats?: Record<DailyReportStatus, number>;
  className?: string;
}

export function DailyReportsStatusTabs({ value, onChange, stats, className }: StatusTabsProps) {
  const totalCount = stats
    ? Object.values(stats).reduce((sum, count) => sum + count, 0)
    : 0;

  const tabs: Array<{
    key: DailyReportStatus | 'all';
    label: string;
    count: number;
    highlight?: boolean;
  }> = [
    { key: 'all', label: '全部', count: totalCount },
    { key: 'trend_pending', label: '待审核', count: (stats?.trend_pending ?? 0) + (stats?.final_pending ?? 0), highlight: true },
    { key: 'trend_flagged', label: '异常', count: stats?.trend_flagged ?? 0, highlight: true },
    { key: 'final_locked', label: '已完成', count: stats?.final_locked ?? 0 },
  ];

  return (
    <div className={cn('flex items-center gap-1 p-1 bg-gray-100 rounded-lg w-fit', className)} data-testid="status-tabs">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-md transition-all',
            value === tab.key
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          )}
        >
          {tab.label}
          {tab.count > 0 && (
            <span className={cn(
              'ml-2 px-2 py-0.5 text-xs rounded-full',
              tab.highlight && tab.count > 0
                ? 'bg-red-100 text-red-700'
                : value === tab.key
                  ? 'bg-gray-100 text-gray-700'
                  : 'bg-gray-200 text-gray-600'
            )}>
              {tab.count}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

export default DailyReportsStatusTabs;
