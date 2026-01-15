/**
 * DailyReportsStatusTabs Component
 *
 * 状态 Tab - Segmented Control 风格
 * 从 DailyReportsPage.tsx 提取
 *
 * SoT: docs/10.module-specs/B2-daily-report-review.md
 * SoT: STATE_MACHINE.md v2.6 Section 8 (日报 8 状态机)
 *
 * Phase 1 模式 (默认启用):
 * - 只显示 3 个状态 Tab: 全部、待审核、已确认
 */

'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import type { DailyReportStatus, Phase1Status } from '../types';
import { PHASE1_STATUS_MAP } from '../types';

interface StatusTabsProps {
  value: DailyReportStatus | Phase1Status | 'all';
  onChange: (status: DailyReportStatus | Phase1Status | 'all') => void;
  stats?: Record<DailyReportStatus, number>;
  className?: string;
  /** Phase 1 模式 - 简化为 3 个状态 Tab (默认 true) */
  phase1?: boolean;
}

/**
 * 聚合 8 状态统计到 Phase 1 的 3 状态
 */
function aggregateToPhase1Stats(
  stats?: Record<DailyReportStatus, number>
): Record<Phase1Status, number> {
  if (!stats) return { raw_submitted: 0, trend_ok: 0, final_confirmed: 0 };

  const phase1Stats: Record<Phase1Status, number> = {
    raw_submitted: 0,
    trend_ok: 0,
    final_confirmed: 0,
  };

  // 遍历所有状态并聚合到 Phase 1 状态
  (Object.entries(stats) as [DailyReportStatus, number][]).forEach(([status, count]) => {
    const phase1Status = PHASE1_STATUS_MAP[status];
    phase1Stats[phase1Status] += count;
  });

  return phase1Stats;
}

export function DailyReportsStatusTabs({
  value,
  onChange,
  stats,
  className,
  phase1 = true,
}: StatusTabsProps) {
  const totalCount = stats ? Object.values(stats).reduce((sum, count) => sum + count, 0) : 0;

  // Phase 1 模式: 简化的 3 状态 Tab
  if (phase1) {
    const phase1Stats = aggregateToPhase1Stats(stats);
    const pendingCount = phase1Stats.raw_submitted + phase1Stats.trend_ok;

    const tabs: Array<{
      key: Phase1Status | 'all';
      label: string;
      count: number;
      highlight?: boolean;
    }> = [
      { key: 'all', label: '全部', count: totalCount },
      { key: 'raw_submitted', label: '待审核', count: pendingCount, highlight: pendingCount > 0 },
      { key: 'final_confirmed', label: '已确认', count: phase1Stats.final_confirmed },
    ];

    return (
      <div
        className={cn('flex items-center gap-1 p-1 bg-gray-100 rounded-lg w-fit', className)}
        data-testid="status-tabs"
      >
        {tabs.map((tab) => (
          <Button
            key={tab.key}
            onClick={() => onChange(tab.key)}
            variant="ghost"
            className={cn(
              'px-4 py-2 text-sm font-medium rounded-md transition-all',
              value === tab.key
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            {tab.label}
            {tab.count > 0 && (
              <span
                className={cn(
                  'ml-2 px-2 py-0.5 text-xs rounded-full',
                  tab.highlight && tab.count > 0
                    ? 'bg-red-100 text-red-700'
                    : value === tab.key
                      ? 'bg-gray-100 text-gray-700'
                      : 'bg-gray-200 text-gray-600'
                )}
              >
                {tab.count}
              </span>
            )}
          </Button>
        ))}
      </div>
    );
  }

  // 完整 8 状态模式 (Phase 2+)
  const tabs: Array<{
    key: DailyReportStatus | 'all';
    label: string;
    count: number;
    highlight?: boolean;
  }> = [
    { key: 'all', label: '全部', count: totalCount },
    {
      key: 'trend_pending',
      label: '待审核',
      count: (stats?.trend_pending ?? 0) + (stats?.final_pending ?? 0),
      highlight: true,
    },
    { key: 'trend_flagged', label: '异常', count: stats?.trend_flagged ?? 0, highlight: true },
    { key: 'final_locked', label: '已完成', count: stats?.final_locked ?? 0 },
  ];

  return (
    <div
      className={cn('flex items-center gap-1 p-1 bg-gray-100 rounded-lg w-fit', className)}
      data-testid="status-tabs"
    >
      {tabs.map((tab) => (
        <Button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          variant="ghost"
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-md transition-all',
            value === tab.key
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          )}
        >
          {tab.label}
          {tab.count > 0 && (
            <span
              className={cn(
                'ml-2 px-2 py-0.5 text-xs rounded-full',
                tab.highlight && tab.count > 0
                  ? 'bg-red-100 text-red-700'
                  : value === tab.key
                    ? 'bg-gray-100 text-gray-700'
                    : 'bg-gray-200 text-gray-600'
              )}
            >
              {tab.count}
            </span>
          )}
        </Button>
      ))}
    </div>
  );
}

export default DailyReportsStatusTabs;
