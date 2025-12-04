'use client';

import { Calendar, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { DashboardFilters as FilterState, ProjectOption } from '../types';

interface DashboardFiltersProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  projects: ProjectOption[];
  onRefresh?: () => void;
  loading?: boolean;
  className?: string;
}

const DATE_RANGE_OPTIONS = [
  { value: 'today', label: '今日' },
  { value: '7d', label: '近7天' },
  { value: '30d', label: '近30天' },
] as const;

export function DashboardFilters({
  filters,
  onFiltersChange,
  projects,
  onRefresh,
  loading = false,
  className = ''
}: DashboardFiltersProps) {
  const handleDateRangeChange = (value: string) => {
    onFiltersChange({
      ...filters,
      dateRange: value as FilterState['dateRange']
    });
  };

  const handleProjectChange = (value: string) => {
    onFiltersChange({
      ...filters,
      projectId: value === 'all' ? undefined : value
    });
  };

  return (
    <div className={`flex flex-wrap items-center justify-between gap-4 ${className}`}>
      {/* 左侧筛选器 */}
      <div className="flex flex-wrap items-center gap-3">
        {/* 日期范围选择 */}
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <Select
            value={filters.dateRange}
            onValueChange={handleDateRangeChange}
          >
            <SelectTrigger className="w-[120px] h-9">
              <SelectValue placeholder="选择日期" />
            </SelectTrigger>
            <SelectContent>
              {DATE_RANGE_OPTIONS.map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* 项目筛选 */}
        <Select
          value={filters.projectId || 'all'}
          onValueChange={handleProjectChange}
        >
          <SelectTrigger className="w-[180px] h-9">
            <SelectValue placeholder="选择项目" />
          </SelectTrigger>
          <SelectContent>
            {projects.map(project => (
              <SelectItem key={project.id} value={project.id}>
                {project.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* 右侧刷新按钮 */}
      <Button
        variant="outline"
        size="sm"
        onClick={onRefresh}
        disabled={loading}
        className="h-9"
      >
        <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
        刷新数据
      </Button>
    </div>
  );
}

export default DashboardFilters;
