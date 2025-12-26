/**
 * DailyReportsFilters Component
 *
 * 统一筛选面板 - 从 DailyReportsPage.tsx 提取
 *
 * SoT: docs/10.module-specs/B2-daily-report-review.md
 */

'use client';

import React from 'react';
import { format } from 'date-fns';
import {
  Search,
  CalendarIcon,
  ChevronDown,
  X,
  Filter,
  BarChart3,
  List,
} from 'lucide-react';
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
import { cn } from '@/lib/utils';
import { DailyReportsStatusTabs } from './DailyReportsStatusTabs';
import { PLATFORM_OPTIONS, REGION_OPTIONS } from '../types';
import type { DailyReportStatus, DailyReportListParams } from '../types';

interface TeamOption {
  id: string;
  name: string;
  code: string;
}

interface DailyReportsFiltersProps {
  filters: DailyReportListParams;
  dateRange: { from: Date | undefined; to: Date | undefined };
  statusFilter: DailyReportStatus | 'all';
  searchQuery: string;
  showAdvanced: boolean;
  viewMode: 'table' | 'stats';
  teamOptions: TeamOption[];
  submitterOptions: string[];
  stats?: Record<DailyReportStatus, number>;
  onFilterChange: (key: keyof DailyReportListParams, value: string | undefined) => void;
  onDateRangeChange: (range: { from: Date | undefined; to: Date | undefined }) => void;
  onStatusFilter: (status: DailyReportStatus | 'all') => void;
  onSearchChange: (query: string) => void;
  onSearch: () => void;
  onToggleAdvanced: () => void;
  onClearFilters: () => void;
  onViewModeChange: (mode: 'table' | 'stats') => void;
  className?: string;
}

export function DailyReportsFilters({
  filters,
  dateRange,
  statusFilter,
  searchQuery,
  showAdvanced,
  viewMode,
  teamOptions,
  submitterOptions,
  stats,
  onFilterChange,
  onDateRangeChange,
  onStatusFilter,
  onSearchChange,
  onSearch,
  onToggleAdvanced,
  onClearFilters,
  onViewModeChange,
  className,
}: DailyReportsFiltersProps) {
  const hasActiveFilters = filters.team_id || filters.submitter_name ||
    filters.region || filters.platform || filters.search ||
    dateRange.from || statusFilter !== 'all';

  return (
    <div className={cn('bg-white rounded-xl shadow-sm p-5 space-y-4', className)} data-testid="daily-reports-filters">
      {/* Row 1: 搜索 + 常用筛选 */}
      <div className="flex items-center gap-4 flex-wrap">
        {/* 搜索框 */}
        <div className="relative flex-1 max-w-md min-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="搜索项目名称 / 账户ID / 投手姓名..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onSearch()}
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
                onDateRangeChange({ from: r?.from, to: r?.to });
              }}
              numberOfMonths={2}
            />
          </PopoverContent>
        </Popover>

        {/* 团队 */}
        <Select
          value={filters.team_id || 'all'}
          onValueChange={(v) => onFilterChange('team_id', v === 'all' ? undefined : v)}
        >
          <SelectTrigger className="h-10 w-[140px] bg-gray-50 border-gray-200">
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
          onValueChange={(v) => onFilterChange('submitter_name', v === 'all' ? undefined : v)}
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
          onClick={onToggleAdvanced}
        >
          <Filter className="h-4 w-4 mr-2" />
          高级筛选
          <ChevronDown className={cn('ml-1 h-4 w-4 transition-transform', showAdvanced && 'rotate-180')} />
        </Button>

        {/* 清除筛选 */}
        {hasActiveFilters && (
          <Button variant="ghost" className="h-10 text-gray-500" onClick={onClearFilters}>
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
            onClick={() => onViewModeChange('table')}
          >
            <List className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'stats' ? 'secondary' : 'ghost'}
            size="sm"
            className="h-8 px-3"
            onClick={() => onViewModeChange('stats')}
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
            onValueChange={(v) => onFilterChange('region', v === 'all' ? undefined : v)}
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
            onValueChange={(v) => onFilterChange('platform', v === 'all' ? undefined : v)}
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

      {/* Row 3: 状态 Tab */}
      <div className="pt-4 border-t border-gray-100">
        <DailyReportsStatusTabs
          value={statusFilter}
          onChange={onStatusFilter}
          stats={stats}
        />
      </div>
    </div>
  );
}

export default DailyReportsFilters;
