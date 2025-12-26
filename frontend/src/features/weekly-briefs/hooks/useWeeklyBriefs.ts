/**
 * Weekly Briefs React Query Hooks
 *
 * TanStack Query v5 hooks for weekly brief management
 *
 * SoT: docs/10.module-specs/B3-weekly-brief.md §6.1 前端代码块
 * SoT: STATE_MACHINE.md v2.6 (周报状态: draft → submitted)
 * SoT: API_SOT.md v9.0 Section 5.7 (Weekly Brief endpoints)
 *
 * 一句话定义: 管理周报的数据获取和状态变更
 *
 * 周报 2 状态机:
 *   draft → submitted (终态)
 *
 * @module features/weekly-briefs/hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import {
  getWeeklyBriefList,
  getWeeklyBriefById,
  getWeeklyBriefStats,
  getProjectWeeklySummary,
  createWeeklyBrief,
  updateWeeklyBrief,
  submitWeeklyBrief,
  exportWeeklyBriefs,
} from '../services';
import type {
  WeeklyBrief,
  WeeklyBriefListParams,
  WeeklyBriefListResponse,
  WeeklyBriefStats,
  WeeklySummary,
  CreateWeeklyBriefRequest,
  UpdateWeeklyBriefRequest,
  SubmitWeeklyBriefResponse,
} from '../types';

// ========== Query Hooks ==========

/**
 * 获取周报列表
 */
export function useWeeklyBriefList(
  params: WeeklyBriefListParams = {},
  options?: Omit<UseQueryOptions<WeeklyBriefListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.weeklyBriefs.list(params as Record<string, unknown>),
    queryFn: () => getWeeklyBriefList(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}

/**
 * 获取周报详情
 */
export function useWeeklyBriefDetail(
  id: number,
  options?: Omit<UseQueryOptions<WeeklyBrief>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.weeklyBriefs.detail(id),
    queryFn: () => getWeeklyBriefById(id),
    staleTime: 1000 * 60 * 5,
    enabled: id > 0,
    ...options,
  });
}

/**
 * 获取周报统计
 */
export function useWeeklyBriefStats(
  params: { week?: string; week_start?: string } = {},
  options?: Omit<UseQueryOptions<WeeklyBriefStats>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.weeklyBriefs.stats(params as Record<string, unknown>),
    queryFn: () => getWeeklyBriefStats(params),
    staleTime: 1000 * 60 * 5,
    ...options,
  });
}

/**
 * 获取项目周数据汇总
 */
export function useProjectWeeklySummary(
  projectId: number,
  weekStart: string,
  options?: Omit<UseQueryOptions<WeeklySummary>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.weeklyBriefs.projectSummary(projectId, weekStart),
    queryFn: () => getProjectWeeklySummary(projectId, weekStart),
    staleTime: 1000 * 60 * 5,
    enabled: projectId > 0 && !!weekStart,
    ...options,
  });
}

// ========== Mutation Hooks ==========

/**
 * 创建周报
 */
export function useCreateWeeklyBrief() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateWeeklyBriefRequest) => createWeeklyBrief(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.weeklyBriefs.all });
    },
  });
}

/**
 * 更新周报
 */
export function useUpdateWeeklyBrief() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateWeeklyBriefRequest }) =>
      updateWeeklyBrief(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.weeklyBriefs.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.weeklyBriefs.detail(id) });
    },
  });
}

/**
 * 提交周报
 */
export function useSubmitWeeklyBrief() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => submitWeeklyBrief(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.weeklyBriefs.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.weeklyBriefs.detail(id) });
    },
  });
}

/**
 * 导出周报
 */
export function useExportWeeklyBriefs() {
  return useMutation({
    mutationFn: (params: { week?: string; project_id?: number; format?: 'pdf' | 'excel' }) =>
      exportWeeklyBriefs(params),
    onSuccess: (blob, params) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const format = params.format || 'excel';
      const ext = format === 'pdf' ? 'pdf' : 'xlsx';
      a.download = `周度简报_${params.week || new Date().toISOString().slice(0, 10)}.${ext}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
}

// ========== Refresh Hook ==========

/**
 * 刷新周报数据
 * SoT: B3-weekly-brief.md §2.4 数据刷新策略
 *
 * @example
 * ```tsx
 * const { refreshAll, refreshList, refreshStats } = useRefreshWeeklyBriefs();
 * // 刷新所有周报数据
 * refreshAll();
 * // 仅刷新列表
 * refreshList();
 * // 仅刷新统计
 * refreshStats();
 * ```
 */
export function useRefreshWeeklyBriefs() {
  const queryClient = useQueryClient();

  return {
    /** 刷新所有周报数据 */
    refreshAll: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.weeklyBriefs.all });
    },
    /** 刷新周报列表 */
    refreshList: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.weeklyBriefs.list() });
    },
    /** 刷新周报统计 */
    refreshStats: () => {
      queryClient.invalidateQueries({ queryKey: ['weeklyBriefs', 'stats'] });
    },
    /** 刷新单个周报详情 */
    refreshDetail: (id: number) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.weeklyBriefs.detail(id) });
    },
    /** 刷新项目周数据汇总 */
    refreshProjectSummary: (projectId: number, weekStart: string) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.weeklyBriefs.projectSummary(projectId, weekStart) });
    },
  };
}
