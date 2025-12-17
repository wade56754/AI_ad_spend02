/**
 * Daily Reports Page Component
 *
 * Main page for daily report management with filters, stats, and 8-state workflow
 * SoT: STATE_MACHINE.md v2.6 Section 8
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import {
  CalendarIcon,
  Download,
  Upload,
  RefreshCw,
  Filter,
  BarChart3,
  FileText,
  AlertTriangle,
  Clock,
  Lock,
} from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { DailyReportsTable } from './DailyReportsTable';
import { StatusLegend } from './StatusBadge';
import { useDailyReports, useDailyReportStats } from '../hooks';
import type { DailyReportStatus, DailyReportListParams } from '../types';
import { STATUS_CONFIG } from '../types';

/**
 * Stat card for displaying report statistics
 */
interface StatCardProps {
  title: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  variant?: 'default' | 'success' | 'warning' | 'error';
  onClick?: () => void;
}

function StatCard({ title, value, icon: Icon, variant = 'default', onClick }: StatCardProps) {
  const variantStyles = {
    default: 'bg-gray-50 text-gray-700',
    success: 'bg-green-50 text-green-700',
    warning: 'bg-amber-50 text-amber-700',
    error: 'bg-red-50 text-red-700',
  };

  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:shadow-md',
        onClick && 'hover:ring-2 hover:ring-primary/20'
      )}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold mt-1">{value}</p>
          </div>
          <div className={cn('p-3 rounded-full', variantStyles[variant])}>
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function DailyReportsPage() {
  // Filter state
  const [filters, setFilters] = useState<DailyReportListParams>({
    page: 1,
    page_size: 20,
    sort_by: 'report_date',
    sort_order: 'desc',
  });
  const [dateRange, setDateRange] = useState<{
    from: Date | undefined;
    to: Date | undefined;
  }>({
    from: undefined,
    to: undefined,
  });
  const [statusFilter, setStatusFilter] = useState<DailyReportStatus | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Data fetching
  const { data: reportsData, refetch } = useDailyReports(filters);
  const { data: stats } = useDailyReportStats({
    start_date: dateRange.from ? format(dateRange.from, 'yyyy-MM-dd') : undefined,
    end_date: dateRange.to ? format(dateRange.to, 'yyyy-MM-dd') : undefined,
  });

  // Handle filter changes
  const handleStatusFilter = (status: DailyReportStatus | 'all') => {
    setStatusFilter(status);
    setFilters((prev) => ({
      ...prev,
      status: status === 'all' ? undefined : status,
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

  // Calculate stats from data
  const totalReports = reportsData?.meta?.pagination?.total ?? 0;
  const pendingCount = (stats?.trend_pending ?? 0) + (stats?.final_pending ?? 0);
  const flaggedCount = stats?.trend_flagged ?? 0;
  const lockedCount = stats?.final_locked ?? 0;

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">日报管理</h1>
          <p className="text-muted-foreground">管理广告消耗日报数据及审批流程</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
          <Button variant="outline" size="sm">
            <Upload className="h-4 w-4 mr-2" />
            批量导入
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="总日报数"
          value={totalReports}
          icon={FileText}
          onClick={() => handleStatusFilter('all')}
        />
        <StatCard
          title="待审核"
          value={pendingCount}
          icon={Clock}
          variant="warning"
          onClick={() => handleStatusFilter('trend_pending')}
        />
        <StatCard
          title="异常待处理"
          value={flaggedCount}
          icon={AlertTriangle}
          variant="error"
          onClick={() => handleStatusFilter('trend_flagged')}
        />
        <StatCard
          title="已锁定"
          value={lockedCount}
          icon={Lock}
          variant="success"
          onClick={() => handleStatusFilter('final_locked')}
        />
      </div>

      {/* Filters */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-base">筛选条件</CardTitle>
            </div>
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              清除筛选
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-4">
            {/* Date Range Picker */}
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    'w-[260px] justify-start text-left font-normal',
                    !dateRange.from && 'text-muted-foreground'
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {dateRange.from ? (
                    dateRange.to ? (
                      <>
                        {format(dateRange.from, 'MM/dd')} -{' '}
                        {format(dateRange.to, 'MM/dd')}
                      </>
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
                  selected={dateRange.from && dateRange.to ? [dateRange.from, dateRange.to] : dateRange.from ? [dateRange.from] : undefined}
                  onSelect={(dates) => {
                    if (!dates) {
                      handleDateRangeChange({ from: undefined, to: undefined });
                    } else if (Array.isArray(dates)) {
                      handleDateRangeChange({
                        from: dates[0],
                        to: dates.length > 1 ? dates[1] : undefined
                      });
                    } else {
                      handleDateRangeChange({ from: dates, to: undefined });
                    }
                  }}
                  numberOfMonths={2}
                />
              </PopoverContent>
            </Popover>

            {/* Status Filter */}
            <Select
              value={statusFilter}
              onValueChange={(value) => handleStatusFilter(value as DailyReportStatus | 'all')}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(STATUS_CONFIG).map(([status, config]) => (
                  <SelectItem key={status} value={status}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Search */}
            <div className="flex items-center gap-2">
              <Input
                placeholder="搜索项目/账户..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="w-[200px]"
              />
              <Button variant="secondary" size="sm" onClick={handleSearch}>
                搜索
              </Button>
            </div>
          </div>

          {/* Status Legend */}
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs text-muted-foreground mb-2">状态说明</p>
            <StatusLegend />
          </div>
        </CardContent>
      </Card>

      {/* Tabs for different views */}
      <Tabs defaultValue="table" className="space-y-4">
        <TabsList>
          <TabsTrigger value="table" className="gap-2">
            <FileText className="h-4 w-4" />
            列表视图
          </TabsTrigger>
          <TabsTrigger value="stats" className="gap-2">
            <BarChart3 className="h-4 w-4" />
            统计视图
          </TabsTrigger>
        </TabsList>

        <TabsContent value="table">
          <Card>
            <CardContent className="p-0">
              <DailyReportsTable />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stats">
          <Card>
            <CardHeader>
              <CardTitle>状态分布统计</CardTitle>
              <CardDescription>各状态的日报数量分布</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(STATUS_CONFIG).map(([status, config]) => (
                  <div
                    key={status}
                    className="p-4 rounded-lg border text-center cursor-pointer hover:bg-gray-50"
                    onClick={() => handleStatusFilter(status as DailyReportStatus)}
                  >
                    <p className="text-3xl font-bold">
                      {stats?.[status as DailyReportStatus] ?? 0}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">{config.label}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
