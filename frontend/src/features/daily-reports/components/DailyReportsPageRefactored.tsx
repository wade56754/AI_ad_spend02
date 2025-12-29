/**
 * DailyReportsPage (Refactored)
 *
 * 日报管理页面 - 从 602 行重构为 ~200 行
 * 子组件已提取到独立文件
 *
 * SoT: docs/10.module-specs/B2-daily-report-review.md §4.1 页面布局
 * SoT: STATE_MACHINE.md v2.6 Section 8 (日报 8 状态机)
 * SoT: API_SOT.md v9.0 Section 5.4 (Daily Reports endpoints)
 */

'use client';

import { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, Upload, RefreshCw } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import { useQuery } from '@tanstack/react-query';
import { apiFetch, apiDownload } from '@/lib/api';

import { DailyReportsTable } from './DailyReportsTable';
import { DailyReportsStats } from './DailyReportsStats';
import { DailyReportsFilters } from './DailyReportsFilters';
import { useDailyReports, useDailyReportStats, useRefreshDailyReports } from '../hooks';
import { STATUS_CONFIG } from '../types';
import type { DailyReportStatus, DailyReportListParams } from '../types';

// ============ Types ============

interface TeamOption {
  id: string;
  name: string;
  code: string;
}

// ============ Hooks ============

const useTeamOptions = () => {
  return useQuery({
    queryKey: ['daily-reports', 'filter-options', 'teams'],
    queryFn: async () => {
      return await apiFetch<TeamOption[]>('/api/v1/daily-reports/filter-options/teams');
    },
  });
};

const useSubmitterOptions = () => {
  return useQuery({
    queryKey: ['daily-reports', 'filter-options', 'submitters'],
    queryFn: async () => {
      return await apiFetch<string[]>('/api/v1/daily-reports/filter-options/submitters');
    },
  });
};

// ============ Main Component ============

export function DailyReportsPageRefactored() {
  // ========== State ==========
  const [filters, setFilters] = useState<DailyReportListParams>({
    page: 1,
    page_size: 20,
    sort_by: 'report_date',
    sort_order: 'desc',
  });
  const [dateRange, setDateRange] = useState<{ from: Date | undefined; to: Date | undefined }>({
    from: undefined,
    to: undefined,
  });
  const [statusFilter, setStatusFilter] = useState<DailyReportStatus | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [viewMode, setViewMode] = useState<'table' | 'stats'>('table');
  const [isExporting, setIsExporting] = useState(false);

  // ========== Data Fetching ==========
  const { data: reportsData, isLoading } = useDailyReports(filters);
  const { refreshAll } = useRefreshDailyReports();
  const { data: stats } = useDailyReportStats({
    start_date: dateRange.from ? format(dateRange.from, 'yyyy-MM-dd') : undefined,
    end_date: dateRange.to ? format(dateRange.to, 'yyyy-MM-dd') : undefined,
  });
  const { data: teamOptions = [] } = useTeamOptions();
  const { data: submitterOptions = [] } = useSubmitterOptions();

  // ========== Handlers ==========
  const handleStatusFilter = useCallback((status: DailyReportStatus | 'all') => {
    setStatusFilter(status);
    setFilters((prev) => ({
      ...prev,
      status: status === 'all' ? undefined : status,
      page: 1,
    }));
  }, []);

  const handleFilterChange = useCallback((key: keyof DailyReportListParams, value: string | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
      page: 1,
    }));
  }, []);

  const handleDateRangeChange = useCallback((range: { from: Date | undefined; to: Date | undefined }) => {
    setDateRange(range);
    setFilters((prev) => ({
      ...prev,
      start_date: range.from ? format(range.from, 'yyyy-MM-dd') : undefined,
      end_date: range.to ? format(range.to, 'yyyy-MM-dd') : undefined,
      page: 1,
    }));
  }, []);

  const handleSearch = useCallback(() => {
    setFilters((prev) => ({
      ...prev,
      search: searchQuery || undefined,
      page: 1,
    }));
  }, [searchQuery]);

  const clearFilters = useCallback(() => {
    setStatusFilter('all');
    setDateRange({ from: undefined, to: undefined });
    setSearchQuery('');
    setFilters({
      page: 1,
      page_size: 20,
      sort_by: 'report_date',
      sort_order: 'desc',
    });
  }, []);

  const handleExport = useCallback(async () => {
    try {
      setIsExporting(true);
      const params = new URLSearchParams();
      if (filters.start_date) params.set('start_date', filters.start_date);
      if (filters.end_date) params.set('end_date', filters.end_date);
      if (filters.status) {
        const statusValue = Array.isArray(filters.status) ? filters.status.join(',') : filters.status;
        params.set('status', statusValue);
      }
      if (filters.team_id) params.set('team_id', filters.team_id);
      if (filters.submitter_name) params.set('submitter_name', filters.submitter_name);
      if (filters.region) params.set('region', filters.region);
      if (filters.platform) params.set('platform', filters.platform);
      params.set('format', 'xlsx');

      const filename = `daily-reports-${format(new Date(), 'yyyyMMdd-HHmmss')}.xlsx`;
      await apiDownload(`/api/v1/daily-reports/export?${params.toString()}`, { saveAs: filename });
      toast.success('导出成功', { description: `文件已保存: ${filename}` });
    } catch (error) {
      console.error('Export failed:', error);
      toast.error('导出失败', { description: error instanceof Error ? error.message : '请稍后重试' });
    } finally {
      setIsExporting(false);
    }
  }, [filters]);

  // ========== Computed ==========
  const totalReports = reportsData?.meta?.pagination?.total ?? 0;
  const pendingCount = (stats?.trend_pending ?? 0) + (stats?.final_pending ?? 0);
  const flaggedCount = stats?.trend_flagged ?? 0;
  const lockedCount = stats?.final_locked ?? 0;

  // ========== Render ==========
  return (
    <div className="min-h-screen bg-gray-50 -m-6 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">日报审核</h1>
          <p className="text-sm text-gray-500 mt-1">广告消耗日报数据及审批流程</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refreshAll()}
            disabled={isLoading}
            className="text-gray-600"
          >
            <RefreshCw className={cn('h-4 w-4 mr-2', isLoading && 'animate-spin')} />
            刷新
          </Button>
          <Button variant="outline" size="sm" className="bg-white">
            <Upload className="h-4 w-4 mr-2" />
            导入
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={handleExport}
            disabled={isExporting}
          >
            <Download className={cn('h-4 w-4 mr-2', isExporting && 'animate-pulse')} />
            {isExporting ? '导出中...' : '导出'}
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <DailyReportsStats
        totalReports={totalReports}
        pendingCount={pendingCount}
        flaggedCount={flaggedCount}
        lockedCount={lockedCount}
        statusFilter={statusFilter}
        onStatusFilter={handleStatusFilter}
      />

      {/* Filters */}
      <DailyReportsFilters
        filters={filters}
        dateRange={dateRange}
        statusFilter={statusFilter}
        searchQuery={searchQuery}
        showAdvanced={showAdvanced}
        viewMode={viewMode}
        teamOptions={teamOptions}
        submitterOptions={submitterOptions}
        stats={stats}
        onFilterChange={handleFilterChange}
        onDateRangeChange={handleDateRangeChange}
        onStatusFilter={handleStatusFilter}
        onSearchChange={setSearchQuery}
        onSearch={handleSearch}
        onToggleAdvanced={() => setShowAdvanced(!showAdvanced)}
        onClearFilters={clearFilters}
        onViewModeChange={setViewMode}
      />

      {/* Content */}
      {viewMode === 'table' ? (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <DailyReportsTable filters={filters} onFiltersChange={setFilters} />
        </div>
      ) : (
        <Card className="shadow-sm border-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">状态分布统计</CardTitle>
            <CardDescription>各状态的日报数量分布</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(STATUS_CONFIG).map(([status, config]) => (
                <div
                  key={status}
                  className={cn(
                    'p-5 rounded-xl bg-gray-50 text-center cursor-pointer transition-all',
                    'hover:bg-gray-100',
                    statusFilter === status && 'ring-2 ring-primary bg-white shadow-sm'
                  )}
                  onClick={() => handleStatusFilter(status as DailyReportStatus)}
                >
                  <p className="text-3xl font-bold text-gray-900 tabular-nums">
                    {stats?.[status as DailyReportStatus] ?? 0}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">{config.label}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default DailyReportsPageRefactored;
