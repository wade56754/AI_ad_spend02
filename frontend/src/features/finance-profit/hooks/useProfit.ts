/**
 * Finance Profit React Query Hooks
 *
 * TanStack Query v5 hooks for profit analysis
 * SoT 对齐: BUSINESS_RULES.md v3.1
 */

import {
  useQuery,
  useMutation,
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
 * Fetch profit summary
 */
export function useProfitSummary(
  params: ProfitSummaryParams = {},
  options?: Omit<UseQueryOptions<ProfitSummaryResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.financeProfit.summary(params as Record<string, unknown>),
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
