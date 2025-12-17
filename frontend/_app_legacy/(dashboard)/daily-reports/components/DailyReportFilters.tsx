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
  Target,
  ChevronDown,
  X,
  User,
  FileText,
  AlertTriangle,
  Star,
  Settings
} from 'lucide-react';
import { DailyReportFilters as IDailyReportFilters, ReportStatus, DateRange } from '../types';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';

interface DailyReportFiltersProps {
  filters: IDailyReportFilters;
  onFiltersChange: (filters: IDailyReportFilters) => void;
  totalCount: number;
  onReset: () => void;
  onExport: () => void;
  onNewReport: () => void;
  loading?: boolean;
  projectOptions?: Array<{ value: string; label: string }>;
  accountOptions?: Array<{ value: string; label: string }>;
  userOptions?: Array<{ value: string; label: string }>;
}

/**
 * 日报筛选组件
 *
 * 提供搜索、状态、项目、账户等多维度筛选功能
 */
export function DailyReportFilters({
  filters,
  onFiltersChange,
  totalCount,
  onReset,
  onExport,
  onNewReport,
  loading = false,
  projectOptions = [],
  accountOptions = [],
  userOptions = []
}: DailyReportFiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [tempCustomDateRange, setTempCustomDateRange] = useState({
    start: filters.custom_date_range.start || format(subDays(new Date(), 7), 'yyyy-MM-dd'),
    end: filters.custom_date_range.end || format(new Date(), 'yyyy-MM-dd')
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
      status: value as ReportStatus | 'all'
    });
  };

  // 处理日期范围筛选
  const handleDateRangeChange = (value: string) => {
    onFiltersChange({
      ...filters,
      date_range: value as DateRange
    });
  };

  // 处理自定义日期范围
  const handleCustomDateRangeChange = () => {
    onFiltersChange({
      ...filters,
      date_range: 'custom',
      custom_date_range: {
        start: tempCustomDateRange.start,
        end: tempCustomDateRange.end
      }
    });
    setShowAdvanced(false);
  };

  // 处理项目筛选
  const handleProjectChange = (value: string) => {
    onFiltersChange({
      ...filters,
      project_id: value === 'all' ? 'all' : parseInt(value)
    });
  };

  // 处理账户筛选
  const handleAccountChange = (value: string) => {
    onFiltersChange({
      ...filters,
      account_id: value === 'all' ? 'all' : parseInt(value)
    });
  };

  // 处理提交人筛选
  const handleSubmittedByChange = (value: string) => {
    onFiltersChange({
      ...filters,
      submitted_by: value === 'all' ? 'all' : parseInt(value)
    });
  };

  // 处理消耗范围变化
  const handleSpendRangeChange = (field: 'min' | 'max', value: string) => {
    const numValue = value ? parseFloat(value) : undefined;
    onFiltersChange({
      ...filters,
      spend_range: {
        ...filters.spend_range,
        [field]: numValue
      }
    });
  };

  // 处理ROI范围变化
  const handleRoiRangeChange = (field: 'min' | 'max', value: string) => {
    const numValue = value ? parseFloat(value) : undefined;
    onFiltersChange({
      ...filters,
      roi_range: {
        ...filters.roi_range,
        [field]: numValue
      }
    });
  };

  // 处理质量评分范围变化
  const handleQualityScoreRangeChange = (field: 'min' | 'max', value: string) => {
    const numValue = value ? parseInt(value) : undefined;
    onFiltersChange({
      ...filters,
      quality_score_range: {
        ...filters.quality_score_range,
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
  const clearTag = (key: keyof IDailyReportFilters) => {
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
    if (filters.project_id !== 'all') count++;
    if (filters.account_id !== 'all') count++;
    if (filters.submitted_by !== 'all') count++;
    if (filters.date_range !== 'today') count++;
    if (filters.spend_range.min || filters.spend_range.max) count++;
    if (filters.roi_range.min || filters.roi_range.max) count++;
    if (filters.quality_score_range.min || filters.quality_score_range.max) count++;
    if (filters.has_attachments !== null) count++;
    if (filters.has_anomalies !== null) count++;
    if (filters.tags.length > 0) count++;
    return count;
  };

  const activeFiltersCount = getActiveFiltersCount();

  // 获取日期范围显示文本
  const getDateRangeDisplay = () => {
    switch (filters.date_range) {
      case 'today':
        return '今天';
      case 'yesterday':
        return '昨天';
      case 'last_7_days':
        return '最近7天';
      case 'last_30_days':
        return '最近30天';
      case 'this_month':
        return '本月';
      case 'custom':
        if (filters.custom_date_range.start && filters.custom_date_range.end) {
          return `${filters.custom_date_range.start} ~ ${filters.custom_date_range.end}`;
        }
        return '自定义';
      default:
        return '今天';
    }
  };

  return (
    <div className="bg-card rounded-lg border p-4 space-y-4">
      {/* 基础筛选区域 */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center">
        {/* 搜索框 */}
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜索项目、账户或提交人..."
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
              <SelectItem value="pending">待审核</SelectItem>
              <SelectItem value="approved">已通过</SelectItem>
              <SelectItem value="rejected">已拒绝</SelectItem>
              <SelectItem value="needs_revision">需修改</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filters.date_range} onValueChange={handleDateRangeChange}>
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="日期范围" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today">今天</SelectItem>
              <SelectItem value="yesterday">昨天</SelectItem>
              <SelectItem value="last_7_days">最近7天</SelectItem>
              <SelectItem value="last_30_days">最近30天</SelectItem>
              <SelectItem value="this_month">本月</SelectItem>
              <SelectItem value="custom">自定义</SelectItem>
            </SelectContent>
          </Select>

          {projectOptions.length > 0 && (
            <Select value={filters.project_id.toString()} onValueChange={handleProjectChange}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="项目" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部项目</SelectItem>
                {projectOptions.map(option => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {accountOptions.length > 0 && (
            <Select value={filters.account_id.toString()} onValueChange={handleAccountChange}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="账户" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部账户</SelectItem>
                {accountOptions.map(option => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {userOptions.length > 0 && (
            <Select value={filters.submitted_by.toString()} onValueChange={handleSubmittedByChange}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="提交人" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部提交人</SelectItem>
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

              {/* 自定义日期范围 */}
              {filters.date_range === 'custom' && (
                <div className="p-3 space-y-2">
                  <label className="text-sm font-medium flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    自定义日期范围
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <Input
                      type="date"
                      value={tempCustomDateRange.start}
                      onChange={(e) => setTempCustomDateRange(prev => ({ ...prev, start: e.target.value }))}
                      placeholder="开始日期"
                    />
                    <Input
                      type="date"
                      value={tempCustomDateRange.end}
                      onChange={(e) => setTempCustomDateRange(prev => ({ ...prev, end: e.target.value }))}
                      placeholder="结束日期"
                    />
                  </div>
                  <Button size="sm" onClick={handleCustomDateRangeChange} className="w-full">
                    应用日期范围
                  </Button>
                </div>
              )}

              <DropdownMenuSeparator />

              {/* 消耗范围 */}
              <div className="p-3 space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  消耗金额范围 ($)
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="number"
                    placeholder="最小消耗"
                    value={filters.spend_range.min || ''}
                    onChange={(e) => handleSpendRangeChange('min', e.target.value)}
                  />
                  <Input
                    type="number"
                    placeholder="最大消耗"
                    value={filters.spend_range.max || ''}
                    onChange={(e) => handleSpendRangeChange('max', e.target.value)}
                  />
                </div>
              </div>

              <DropdownMenuSeparator />

              {/* ROI范围 */}
              <div className="p-3 space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Target className="h-4 w-4" />
                  ROI范围
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="number"
                    step="0.1"
                    placeholder="最小ROI"
                    value={filters.roi_range.min || ''}
                    onChange={(e) => handleRoiRangeChange('min', e.target.value)}
                  />
                  <Input
                    type="number"
                    step="0.1"
                    placeholder="最大ROI"
                    value={filters.roi_range.max || ''}
                    onChange={(e) => handleRoiRangeChange('max', e.target.value)}
                  />
                </div>
              </div>

              <DropdownMenuSeparator />

              {/* 数据质量评分范围 */}
              <div className="p-3 space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Star className="h-4 w-4" />
                  质量评分范围 (0-100)
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    placeholder="最低评分"
                    value={filters.quality_score_range.min || ''}
                    onChange={(e) => handleQualityScoreRangeChange('min', e.target.value)}
                  />
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    placeholder="最高评分"
                    value={filters.quality_score_range.max || ''}
                    onChange={(e) => handleQualityScoreRangeChange('max', e.target.value)}
                  />
                </div>
              </div>

              <DropdownMenuSeparator />

              {/* 其他筛选条件 */}
              <div className="p-3 space-y-2">
                <label className="text-sm font-medium">其他条件</label>
                <div className="space-y-2">
                  <DropdownMenuCheckboxItem
                    checked={filters.has_attachments === true}
                    onCheckedChange={(checked) =>
                      onFiltersChange({
                        ...filters,
                        has_attachments: checked ? true : null
                      })
                    }
                  >
                    包含附件
                  </DropdownMenuCheckboxItem>
                  <DropdownMenuCheckboxItem
                    checked={filters.has_anomalies === true}
                    onCheckedChange={(checked) =>
                      onFiltersChange({
                        ...filters,
                        has_anomalies: checked ? true : null
                      })
                    }
                  >
                    异常数据
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
                    <SelectItem value="report_date-desc">最新日期</SelectItem>
                    <SelectItem value="submitted_at-desc">最近提交</SelectItem>
                    <SelectItem value="project_name-asc">项目名称 A-Z</SelectItem>
                    <SelectItem value="account_name-asc">账户名称 A-Z</SelectItem>
                    <SelectItem value="spend_amount-desc">消耗从高到低</SelectItem>
                    <SelectItem value="spend_amount-asc">消耗从低到高</SelectItem>
                    <SelectItem value="roi-desc">ROI从高到低</SelectItem>
                    <SelectItem value="roi-asc">ROI从低到高</SelectItem>
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
          {filters.project_id !== 'all' && (
            <Badge variant="secondary" className="gap-1">
              项目: {projectOptions.find(p => p.value === filters.project_id.toString())?.label || filters.project_id}
              <X className="h-3 w-3 cursor-pointer" onClick={() => clearTag('project_id')} />
            </Badge>
          )}
          {filters.account_id !== 'all' && (
            <Badge variant="secondary" className="gap-1">
              账户: {accountOptions.find(a => a.value === filters.account_id.toString())?.label || filters.account_id}
              <X className="h-3 w-3 cursor-pointer" onClick={() => clearTag('account_id')} />
            </Badge>
          )}
          {filters.submitted_by !== 'all' && (
            <Badge variant="secondary" className="gap-1">
              提交人: {userOptions.find(u => u.value === filters.submitted_by.toString())?.label || filters.submitted_by}
              <X className="h-3 w-3 cursor-pointer" onClick={() => clearTag('submitted_by')} />
            </Badge>
          )}
          {filters.date_range !== 'today' && (
            <Badge variant="secondary" className="gap-1">
              日期: {getDateRangeDisplay()}
              <X className="h-3 w-3 cursor-pointer" onClick={() => {
                onFiltersChange({
                  ...filters,
                  date_range: 'today'
                });
              }} />
            </Badge>
          )}
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            共找到 <span className="font-medium text-foreground">{totalCount}</span> 份日报
          </span>

          {/* 操作按钮 */}
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={onExport} disabled={loading || totalCount === 0}>
              <Download className="h-4 w-4 mr-2" />
              导出数据
            </Button>
            <Button onClick={onNewReport} disabled={loading}>
              <Plus className="h-4 w-4 mr-2" />
              提交日报
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DailyReportFilters;