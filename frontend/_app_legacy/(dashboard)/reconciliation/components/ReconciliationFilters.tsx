'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import {
  Search,
  Filter,
  RotateCcw,
  Download,
  Plus,
  Calendar,
  DollarSign,
  BarChart3,
  ChevronDown,
  X,
  User,
  FileText,
  Settings,
  Clock,
  Activity
} from 'lucide-react';
import { ReconciliationFilters as IReconciliationFilters, ReconciliationStatus, PlatformSpendSource } from '../types';
import { format, subDays, startOfMonth, endOfMonth } from 'date-fns';

interface ReconciliationFiltersProps {
  filters: IReconciliationFilters;
  onFiltersChange: (filters: IReconciliationFilters) => void;
  totalCount: number;
  onReset: () => void;
  onExport: () => void;
  onNewBatch: () => void;
  loading?: boolean;
  userOptions?: Array<{ value: string; label: string }>;
}

/**
 * 对账筛选组件
 *
 * 提供搜索、状态、平台来源等多维度筛选功能
 */
export function ReconciliationFilters({
  filters,
  onFiltersChange,
  totalCount,
  onReset,
  onExport,
  onNewBatch,
  loading = false,
  userOptions = []
}: ReconciliationFiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [tempDateRange, setTempDateRange] = useState({
    start: filters.date_range.start || format(startOfMonth(subDays(new Date(), 1)), 'yyyy-MM-dd'),
    end: filters.date_range.end || format(endOfMonth(subDays(new Date(), 1)), 'yyyy-MM-dd')
  });

  // 处理搜索输入
  const handleSearchChange = (value: string) => {
    onFiltersChange({
      ...filters,
      search_term: value
    });
  };

  // 处理状态筛选
  const handleStatusChange = (value: string) => {
    onFiltersChange({
      ...filters,
      status: value as ReconciliationStatus | 'all'
    });
  };

  // 处理平台数据源筛选
  const handlePlatformSourceChange = (value: string) => {
    onFiltersChange({
      ...filters,
      platform_spend_source: value as PlatformSpendSource | 'all'
    });
  };

  // 处理创建人筛选
  const handleCreatedByChange = (value: string) => {
    onFiltersChange({
      ...filters,
      created_by: value === 'all' ? 'all' : parseInt(value)
    });
  };

  // 处理日期范围变化
  const handleDateRangeChange = () => {
    onFiltersChange({
      ...filters,
      date_range: {
        start: tempDateRange.start,
        end: tempDateRange.end
      }
    });
    setShowAdvanced(false);
  };

  // 处理差异金额范围变化
  const handleDifferenceRangeChange = (field: 'min' | 'max', value: string) => {
    const numValue = value ? parseFloat(value) : undefined;
    onFiltersChange({
      ...filters,
      difference_range: {
        ...filters.difference_range,
        [field]: numValue
      }
    });
  };

  // 处理差异数量范围变化
  const handleDiscrepancyRangeChange = (field: 'min' | 'max', value: string) => {
    const numValue = value ? parseInt(value) : undefined;
    onFiltersChange({
      ...filters,
      discrepancy_range: {
        ...filters.discrepancy_range,
        [field]: numValue
      }
    });
  };

  // 处理排序变化
  const handleSortChange = (value: string) => {
    const [sortBy, sortOrder] = value.split('-');
    onFiltersChange({
      ...filters,
      sort_by: sortBy as any,
      sort_order: sortOrder as 'asc' | 'desc'
    });
  };

  // 清除标签
  const clearTag = (key: keyof IReconciliationFilters) => {
    onFiltersChange({
      ...filters,
      [key]: key === 'tags' ? [] : 'all'
    });
  };

  // 获取激活的筛选条件数量
  const getActiveFiltersCount = () => {
    let count = 0;
    if (filters.search_term) count++;
    if (filters.status !== 'all') count++;
    if (filters.platform_spend_source !== 'all') count++;
    if (filters.created_by !== 'all') count++;
    if (filters.date_range.start || filters.date_range.end) count++;
    if (filters.difference_range.min || filters.difference_range.max) count++;
    if (filters.discrepancy_range.min || filters.discrepancy_range.max) count++;
    if (filters.has_discrepancies !== null) count++;
    if (filters.is_auto_matching !== null) count++;
    if (filters.tags.length > 0) count++;
    return count;
  };

  const activeFiltersCount = getActiveFiltersCount();

  return (
    <div className="bg-card rounded-lg border p-4 space-y-4">
      {/* 基础筛选区域 */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center">
        {/* 搜索框 */}
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜索批次名称或创建人..."
              value={filters.search_term}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="pl-10 pr-4"
            />
          </div>
        </div>

        {/* 主要筛选条件 */}
        <div className="flex flex-wrap gap-2">
          <Select value={filters.status} onValueChange={handleStatusChange}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              <SelectItem value="pending">待处理</SelectItem>
              <SelectItem value="in_progress">对账中</SelectItem>
              <SelectItem value="completed">已完成</SelectItem>
              <SelectItem value="failed">失败</SelectItem>
              <SelectItem value="cancelled">已取消</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filters.platform_spend_source} onValueChange={handlePlatformSourceChange}>
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="数据源" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部数据源</SelectItem>
              <SelectItem value="manual">手动录入</SelectItem>
              <SelectItem value="api">API获取</SelectItem>
              <SelectItem value="file">文件上传</SelectItem>
            </SelectContent>
          </Select>

          {userOptions.length > 0 && (
            <Select value={filters.created_by.toString()} onValueChange={handleCreatedByChange}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="创建人" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部创建人</SelectItem>
                {userOptions.map(option => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-2">
          <DropdownMenu open={showAdvanced} onOpenChange={setShowAdvanced}>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2">
                <Filter className="h-4 w-4" />
                高级筛选
                {activeFiltersCount > 0 && (
                  <Badge variant="secondary" className="h-5 px-1 text-xs">
                    {activeFiltersCount}
                  </Badge>
                )}
                <ChevronDown className="h-3 w-3" />
              </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent className="w-96" align="end">
              <DropdownMenuLabel>高级筛选条件</DropdownMenuLabel>
              <DropdownMenuSeparator />

              {/* 日期范围 */}
              <div className="p-3 space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  对账周期范围
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="date"
                    value={tempDateRange.start}
                    onChange={(e) => setTempDateRange(prev => ({ ...prev, start: e.target.value }))}
                    placeholder="开始日期"
                  />
                  <Input
                    type="date"
                    value={tempDateRange.end}
                    onChange={(e) => setTempDateRange(prev => ({ ...prev, end: e.target.value }))}
                    placeholder="结束日期"
                  />
                </div>
                <Button size="sm" onClick={handleDateRangeChange} className="w-full">
                  应用日期范围
                </Button>
              </div>

              <DropdownMenuSeparator />

              {/* 差异金额范围 */}
              <div className="p-3 space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  差异金额范围 (¥)
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="number"
                    placeholder="最小差异"
                    value={filters.difference_range.min || ''}
                    onChange={(e) => handleDifferenceRangeChange('min', e.target.value)}
                  />
                  <Input
                    type="number"
                    placeholder="最大差异"
                    value={filters.difference_range.max || ''}
                    onChange={(e) => handleDifferenceRangeChange('max', e.target.value)}
                  />
                </div>
              </div>

              <DropdownMenuSeparator />

              {/* 差异数量范围 */}
              <div className="p-3 space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  差异数量范围
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="number"
                    placeholder="最小数量"
                    value={filters.discrepancy_range.min || ''}
                    onChange={(e) => handleDiscrepancyRangeChange('min', e.target.value)}
                  />
                  <Input
                    type="number"
                    placeholder="最大数量"
                    value={filters.discrepancy_range.max || ''}
                    onChange={(e) => handleDiscrepancyRangeChange('max', e.target.value)}
                  />
                </div>
              </div>

              <DropdownMenuSeparator />

              {/* 其他筛选条件 */}
              <div className="p-3 space-y-2">
                <label className="text-sm font-medium">其他条件</label>
                <div className="space-y-2">
                  <DropdownMenuCheckboxItem
                    checked={filters.has_discrepancies === true}
                    onCheckedChange={(checked) =>
                      onFiltersChange({
                        ...filters,
                        has_discrepancies: checked ? true : null
                      })
                    }
                  >
                    存在差异
                  </DropdownMenuCheckboxItem>
                  <DropdownMenuCheckboxItem
                    checked={filters.is_auto_matching === true}
                    onCheckedChange={(checked) =>
                      onFiltersChange({
                        ...filters,
                        is_auto_matching: checked ? true : null
                      })
                    }
                  >
                    启用自动匹配
                  </DropdownMenuCheckboxItem>
                </div>
              </div>

              <DropdownMenuSeparator />

              {/* 排序选项 */}
              <div className="p-3 space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  排序方式
                </label>
                <Select
                  value={`${filters.sort_by}-${filters.sort_order}`}
                  onValueChange={handleSortChange}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="created_at-desc">最新创建</SelectItem>
                    <SelectItem value="batch_name-asc">批次名称 A-Z</SelectItem>
                    <SelectItem value="batch_name-desc">批次名称 Z-A</SelectItem>
                    <SelectItem value="period_start-desc">最新周期</SelectItem>
                    <SelectItem value="status-asc">状态排序</SelectItem>
                    <SelectItem value="total_difference-desc">差异从高到低</SelectItem>
                    <SelectItem value="total_difference-asc">差异从低到高</SelectItem>
                    <SelectItem value="completed_at-desc">最近完成</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </DropdownMenuContent>
          </DropdownMenu>

          <Button variant="outline" size="sm" onClick={onReset} disabled={loading}>
            <RotateCcw className="h-4 w-4 mr-2" />
            重置
          </Button>
        </div>
      </div>

      {/* 筛选标签和统计信息 */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2">
          {filters.status !== 'all' && (
            <Badge variant="secondary" className="gap-1">
              状态: {filters.status}
              <X className="h-3 w-3 cursor-pointer" onClick={() => clearTag('status')} />
            </Badge>
          )}
          {filters.platform_spend_source !== 'all' && (
            <Badge variant="secondary" className="gap-1">
              数据源: {filters.platform_spend_source}
              <X className="h-3 w-3 cursor-pointer" onClick={() => clearTag('platform_spend_source')} />
            </Badge>
          )}
          {filters.created_by !== 'all' && (
            <Badge variant="secondary" className="gap-1">
              创建人: {userOptions.find(u => u.value === filters.created_by.toString())?.label || filters.created_by}
              <X className="h-3 w-3 cursor-pointer" onClick={() => clearTag('created_by')} />
            </Badge>
          )}
          {filters.date_range.start && (
            <Badge variant="secondary" className="gap-1">
              日期: {filters.date_range.start} ~ {filters.date_range.end || '至今'}
              <X className="h-3 w-3 cursor-pointer" onClick={() => {
                onFiltersChange({
                  ...filters,
                  date_range: { start: '', end: '' }
                });
              }} />
            </Badge>
          )}
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            共找到 <span className="font-medium text-foreground">{totalCount}</span> 个对账批次
          </span>

          {/* 操作按钮 */}
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={onExport} disabled={loading || totalCount === 0}>
              <Download className="h-4 w-4 mr-2" />
              导出数据
            </Button>
            <Button onClick={onNewBatch} disabled={loading}>
              <Plus className="h-4 w-4 mr-2" />
              新建批次
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ReconciliationFilters;