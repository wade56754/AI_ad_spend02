'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  Filter,
  RotateCcw,
  Download,
  Plus,
  CheckSquare,
  Calendar,
  ChevronDown
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { RechargeFilters, RechargeStatus, Platform, Priority, PaymentMethod } from '../types';

interface RechargeFiltersProps {
  filters: RechargeFilters;
  onFiltersChange: (filters: RechargeFilters) => void;
  totalCount: number;
  onReset: () => void;
  onExport: () => void;
  onNewRequest: () => void;
  selectedCount?: number;
  onBatchApprove?: () => void;
  loading?: boolean;
}

/**
 * 充值管理筛选工具栏组件
 *
 * 提供搜索、筛选、批量操作等功能
 */
export function RechargeFilters({
  filters,
  onFiltersChange,
  totalCount,
  onReset,
  onExport,
  onNewRequest,
  selectedCount = 0,
  onBatchApprove,
  loading = false
}: RechargeFiltersProps) {
  const [isAdvancedFilterOpen, setIsAdvancedFilterOpen] = useState(false);

  // 状态选项映射
  const statusOptions: { value: RechargeStatus | 'all'; label: string; color?: string }[] = [
    { value: 'all', label: '全部状态' },
    { value: 'pending', label: '待审核', color: 'warning' },
    { value: 'processing', label: '充值中', color: 'info' },
    { value: 'completed', label: '已完成', color: 'success' },
    { value: 'rejected', label: '已驳回', color: 'destructive' },
    { value: 'cancelled', label: '已取消', color: 'secondary' },
  ];

  // 平台选项映射
  const platformOptions: { value: Platform | 'all'; label: string }[] = [
    { value: 'all', label: '全部平台' },
    { value: 'facebook', label: 'Facebook' },
    { value: 'google', label: 'Google' },
    { value: 'tiktok', label: 'TikTok' },
  ];

  // 优先级选项映射
  const priorityOptions: { value: Priority | 'all'; label: string; color?: string }[] = [
    { value: 'all', label: '全部优先级' },
    { value: 'urgent', label: '紧急', color: 'destructive' },
    { value: 'high', label: '高', color: 'warning' },
    { value: 'normal', label: '中', color: 'default' },
    { value: 'low', label: '低', color: 'secondary' },
  ];

  // 支付方式选项映射
  const paymentMethodOptions: { value: PaymentMethod | 'all'; label: string }[] = [
    { value: 'all', label: '全部支付方式' },
    { value: 'alipay', label: '支付宝' },
    { value: 'wechat', label: '微信支付' },
    { value: 'bank_transfer', label: '银行转账' },
    { value: 'credit_card', label: '信用卡' },
  ];

  // 日期范围选项
  const dateRangeOptions = [
    { label: '最近 7 天', days: 7 },
    { label: '最近 30 天', days: 30 },
    { label: '本月', days: 'current_month' },
    { label: '上月', days: 'last_month' },
    { label: '自定义', days: 'custom' },
  ];

  // 计算当前筛选结果描述
  const getFilterDescription = () => {
    const parts = [];
    parts.push(`共 ${totalCount} 条充值申请`);

    if (filters.date_range.start || filters.date_range.end) {
      parts.push('显示自定义日期范围');
    } else {
      parts.push('显示最近 7 天');
    }

    const activeFilters = [];
    if (filters.status !== 'all') activeFilters.push('状态筛选');
    if (filters.platform !== 'all') activeFilters.push('平台筛选');
    if (filters.priority !== 'all') activeFilters.push('优先级筛选');
    if (filters.payment_method !== 'all') activeFilters.push('支付方式筛选');
    if (filters.search_term) activeFilters.push('搜索条件');

    if (activeFilters.length > 0) {
      parts.push(`(${activeFilters.join(' + ')})`);
    }

    return parts.join(' · ');
  };

  // 更新筛选条件
  const updateFilter = (key: keyof RechargeFilters, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value,
    });
  };

  // 更新日期范围
  const updateDateRange = (days: number | 'current_month' | 'last_month' | 'custom') => {
    let start: string | undefined;
    let end: string | undefined;

    if (days === 'custom') {
      // 可以在这里打开日期选择器，暂时不实现
      return;
    } else if (days === 'current_month') {
      const now = new Date();
      start = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
      end = now.toISOString().split('T')[0];
    } else if (days === 'last_month') {
      const now = new Date();
      start = new Date(now.getFullYear(), now.getMonth() - 1, 1).toISOString().split('T')[0];
      end = new Date(now.getFullYear(), now.getMonth(), 0).toISOString().split('T')[0];
    } else if (typeof days === 'number') {
      const endDate = new Date();
      const startDate = new Date(endDate.getTime() - days * 24 * 60 * 60 * 1000);
      start = startDate.toISOString().split('T')[0];
      end = endDate.toISOString().split('T')[0];
    }

    updateFilter('date_range', { start, end });
  };

  return (
    <div className="space-y-4">
      {/* 主要筛选栏 */}
      <Card className="bg-card border-border">
        <CardContent className="p-4">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* 搜索框 */}
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  placeholder="按申请单号、账户名称或申请人搜索..."
                  value={filters.search_term}
                  onChange={(e) => updateFilter('search_term', e.target.value)}
                  className="pl-10 pr-4"
                />
              </div>
            </div>

            {/* 筛选按钮组 */}
            <div className="flex flex-wrap gap-2">
              {/* 状态筛选 */}
              <Select value={filters.status} onValueChange={(value) => updateFilter('status', value as RechargeStatus | 'all')}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {statusOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      <div className="flex items-center gap-2">
                        {option.color && (
                          <div className={`w-2 h-2 rounded-full bg-${option.color}-500`} />
                        )}
                        {option.label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* 平台筛选 */}
              <Select value={filters.platform} onValueChange={(value) => updateFilter('platform', value as Platform | 'all')}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {platformOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* 更多筛选选项 */}
              <DropdownMenu open={isAdvancedFilterOpen} onOpenChange={setIsAdvancedFilterOpen}>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" className="gap-2">
                    <Filter className="h-4 w-4" />
                    更多筛选
                    <ChevronDown className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-80">
                  <div className="p-4 space-y-4">
                    {/* 优先级筛选 */}
                    <div>
                      <label className="text-sm font-medium mb-2 block">优先级</label>
                      <Select value={filters.priority} onValueChange={(value) => updateFilter('priority', value as Priority | 'all')}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {priorityOptions.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              <div className="flex items-center gap-2">
                                {option.color && (
                                  <div className={`w-2 h-2 rounded-full bg-${option.color}-500`} />
                                )}
                                {option.label}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* 支付方式筛选 */}
                    <div>
                      <label className="text-sm font-medium mb-2 block">支付方式</label>
                      <Select value={filters.payment_method} onValueChange={(value) => updateFilter('payment_method', value as PaymentMethod | 'all')}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {paymentMethodOptions.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* 日期范围筛选 */}
                    <div>
                      <label className="text-sm font-medium mb-2 block">时间范围</label>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="outline" className="w-full justify-between">
                            <Calendar className="h-4 w-4 mr-2" />
                            {dateRangeOptions.find(opt => opt.days === 7)?.label || '最近 7 天'}
                            <ChevronDown className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent>
                          {dateRangeOptions.map((option) => (
                            <DropdownMenuItem
                              key={option.label}
                              onClick={() => updateDateRange(option.days)}
                            >
                              {option.label}
                            </DropdownMenuItem>
                          ))}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    <DropdownMenuSeparator />

                    {/* 重置按钮 */}
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => {
                        onReset();
                        setIsAdvancedFilterOpen(false);
                      }}
                    >
                      <RotateCcw className="h-4 w-4 mr-2" />
                      重置筛选
                    </Button>
                  </div>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 操作栏 */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {getFilterDescription()}
        </div>

        <div className="flex items-center gap-2">
          {/* 批量操作（有选中项时显示） */}
          {selectedCount > 0 && (
            <>
              <Badge variant="secondary" className="gap-1">
                <CheckSquare className="h-3 w-3" />
                已选 {selectedCount} 条
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={onBatchApprove}
                disabled={!onBatchApprove}
              >
                批量审核
              </Button>
            </>
          )}

          {/* 导出记录 */}
          <Button variant="outline" size="sm" onClick={onExport} disabled={loading}>
            <Download className="h-4 w-4 mr-2" />
            导出记录
          </Button>

          {/* 新建充值申请 */}
          <Button size="sm" onClick={onNewRequest}>
            <Plus className="h-4 w-4 mr-2" />
            新建充值申请
          </Button>
        </div>
      </div>
    </div>
  );
}

export default RechargeFilters;