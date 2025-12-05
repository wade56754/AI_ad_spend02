/**
 * DailyReportsPageShell - 日报管理页面主容器
 *
 * 布局结构：
 * - Header: 标题 + 状态筛选 + 日期范围 + 新建按钮
 * - KPI 区: 各状态日报数量统计
 * - 主内容: 日报列表表格
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3, STATE_MACHINE.md v2.6
 */

'use client';

import React from 'react';
import { FileText, Plus, Search, Calendar } from 'lucide-react';
import { PageShell } from '@/modules/shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DailyReportsKpiRow } from './DailyReportsKpiRow';
import { DailyReportsDataTable } from './DailyReportsDataTable';
import { useDailyReports, useDailyReportStats } from '../hooks';
import type { DailyReportStatus, DailyReportFilters } from '../types';

export function DailyReportsPageShell() {
  const [filters, setFilters] = React.useState<DailyReportFilters>({});

  const { data: reportsData, isLoading: reportsLoading } = useDailyReports(filters);
  const { data: statsData, isLoading: statsLoading } = useDailyReportStats();

  const reports = reportsData?.data ?? [];
  const loading = reportsLoading || statsLoading;

  const summary = {
    total: reports.length,
    raw_submitted: statsData?.raw_submitted ?? 0,
    trend_pending: statsData?.trend_pending ?? 0,
    trend_flagged: statsData?.trend_flagged ?? 0,
    final_pending: statsData?.final_pending ?? 0,
    final_confirmed: statsData?.final_confirmed ?? 0,
    final_locked: statsData?.final_locked ?? 0,
  };

  const handleStatusChange = (value: string) => {
    if (value === 'all') {
      const { status, ...rest } = filters;
      setFilters(rest);
    } else {
      setFilters({ ...filters, status: value as DailyReportStatus });
    }
  };

  return (
    <PageShell
      title="日报管理"
      description="管理投放日报，支持 8 状态流转（raw_submitted → final_locked）"
      icon={FileText}
      filters={
        <>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <Input
              placeholder="搜索日报..."
              className="pl-9 w-[200px] bg-card-bg border-border-default text-text-body placeholder:text-text-muted"
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          </div>
          <Select onValueChange={handleStatusChange} defaultValue="all">
            <SelectTrigger className="w-[140px] bg-card-bg border-border-default text-text-body">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent className="bg-card-bg border-border-default">
              <SelectItem value="all" className="text-text-body hover:bg-elevated">全部状态</SelectItem>
              <SelectItem value="raw_submitted" className="text-text-body hover:bg-elevated">原始提交</SelectItem>
              <SelectItem value="trend_pending" className="text-text-body hover:bg-elevated">趋势待审</SelectItem>
              <SelectItem value="trend_flagged" className="text-text-body hover:bg-elevated">趋势异常</SelectItem>
              <SelectItem value="final_pending" className="text-text-body hover:bg-elevated">终审待审</SelectItem>
              <SelectItem value="final_confirmed" className="text-text-body hover:bg-elevated">终审确认</SelectItem>
              <SelectItem value="final_locked" className="text-text-body hover:bg-elevated">已锁定</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            className="gap-2 bg-card-bg border-border-default text-text-body hover:bg-elevated"
          >
            <Calendar className="w-4 h-4" />
            日期范围
          </Button>
        </>
      }
      actions={
        <Button
          size="sm"
          className="gap-2 bg-accent hover:bg-accent-hover shadow-lg shadow-accent/20"
        >
          <Plus className="w-4 h-4" />
          提交日报
        </Button>
      }
      kpiSection={<DailyReportsKpiRow summary={summary} loading={loading} />}
    >
      <DailyReportsDataTable
        reports={reports}
        loading={loading}
        onRowClick={(report) => console.log('View report:', report)}
      />
    </PageShell>
  );
}

export default DailyReportsPageShell;
