/**
 * Finance Profit React Query Hooks
 *
 * TanStack Query v5 hooks for profit analysis
 *
 * SoT: docs/10.module-specs/A3-project-pnl.md §2.4 数据刷新策略
 * SoT: MASTER.md v4.4 §6.5 页面 3 项目盈亏字段集
 * SoT: BUSINESS_RULES.md v3.2: 利润计算公式
 *
 * @module features/finance-profit/hooks
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import {
  getProfitSummary,
  getProfitOverview,
  getProfitByProject,
  getProfitByAccount,
  getProfitByChannel,
  getProfitTrend,
  compareProfits,
} from '../services';
import type {
  ProfitSummaryResponse,
  ProfitOverviewResponse,
  ProfitByProjectResponse,
  ProfitByAccountResponse,
  ProfitByChannelResponse,
  ProfitTrendResponse,
  ProfitCompareResponse,
  ProfitSummaryParams,
  ProfitByDimensionParams,
  ProfitTrendParams,
  ProfitCompareParams,
} from '../types';

// ========== Query Hooks ==========

/**
 * Fetch profit overview (today/week/month)
 */
export function useProfitOverview(
  options?: Omit<UseQueryOptions<ProfitOverviewResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.financeProfit.overview(),
    queryFn: getProfitOverview,
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}

/**
 * Fetch profit summary for a specific month
 * @param params.year - 年份 (2020-2099)
 * @param params.month - 月份 (1-12)
 */
export function useProfitSummary(
  params: ProfitSummaryParams,
  options?: Omit<UseQueryOptions<ProfitSummaryResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.financeProfit.summary({ year: params.year, month: params.month }),
    queryFn: () => getProfitSummary(params),
    ...options,
  });
}

/**
 * Fetch profit by project
 */
export function useProfitByProject(
  params: ProfitByDimensionParams = {},
  options?: Omit<UseQueryOptions<ProfitByProjectResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.financeProfit.byProject(params as Record<string, unknown>),
    queryFn: () => getProfitByProject(params),
    ...options,
  });
}

/**
 * Fetch profit by account
 */
export function useProfitByAccount(
  params: ProfitByDimensionParams = {},
  options?: Omit<UseQueryOptions<ProfitByAccountResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.financeProfit.byAccount(params as Record<string, unknown>),
    queryFn: () => getProfitByAccount(params),
    ...options,
  });
}

/**
 * Fetch profit by channel
 */
export function useProfitByChannel(
  params: ProfitByDimensionParams = {},
  options?: Omit<UseQueryOptions<ProfitByChannelResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.financeProfit.byChannel(params as Record<string, unknown>),
    queryFn: () => getProfitByChannel(params),
    ...options,
  });
}

/**
 * Fetch profit trend
 */
export function useProfitTrend(
  params: ProfitTrendParams = {},
  options?: Omit<UseQueryOptions<ProfitTrendResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.financeProfit.trend(params as Record<string, unknown>),
    queryFn: () => getProfitTrend(params),
    ...options,
  });
}

/**
 * Compare profits mutation (POST endpoint)
 */
export function useCompareProfits() {
  return useMutation({
    mutationFn: (params: ProfitCompareParams) => compareProfits(params),
  });
}

/**
 * Prefetch profit data for better UX
 */
export function usePrefetchProfitData() {
  // This can be used to prefetch common queries
  return {
    prefetchOverview: () => {
      // Implementation would use queryClient.prefetchQuery
    },
  };
}

// ========== Refresh Hook ==========

/**
 * 刷新利润分析数据
 * SoT: A3-project-pnl.md §2.4 数据刷新策略
 *
 * @example
 * ```tsx
 * const { refreshAll, refreshOverview } = useRefreshProfit();
 * // 刷新所有数据
 * refreshAll();
 * // 仅刷新概览
 * refreshOverview();
 * ```
 */
export function useRefreshProfit() {
  const queryClient = useQueryClient();

  return {
    /** 刷新所有利润数据 */
    refreshAll: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.financeProfit.all });
    },
    /** 刷新利润概览 */
    refreshOverview: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.financeProfit.overview() });
    },
    /** 刷新按项目利润 */
    refreshByProject: () => {
      queryClient.invalidateQueries({ queryKey: ['financeProfit', 'byProject'] });
    },
    /** 刷新按账户利润 */
    refreshByAccount: () => {
      queryClient.invalidateQueries({ queryKey: ['financeProfit', 'byAccount'] });
    },
    /** 刷新按渠道利润 */
    refreshByChannel: () => {
      queryClient.invalidateQueries({ queryKey: ['financeProfit', 'byChannel'] });
    },
    /** 刷新利润趋势 */
    refreshTrend: () => {
      queryClient.invalidateQueries({ queryKey: ['financeProfit', 'trend'] });
    },
  };
}
