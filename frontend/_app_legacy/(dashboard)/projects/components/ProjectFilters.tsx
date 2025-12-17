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
  Calendar,
  ChevronDown,
  Users,
  DollarSign,
  Target,
  Clock
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ProjectFilters, ProjectStatus, ProjectPriority, Platform } from '../types';

interface ProjectFiltersProps {
  filters: ProjectFilters;
  onFiltersChange: (filters: ProjectFilters) => void;
  totalCount: number;
  onReset: () => void;
  onExport: () => void;
  onNewProject: () => void;
  loading?: boolean;
}

/**
 * 项目筛选工具栏组件
 *
 * 提供搜索、筛选、批量操作等功能
 */
export function ProjectFilters({
  filters,
  onFiltersChange,
  totalCount,
  onReset,
  onExport,
  onNewProject,
  loading = false
}: ProjectFiltersProps) {
  const [isAdvancedFilterOpen, setIsAdvancedFilterOpen] = useState(false);

  // 状态选项映射
  const statusOptions: { value: ProjectStatus | 'all'; label: string; color?: string }[] = [
    { value: 'all', label: '全部状态' },
    { value: 'planning', label: '规划中', color: 'info' },
    { value: 'active', label: '进行中', color: 'success' },
    { value: 'paused', label: '暂停', color: 'warning' },
    { value: 'completed', label: '已完成', color: 'primary' },
  ];

  // 优先级选项映射
  const priorityOptions: { value: ProjectPriority | 'all'; label: string; color?: string }[] = [
    { value: 'all', label: '全部优先级' },
    { value: 'high', label: '高', color: 'destructive' },
    { value: 'medium', label: '中', color: 'warning' },
    { value: 'low', label: '低', color: 'secondary' },
  ];

  // 平台选项映射
  const platformOptions: { value: Platform | 'all'; label: string }[] = [
    { value: 'all', label: '全部平台' },
    { value: 'facebook', label: 'Facebook' },
    { value: 'google', label: 'Google' },
    { value: 'tiktok', label: 'TikTok' },
    { value: 'instagram', label: 'Instagram' },
    { value: 'youtube', label: 'YouTube' },
    { value: 'twitter', label: 'Twitter' },
    { value: 'linkedin', label: 'LinkedIn' },
  ];

  // 排序选项映射
  const sortOptions = [
    { value: 'name', label: '项目名称' },
    { value: 'created_at', label: '创建时间' },
    { value: 'updated_at', label: '更新时间' },
    { value: 'budget', label: '预算金额' },
    { value: 'roi', label: 'ROI' },
    { value: 'start_date', label: '开始时间' },
  ];

  // 日期范围选项
  const dateRangeOptions = [
    { label: '最近 7 天', days: 7 },
    { label: '最近 30 天', days: 30 },
    { label: '本月', days: 'current_month' },
    { label: '上月', days: 'last_month' },
    { label: '最近 3 个月', days: 90 },
    { label: '自定义', days: 'custom' },
  ];

  // 计算当前筛选结果描述
  const getFilterDescription = () => {
    const parts = [];
    parts.push(`共 ${totalCount} 个项目`);

    if (filters.date_range.start || filters.date_range.end) {
      parts.push('显示自定义日期范围');
    } else {
      parts.push('显示所有时间');
    }

    const activeFilters = [];
    if (filters.status !== 'all') activeFilters.push('状态筛选');
    if (filters.priority !== 'all') activeFilters.push('优先级筛选');
    if (filters.platform !== 'all') activeFilters.push('平台筛选');
    if (filters.search_term) activeFilters.push('搜索条件');
    if (filters.tags.length > 0) activeFilters.push('标签筛选');

    if (activeFilters.length > 0) {
      parts.push(`(${activeFilters.join(' + ')})`);
    }

    return parts.join(' · ');
  };

  // 更新筛选条件
  const updateFilter = (key: keyof ProjectFilters, value: any) => {
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
                  placeholder="按项目名称、客户名称或团队负责人搜索..."
                  value={filters.search_term}
                  onChange={(e) => updateFilter('search_term', e.target.value)}
                  className="pl-10 pr-4"
                />
              </div>
            </div>

            {/* 筛选按钮组 */}
            <div className="flex flex-wrap gap-2">
              {/* 状态筛选 */}
              <Select value={filters.status} onValueChange={(value) => updateFilter('status', value as ProjectStatus | 'all')}>
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

              {/* 排序选择 */}
              <Select value={filters.sort_by} onValueChange={(value) => updateFilter('sort_by', value)}>
                <SelectTrigger className="w-36">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {sortOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* 排序方向 */}
              <Select value={filters.sort_order} onValueChange={(value) => updateFilter('sort_order', value as 'asc' | 'desc')}>
                <SelectTrigger className="w-20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="desc">降序</SelectItem>
                  <SelectItem value="asc">升序</SelectItem>
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
                      <Select value={filters.priority} onValueChange={(value) => updateFilter('priority', value as ProjectPriority | 'all')}>
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

                    {/* 平台筛选 */}
                    <div>
                      <label className="text-sm font-medium mb-2 block">投放平台</label>
                      <Select value={filters.platform} onValueChange={(value) => updateFilter('platform', value as Platform | 'all')}>
                        <SelectTrigger>
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
                    </div>

                    {/* 日期范围筛选 */}
                    <div>
                      <label className="text-sm font-medium mb-2 block">项目时间</label>
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
          {/* 导出数据 */}
          <Button variant="outline" size="sm" onClick={onExport} disabled={loading}>
            <Download className="h-4 w-4 mr-2" />
            导出数据
          </Button>

          {/* 新建项目 */}
          <Button size="sm" onClick={onNewProject}>
            <Plus className="h-4 w-4 mr-2" />
            新建项目
          </Button>
        </div>
      </div>
    </div>
  );
}

export default ProjectFilters;