/**
 * useDashboardFilters Hook
 *
 * Dashboard 筛选状态管理
 * - 日期范围（7d/30d/custom）
 * - 项目筛选
 * - 支持 URL 同步（可选）
 *
 * @see FRONTEND_STYLE_GUIDE v2.3 - Hooks 规范
 */

'use client';

import { useState, useCallback, useMemo } from 'react';
import type { DashboardFiltersState, TimeRange, ProjectOption } from '../types';

// 默认筛选状态
const DEFAULT_FILTERS: DashboardFiltersState = {
  dateRange: '7d',
  projectId: undefined,
  startDate: undefined,
  endDate: undefined,
};

// 模拟项目选项（后续从 API 获取）
const MOCK_PROJECT_OPTIONS: ProjectOption[] = [
  { id: 'all', name: '全部项目' },
  { id: 'proj-001', name: 'ABC公司Q4项目' },
  { id: 'proj-002', name: 'XYZ科技投放' },
  { id: 'proj-003', name: 'DEF品牌推广' },
  { id: 'proj-004', name: 'GHI电商活动' },
];

// 时间范围选项
export const DATE_RANGE_OPTIONS: { value: TimeRange; label: string }[] = [
  { value: '7d', label: '近7天' },
  { value: '30d', label: '近30天' },
  { value: '90d', label: '近90天' },
];

interface UseDashboardFiltersResult {
  // 当前筛选状态
  filters: DashboardFiltersState;

  // 项目选项列表
  projectOptions: ProjectOption[];

  // 状态更新函数
  setDateRange: (range: DashboardFiltersState['dateRange']) => void;
  setProjectId: (projectId: string | undefined) => void;
  setCustomDateRange: (startDate: string, endDate: string) => void;
  resetFilters: () => void;

  // 派生状态
  dateRangeLabel: string;
  projectLabel: string;
  hasActiveFilters: boolean;
}

export function useDashboardFilters(
  initialFilters: Partial<DashboardFiltersState> = {}
): UseDashboardFiltersResult {
  const [filters, setFilters] = useState<DashboardFiltersState>({
    ...DEFAULT_FILTERS,
    ...initialFilters,
  });

  // 设置日期范围
  const setDateRange = useCallback((range: DashboardFiltersState['dateRange']) => {
    setFilters((prev) => ({
      ...prev,
      dateRange: range,
      // 非自定义时清空具体日期
      startDate: range === 'custom' ? prev.startDate : undefined,
      endDate: range === 'custom' ? prev.endDate : undefined,
    }));
  }, []);

  // 设置项目 ID
  const setProjectId = useCallback((projectId: string | undefined) => {
    setFilters((prev) => ({
      ...prev,
      projectId: projectId === 'all' ? undefined : projectId,
    }));
  }, []);

  // 设置自定义日期范围
  const setCustomDateRange = useCallback((startDate: string, endDate: string) => {
    setFilters((prev) => ({
      ...prev,
      dateRange: 'custom',
      startDate,
      endDate,
    }));
  }, []);

  // 重置筛选
  const resetFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
  }, []);

  // 日期范围显示文本
  const dateRangeLabel = useMemo(() => {
    if (filters.dateRange === 'custom' && filters.startDate && filters.endDate) {
      return `${filters.startDate} ~ ${filters.endDate}`;
    }
    const option = DATE_RANGE_OPTIONS.find((o) => o.value === filters.dateRange);
    return option?.label || '近7天';
  }, [filters.dateRange, filters.startDate, filters.endDate]);

  // 项目显示文本
  const projectLabel = useMemo(() => {
    if (!filters.projectId) return '全部项目';
    const project = MOCK_PROJECT_OPTIONS.find((p) => p.id === filters.projectId);
    return project?.name || '全部项目';
  }, [filters.projectId]);

  // 是否有激活的筛选
  const hasActiveFilters = useMemo(() => {
    return (
      filters.dateRange !== DEFAULT_FILTERS.dateRange ||
      filters.projectId !== undefined
    );
  }, [filters.dateRange, filters.projectId]);

  return {
    filters,
    projectOptions: MOCK_PROJECT_OPTIONS,
    setDateRange,
    setProjectId,
    setCustomDateRange,
    resetFilters,
    dateRangeLabel,
    projectLabel,
    hasActiveFilters,
  };
}

export default useDashboardFilters;
