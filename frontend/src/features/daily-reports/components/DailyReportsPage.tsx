/**
 * DailyReportsPage Component
 *
 * SoT: docs/10.module-specs/B2-daily-report-review.md §4.1 页面布局
 * SoT: STATE_MACHINE.md v2.6 Section 8 (日报 8 状态机)
 * SoT: API_SOT.md v9.0 Section 5.4 (Daily Reports endpoints)
 *
 * 一句话定义: 让主管/财务了解"投手今天干得怎样？有无异常？"
 *
 * 日报 8 状态机:
 *   raw_submitted → trend_pending → trend_ok/trend_flagged
 *   → trend_resolved → final_pending → final_confirmed → final_locked
 *
 * 视觉规范 (v3.0):
 * - 打破三明治布局，统一筛选容器
 * - KPI卡片去边框加投影，图标带色块背景
 * - 状态Tab替代状态说明
 * - 页面背景灰色，内容块白色
 *
 * @module features/daily-reports/components
 */

'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import {
  CalendarIcon,
  Download,
  Upload,
  RefreshCw,
  ChevronDown,
  BarChart3,
  List,
  FileText,
  AlertTriangle,
  Clock,
  Lock,
  Search,
  X,
  Filter,
} from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { DailyReportsTable } from './DailyReportsTable';
import { DailyReportsStatusTabs } from './DailyReportsStatusTabs';
import { useDailyReports, useDailyReportStats, useRefreshDailyReports } from '../hooks';
import type { DailyReportStatus, DailyReportListParams, Phase1Status } from '../types';
import { STATUS_CONFIG, PLATFORM_OPTIONS, REGION_OPTIONS, PHASE1_STATUS_CONFIG } from '../types';
import { useQuery } from '@tanstack/react-query';
import { apiFetch, apiDownload } from '@/lib/api';
import { toast } from 'sonner';

// ============================================================================
// 类型定义
// ============================================================================

interface TeamOption {
  id: string;
  name: string;
  code: string;
}

// ============================================================================
// Hooks - 筛选选项
// ============================================================================

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

// ============================================================================
// 子组件 - KPI 卡片 (v3.0 去边框+投影+色块图标)
// ============================================================================

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  color: 'slate' | 'blue' | 'amber' | 'red' | 'green';
  isActive?: boolean;
  onClick?: () => void;
}

const colorConfig = {
  slate: { iconBg: 'bg-slate-100', iconColor: 'text-slate-600' },
  blue:  { iconBg: 'bg-blue-50',   iconColor: 'text-blue-600' },
  amber: { iconBg: 'bg-amber-50',  iconColor: 'text-amber-600' },
  red:   { iconBg: 'bg-red-50',    iconColor: 'text-red-600' },
  green: { iconBg: 'bg-green-50',  iconColor: 'text-green-600' },
};

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

// ============================================================================
// 主组件
// ============================================================================

export function DailyReportsPage() {
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
  const [statusFilter, setStatusFilter] = useState<Phase1Status | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [viewMode, setViewMode] = useState<'table' | 'stats'>('table');

  // ========== Data Fetching ==========
  // SoT: B2-daily-report-review.md §5 API 接口
  const { data: reportsData, isLoading } = useDailyReports(filters);
  const { refreshAll } = useRefreshDailyReports();
  const { data: stats } = useDailyReportStats({
    start_date: dateRange.from ? format(dateRange.from, 'yyyy-MM-dd') : undefined,
    end_date: dateRange.to ? format(dateRange.to, 'yyyy-MM-dd') : undefined,
  });
  const { data: teamOptions = [] } = useTeamOptions();
  const { data: submitterOptions = [] } = useSubmitterOptions();

  // ========== Handlers ==========
  // Phase 1: 将 3 个展示状态映射到 API 筛选参数
  const handleStatusFilter = (status: Phase1Status | 'all') => {
    setStatusFilter(status);
    // Phase 1 状态到 API 状态的映射
    let apiStatus: DailyReportStatus | DailyReportStatus[] | undefined;
    if (status === 'all') {
      apiStatus = undefined;
    } else if (status === 'raw_submitted') {
      // 待审核: 包含 raw_submitted, trend_pending, trend_flagged
      apiStatus = ['raw_submitted', 'trend_pending', 'trend_flagged'];
    } else if (status === 'trend_ok') {
      // 已审核: 包含 trend_ok, trend_resolved, final_pending
      apiStatus = ['trend_ok', 'trend_resolved', 'final_pending'];
    } else if (status === 'final_confirmed') {
      // 已确认: 包含 final_confirmed, final_locked
      apiStatus = ['final_confirmed', 'final_locked'];
    }
    setFilters((prev) => ({
      ...prev,
      status: apiStatus,
      page: 1,
    }));
  };

  const handleFilterChange = (key: keyof DailyReportListParams, value: string | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value === 'all' ? undefined : value,
      page: 1,
    }));
  };

  const handleDateRangeChange = (range: { from: Date | undefined; to: Date | undefined }) => {
    setDateRange(range);
    setFilters((prev) => ({
      ...prev,
      start_date: range.from ? format(range.from, 'yyyy-MM-dd') : undefined,
      end_date: range.to ? format(range.to, 'yyyy-MM-dd') : undefined,
      page: 1,
    }));
  };

  const handleSearch = () => {
    setFilters((prev) => ({
      ...prev,
      search: searchQuery || undefined,
      page: 1,
    }));
  };

  const clearFilters = () => {
    setStatusFilter('all');
    setDateRange({ from: undefined, to: undefined });
    setSearchQuery('');
    setFilters({
      page: 1,
      page_size: 20,
      sort_by: 'report_date',
      sort_order: 'desc',
    });
  };

  // 导出功能
  const [isExporting, setIsExporting] = useState(false);
  const handleExport = async () => {
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
  };

  // ========== Computed (Phase 1: 聚合到 3 状态) ==========
  const totalReports = reportsData?.meta?.pagination?.total ?? 0;

  // Phase 1 统计: 将 8 状态聚合到 3 个展示状态
  const rawSubmittedCount = (stats?.raw_submitted ?? 0) + (stats?.trend_pending ?? 0) + (stats?.trend_flagged ?? 0);
  const trendOkCount = (stats?.trend_ok ?? 0) + (stats?.trend_resolved ?? 0) + (stats?.final_pending ?? 0);
  const finalConfirmedCount = (stats?.final_confirmed ?? 0) + (stats?.final_locked ?? 0);

  const hasActiveFilters = filters.team_id || filters.submitter_name ||
    filters.region || filters.platform || filters.search ||
    dateRange.from || statusFilter !== 'all';

  // ========== Render ==========
  return (
    <div className="min-h-screen bg-gray-50 -m-6 p-6 space-y-6" data-testid="daily-report-page">
      {/* ====== Header ====== */}
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

      {/* ====== KPI Cards (Phase 1: 3 状态卡片) ====== */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="总日报"
          value={totalReports}
          icon={FileText}
          color="slate"
          isActive={statusFilter === 'all'}
          onClick={() => handleStatusFilter('all')}
        />
        <StatCard
          title="已提交"
          value={rawSubmittedCount}
          icon={Clock}
          color="amber"
          isActive={statusFilter === 'raw_submitted'}
          onClick={() => handleStatusFilter('raw_submitted')}
        />
        <StatCard
          title="已审核"
          value={trendOkCount}
          icon={AlertTriangle}
          color="blue"
          isActive={statusFilter === 'trend_ok'}
          onClick={() => handleStatusFilter('trend_ok')}
        />
        <StatCard
          title="已确认"
          value={finalConfirmedCount}
          icon={Lock}
          color="green"
          isActive={statusFilter === 'final_confirmed'}
          onClick={() => handleStatusFilter('final_confirmed')}
        />
      </div>

      {/* ====== Unified Filter Panel (白色容器，统一筛选) ====== */}
      <div className="bg-white rounded-xl shadow-sm p-5 space-y-4">
        {/* Row 1: 搜索 + 常用筛选 */}
        <div className="flex items-center gap-4 flex-wrap">
          {/* 搜索框 (加宽 + 提示文案) */}
          <div className="relative flex-1 max-w-md min-w-[240px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="搜索项目名称 / 账户ID / 投手姓名..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="pl-10 h-10 bg-gray-50 border-gray-200 focus:bg-white"
            />
          </div>

          {/* 日期范围 */}
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={cn(
                  'h-10 w-[200px] justify-start text-left font-normal bg-gray-50 border-gray-200',
                  !dateRange.from && 'text-gray-500'
                )}
                data-testid="date-filter"
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {dateRange.from ? (
                  dateRange.to ? (
                    <>{format(dateRange.from, 'MM/dd')} - {format(dateRange.to, 'MM/dd')}</>
                  ) : (
                    format(dateRange.from, 'yyyy-MM-dd')
                  )
                ) : (
                  '选择日期范围'
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="range"
                // @ts-expect-error - shadcn/ui Calendar mode="range" 类型定义问题
                selected={dateRange.from ? { from: dateRange.from, to: dateRange.to } : undefined}
                onSelect={(range: unknown) => {
                  const r = range as { from?: Date; to?: Date } | undefined;
                  handleDateRangeChange({ from: r?.from, to: r?.to });
                }}
                numberOfMonths={2}
              />
            </PopoverContent>
          </Popover>

          {/* 团队 */}
          <Select
            value={filters.team_id || 'all'}
            onValueChange={(v) => handleFilterChange('team_id', v)}
          >
            <SelectTrigger className="h-10 w-[140px] bg-gray-50 border-gray-200" data-testid="project-filter">
              <SelectValue placeholder="团队" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部团队</SelectItem>
              {teamOptions.map((t) => (
                <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* 投手 */}
          <Select
            value={filters.submitter_name || 'all'}
            onValueChange={(v) => handleFilterChange('submitter_name', v)}
          >
            <SelectTrigger className="h-10 w-[140px] bg-gray-50 border-gray-200">
              <SelectValue placeholder="投手" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部投手</SelectItem>
              {submitterOptions.map((name) => (
                <SelectItem key={name} value={name}>{name}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* 高级筛选 */}
          <Button
            variant="ghost"
            className="h-10 text-gray-600"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            <Filter className="h-4 w-4 mr-2" />
            高级筛选
            <ChevronDown className={cn('ml-1 h-4 w-4 transition-transform', showAdvanced && 'rotate-180')} />
          </Button>

          {/* 清除筛选 */}
          {hasActiveFilters && (
            <Button variant="ghost" className="h-10 text-gray-500" onClick={clearFilters}>
              <X className="h-4 w-4 mr-1" />
              清除
            </Button>
          )}

          {/* 视图切换 */}
          <div className="ml-auto flex items-center gap-1 bg-gray-100 rounded-lg p-1">
            <Button
              variant={viewMode === 'table' ? 'secondary' : 'ghost'}
              size="sm"
              className="h-8 px-3"
              onClick={() => setViewMode('table')}
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'stats' ? 'secondary' : 'ghost'}
              size="sm"
              className="h-8 px-3"
              onClick={() => setViewMode('stats')}
            >
              <BarChart3 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Row 2: 高级筛选（默认折叠） */}
        {showAdvanced && (
          <div className="flex items-center gap-4 pt-4 border-t border-gray-100">
            {/* 地区 */}
            <Select
              value={filters.region || 'all'}
              onValueChange={(v) => handleFilterChange('region', v)}
            >
              <SelectTrigger className="h-10 w-[140px] bg-gray-50 border-gray-200">
                <SelectValue placeholder="地区" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部地区</SelectItem>
                {REGION_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* 平台 */}
            <Select
              value={filters.platform || 'all'}
              onValueChange={(v) => handleFilterChange('platform', v)}
            >
              <SelectTrigger className="h-10 w-[140px] bg-gray-50 border-gray-200">
                <SelectValue placeholder="平台" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部平台</SelectItem>
                {PLATFORM_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Row 3: 状态 Tab (Phase 1: 3 状态) */}
        <div className="pt-4 border-t border-gray-100" data-testid="status-filter">
          <DailyReportsStatusTabs
            value={statusFilter}
            onChange={handleStatusFilter}
            stats={stats}
            phase1={true}
          />
        </div>
      </div>

      {/* ====== Content ====== */}
      {viewMode === 'table' ? (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden" data-testid="daily-report-table">
          <DailyReportsTable filters={filters} onFiltersChange={setFilters} />
        </div>
      ) : (
        <Card className="shadow-sm border-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">状态分布统计</CardTitle>
            <CardDescription>各状态的日报数量分布 (Phase 1)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* Phase 1: 只显示 3 个状态 */}
              {(Object.entries(PHASE1_STATUS_CONFIG) as [Phase1Status, { label: string; variant: string }][]).map(([status, config]) => {
                // 计算每个 Phase 1 状态的聚合数量
                const count = status === 'raw_submitted' ? rawSubmittedCount
                  : status === 'trend_ok' ? trendOkCount
                  : finalConfirmedCount;

                return (
                  <div
                    key={status}
                    className={cn(
                      'p-5 rounded-xl bg-gray-50 text-center cursor-pointer transition-all',
                      'hover:bg-gray-100',
                      statusFilter === status && 'ring-2 ring-primary bg-white shadow-sm'
                    )}
                    onClick={() => handleStatusFilter(status)}
                  >
                    <p className="text-3xl font-bold text-gray-900 tabular-nums">
                      {count}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">{config.label}</p>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
