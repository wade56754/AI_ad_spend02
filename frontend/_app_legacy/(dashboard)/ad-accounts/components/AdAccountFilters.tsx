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
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Search,
  Filter,
  RotateCcw,
  Download,
  Plus,
  Calendar,
  DollarSign,
  Hash,
  ChevronDown,
  X,
  User,
  Building,
  Shield,
  AlertTriangle,
  Settings
} from 'lucide-react';
import { AdAccountFilters as IAdAccountFilters, Platform, AccountStatus, AccountType, RiskLevel } from '../types';
import { format, subDays } from 'date-fns';

interface AdAccountFiltersProps {
  filters: IAdAccountFilters;
  onFiltersChange: (filters: IAdAccountFilters) => void;
  totalCount: number;
  onReset: () => void;
  onExport: () => void;
  onNewAccount: () => void;
  loading?: boolean;
}

/**
 * 广告账户筛选组件
 *
 * 提供搜索、状态、平台、类型等多维度筛选功能
 */
export function AdAccountFilters({
  filters,
  onFiltersChange,
  totalCount,
  onReset,
  onExport,
  onNewAccount,
  loading = false
}: AdAccountFiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [tempDateRange, setTempDateRange] = useState({
    start: filters.date_range.start || format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    end: filters.date_range.end || format(new Date(), 'yyyy-MM-dd')
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
      status: value as AccountStatus | 'all'
    });
  };

  // 处理平台筛选
  const handlePlatformChange = (value: string) => {
    onFiltersChange({
      ...filters,
      platform: value as Platform | 'all'
    });
  };

  // 处理类型筛选
  const handleTypeChange = (value: string) => {
    onFiltersChange({
      ...filters,
      type: value as AccountType | 'all'
    });
  };

  // 处理风险等级筛选
  const handleRiskLevelChange = (value: string) => {
    onFiltersChange({
      ...filters,
      risk_level: value as RiskLevel | 'all'
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

  // 处理预算范围变化
  const handleBudgetRangeChange = (field: 'min' | 'max', value: string) => {
    const numValue = value ? parseFloat(value) : undefined;
    onFiltersChange({
      ...filters,
      balance_range: {
        ...filters.balance_range,
        [field]: numValue
      }
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
  const clearTag = (key: keyof IAdAccountFilters) => {
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
    if (filters.platform !== 'all') count++;
    if (filters.type !== 'all') count++;
    if (filters.risk_level !== 'all') count++;
    if (filters.date_range.start || filters.date_range.end) count++;
    if (filters.balance_range.min || filters.balance_range.max) count++;
    if (filters.spend_range.min || filters.spend_range.max) count++;
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
              placeholder="搜索账户名称、账户ID..."
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
              <SelectItem value="active">投放中</SelectItem>
              <SelectItem value="paused">已暂停</SelectItem>
              <SelectItem value="pending">待审核</SelectItem>
              <SelectItem value="banned">已封禁</SelectItem>
              <SelectItem value="restricted">受限制</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filters.platform} onValueChange={handlePlatformChange}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="平台" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部平台</SelectItem>
              <SelectItem value="facebook">Facebook</SelectItem>
              <SelectItem value="tiktok">TikTok</SelectItem>
              <SelectItem value="google">Google</SelectItem>
              <SelectItem value="twitter">Twitter</SelectItem>
              <SelectItem value="instagram">Instagram</SelectItem>
              <SelectItem value="youtube">YouTube</SelectItem>
              <SelectItem value="linkedin">LinkedIn</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filters.type} onValueChange={handleTypeChange}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部类型</SelectItem>
              <SelectItem value="personal">个人</SelectItem>
              <SelectItem value="business">商业</SelectItem>
              <SelectItem value="agency">代理商</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filters.risk_level} onValueChange={handleRiskLevelChange}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="风险" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部风险</SelectItem>
              <SelectItem value="low">低风险</SelectItem>
              <SelectItem value="medium">中风险</SelectItem>
              <SelectItem value="high">高风险</SelectItem>
              <SelectItem value="critical">紧急</SelectItem>
            </SelectContent>
          </Select>
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
                  创建日期范围
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

              {/* 余额范围 */}
              <div className="p-3 space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  账户余额范围 ($)
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="number"
                    placeholder="最小余额"
                    value={filters.balance_range.min || ''}
                    onChange={(e) => handleBudgetRangeChange('min', e.target.value)}
                  />
                  <Input
                    type="number"
                    placeholder="最大余额"
                    value={filters.balance_range.max || ''}
                    onChange={(e) => handleBudgetRangeChange('max', e.target.value)}
                  />
                </div>
              </div>

              <DropdownMenuSeparator />

              {/* 消耗范围 */}
              <div className="p-3 space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Hash className="h-4 w-4" />
                  当前消耗范围 ($)
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
                    <SelectItem value="updated_at-desc">最近更新</SelectItem>
                    <SelectItem value="created_at-desc">最新创建</SelectItem>
                    <SelectItem value="account_name-asc">账户名称 A-Z</SelectItem>
                    <SelectItem value="account_name-desc">账户名称 Z-A</SelectItem>
                    <SelectItem value="current_spend-desc">消耗从高到低</SelectItem>
                    <SelectItem value="current_spend-asc">消耗从低到高</SelectItem>
                    <SelectItem value="balance-desc">余额从高到低</SelectItem>
                    <SelectItem value="balance-asc">余额从低到高</SelectItem>
                    <SelectItem value="last_active-desc">最近活跃</SelectItem>
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
          {filters.platform !== 'all' && (
            <Badge variant="secondary" className="gap-1">
              平台: {filters.platform}
              <X className="h-3 w-3 cursor-pointer" onClick={() => clearTag('platform')} />
            </Badge>
          )}
          {filters.type !== 'all' && (
            <Badge variant="secondary" className="gap-1">
              类型: {filters.type}
              <X className="h-3 w-3 cursor-pointer" onClick={() => clearTag('type')} />
            </Badge>
          )}
          {filters.risk_level !== 'all' && (
            <Badge variant="secondary" className="gap-1">
              风险: {filters.risk_level}
              <X className="h-3 w-3 cursor-pointer" onClick={() => clearTag('risk_level')} />
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
            共找到 <span className="font-medium text-foreground">{totalCount}</span> 个账户
          </span>

          {/* 操作按钮 */}
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={onExport} disabled={loading || totalCount === 0}>
              <Download className="h-4 w-4 mr-2" />
              导出数据
            </Button>
            <Button onClick={onNewAccount} disabled={loading}>
              <Plus className="h-4 w-4 mr-2" />
              新建账户
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdAccountFilters;