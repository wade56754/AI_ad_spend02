/**
 * Ad Spend React Query Hooks
 *
 * TanStack Query v5 hooks for ad spend management
 *
 * SoT: docs/10.module-specs/C3-spend-detail.md §6.1 前端代码块
 * SoT: MASTER.md v4.4 §4.5.7 - 消耗 SoT = ad_spend_daily.spend
 * SoT: API_SOT.md v9.0 Section 5 (Ad Spend endpoints)
 *
 * 一句话定义: 管理广告消耗数据的获取和导入导出
 *
 * 消耗 SoT 约束 (C3-spend-detail.md §1.4):
 *   Phase 1: ad_spend_daily.spend (Excel 导入)
 *   Phase 2: daily_report.real_spend (supervisor/finance 确认)
 *
 * Author: AI 代码工厂 v2.4
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import {
  getAdSpendList,
  getAdSpendSummary,
  getAdSpendTrend,
  getAdSpendByProject,
  getAdSpendByAccount,
  exportAdSpend,
  importAdSpend,
} from '../services';
import type {
  AdSpendListParams,
  AdSpendSummaryParams,
  AdSpendListResponse,
  AdSpendSummary,
  AdSpendTrendResponse,
  AdSpendByProject,
  AdSpendByAccount,
} from '../types';

// ========== Query Hooks ==========

/**
 * 获取消耗列表
 */
export function useAdSpendList(
  params: AdSpendListParams = {},
  options?: Omit<UseQueryOptions<AdSpendListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.adSpend.list(params as Record<string, unknown>),
    queryFn: () => getAdSpendList(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}

/**
 * 获取消耗汇总统计
 */
export function useAdSpendSummary(
  params: AdSpendSummaryParams = {},
  options?: Omit<UseQueryOptions<AdSpendSummary>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.adSpend.summary(params as Record<string, unknown>),
    queryFn: () => getAdSpendSummary(params),
    staleTime: 1000 * 60 * 5,
    ...options,
  });
}

/**
 * 获取消耗趋势数据
 */
export function useAdSpendTrend(
  params: AdSpendSummaryParams = {},
  options?: Omit<UseQueryOptions<AdSpendTrendResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.adSpend.trend(params as Record<string, unknown>),
    queryFn: () => getAdSpendTrend(params),
    staleTime: 1000 * 60 * 5,
    ...options,
  });
}

/**
 * 获取按项目汇总的消耗
 */
export function useAdSpendByProject(
  params: AdSpendSummaryParams = {},
  options?: Omit<UseQueryOptions<AdSpendByProject[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.adSpend.byProject(params as Record<string, unknown>),
    queryFn: () => getAdSpendByProject(params),
    staleTime: 1000 * 60 * 5,
    ...options,
  });
}

/**
 * 获取按账户汇总的消耗
 */
export function useAdSpendByAccount(
  params: AdSpendSummaryParams = {},
  options?: Omit<UseQueryOptions<AdSpendByAccount[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.adSpend.byAccount(params as Record<string, unknown>),
    queryFn: () => getAdSpendByAccount(params),
    staleTime: 1000 * 60 * 5,
    ...options,
  });
}

// ========== Mutation Hooks ==========

/**
 * 导出消耗数据
 */
export function useExportAdSpend() {
  return useMutation({
    mutationFn: (params: AdSpendListParams) => exportAdSpend(params),
    onSuccess: (blob) => {
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `消耗明细_${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
}

/**
 * 导入消耗数据
 */
export function useImportAdSpend() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, sourcePlatform }: { file: File; sourcePlatform: string }) =>
      importAdSpend(file, sourcePlatform),
    onSuccess: () => {
      // 导入成功后刷新列表
      queryClient.invalidateQueries({ queryKey: queryKeys.adSpend.all });
    },
  });
}

// ========== Refresh Hook ==========

/**
 * 刷新广告消耗数据
 * SoT: C3-spend-detail.md 数据刷新策略
 *
 * @example
 * ```tsx
 * const { refreshAll, refreshList, refreshSummary, refreshTrend } = useRefreshAdSpend();
 * // 刷新所有消耗数据
 * refreshAll();
 * // 仅刷新列表
 * refreshList();
 * // 仅刷新汇总统计
 * refreshSummary();
 * // 仅刷新趋势数据
 * refreshTrend();
 * ```
 */
export function useRefreshAdSpend() {
  const queryClient = useQueryClient();

  return {
    /** 刷新所有消耗数据 */
    refreshAll: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adSpend.all });
    },
    /** 刷新消耗列表 */
    refreshList: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adSpend.list() });
    },
    /** 刷新汇总统计 */
    refreshSummary: () => {
      queryClient.invalidateQueries({ queryKey: ['adSpend', 'summary'] });
    },
    /** 刷新趋势数据 */
    refreshTrend: () => {
      queryClient.invalidateQueries({ queryKey: ['adSpend', 'trend'] });
    },
    /** 刷新按项目汇总 */
    refreshByProject: () => {
      queryClient.invalidateQueries({ queryKey: ['adSpend', 'byProject'] });
    },
    /** 刷新按账户汇总 */
    refreshByAccount: () => {
      queryClient.invalidateQueries({ queryKey: ['adSpend', 'byAccount'] });
    },
  };
}
