/**
 * DashboardHeader - Dashboard 页面头部组件
 *
 * 功能：
 * - 页面标题与描述
 * - 日期范围筛选器
 * - 项目筛选器
 * - 快捷操作按钮（提交日报、申请充值）
 *
 * @see FRONTEND_STYLE_GUIDE v2.3 - Header 规范
 */

'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Calendar, Filter, Wallet, FileText, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import type { DashboardFiltersState, ProjectOption, TimeRange } from '../types';
import { DATE_RANGE_OPTIONS } from '../hooks/useDashboardFilters';

interface DashboardHeaderProps {
  /** 当前筛选状态 */
  filters: DashboardFiltersState;
  /** 日期范围显示文本 */
  dateRangeLabel: string;
  /** 项目显示文本 */
  projectLabel: string;
  /** 项目选项列表 */
  projectOptions: ProjectOption[];
  /** 风险预警数量（用于描述文案） */
  alertCount: number;
  /** 是否正在加载 */
  loading?: boolean;
  /** 日期范围变更回调 */
  onDateRangeChange: (range: DashboardFiltersState['dateRange']) => void;
  /** 项目变更回调 */
  onProjectChange: (projectId: string | undefined) => void;
  /** 刷新回调 */
  onRefresh?: () => void;
  className?: string;
}

export function DashboardHeader({
  filters,
  dateRangeLabel,
  projectLabel,
  projectOptions,
  alertCount,
  loading,
  onDateRangeChange,
  onProjectChange,
  onRefresh,
  className,
}: DashboardHeaderProps) {
  const router = useRouter();

  const handleSubmitReport = () => {
    router.push('/dashboard/daily-reports/new');
  };

  const handleRequestTopup = () => {
    router.push('/dashboard/topups/new');
  };

  return (
    <header className={cn('flex flex-col md:flex-row justify-between items-start md:items-center gap-4', className)}>
      {/* 左侧：标题与描述 */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-text-strong">
          概览 Dashboard
        </h1>
        <p className="text-text-muted text-sm mt-1">
          欢迎回来。今日系统运行平稳
          {alertCount > 0 && `，有 ${alertCount} 个高风险项需关注。`}
          {alertCount === 0 && '，暂无风险预警。'}
        </p>
      </div>

      {/* 右侧：筛选器 + 操作按钮 */}
      <div className="flex flex-wrap gap-3">
        {/* 筛选器组 */}
        <div className="flex gap-2">
          {/* 日期范围筛选 */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="gap-2 bg-card-bg border-border-default text-text-body hover:bg-elevated hover:text-text-strong"
              >
                <Calendar className="w-4 h-4" />
                {dateRangeLabel}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="bg-card-bg border-border-default">
              {DATE_RANGE_OPTIONS.map((option) => (
                <DropdownMenuItem
                  key={option.value}
                  onClick={() => onDateRangeChange(option.value)}
                  className={cn(
                    'text-text-body hover:bg-elevated cursor-pointer',
                    filters.dateRange === option.value && 'bg-elevated text-accent'
                  )}
                >
                  {option.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* 项目筛选 */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="gap-2 bg-card-bg border-border-default text-text-body hover:bg-elevated hover:text-text-strong"
              >
                <Filter className="w-4 h-4" />
                {projectLabel}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="bg-card-bg border-border-default max-h-[300px] overflow-y-auto">
              {projectOptions.map((project) => (
                <DropdownMenuItem
                  key={project.id}
                  onClick={() => onProjectChange(project.id === 'all' ? undefined : project.id)}
                  className={cn(
                    'text-text-body hover:bg-elevated cursor-pointer',
                    (filters.projectId === project.id ||
                      (!filters.projectId && project.id === 'all')) &&
                      'bg-elevated text-accent'
                  )}
                >
                  {project.name}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* 刷新按钮 */}
          {onRefresh && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onRefresh}
              disabled={loading}
              className="text-text-muted hover:text-text-body hover:bg-elevated"
              title="刷新数据"
            >
              <RefreshCw className={cn('w-4 h-4', loading && 'animate-spin')} />
            </Button>
          )}
        </div>

        {/* 分隔线 */}
        <div className="hidden md:block h-8 w-px bg-border-muted mx-1" />

        {/* 核心业务快捷入口 */}
        <Button
          size="sm"
          onClick={handleSubmitReport}
          className="gap-2 shadow-lg shadow-accent/20 bg-accent hover:bg-accent-dark"
        >
          <FileText className="w-4 h-4" />
          提交日报
        </Button>
        <Button
          size="sm"
          onClick={handleRequestTopup}
          className="gap-2 bg-success hover:bg-success-dark shadow-lg shadow-success/20"
        >
          <Wallet className="w-4 h-4" />
          申请充值
        </Button>
      </div>
    </header>
  );
}

export default DashboardHeader;
