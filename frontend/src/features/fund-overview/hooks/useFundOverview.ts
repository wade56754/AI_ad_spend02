/**
 * Fund Overview React Query Hooks
 *
 * TanStack Query v5 hooks for fund overview data
 *
 * SoT 对齐:
 * - MASTER.md v4.4 §4.5.5: 资金口径定义
 * - MASTER.md v4.4 §6.5: 页面 2 资金总览字段集
 * - A2-fund-overview.md: 模块规格书
 *
 * @module features/fund-overview/hooks
 */

import { useQuery, useQueryClient, type UseQueryOptions } from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import {
  getFundOverview,
  getFundByProject,
  getFundByChannel,
  getReceivables,
  getPayments,
} from '../services';
import type {
  FundOverview,
  FundOverviewParams,
  FundByProjectResponse,
  FundByChannelResponse,
  FundDistributionParams,
  ReceivablesResponse,
  PaymentsResponse,
} from '../types';

// ========== Query Hooks ==========

/**
 * 获取资金概览数据
 *
 * @param params - 查询参数（可选日期范围）
 * @param options - React Query 选项
 * @returns 资金概览查询结果
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useFundOverview({
 *   date_from: '2024-01-01',
 *   date_to: '2024-12-31'
 * });
 * ```
 */
export function useFundOverview(
  params: FundOverviewParams = {},
  options?: Omit<UseQueryOptions<FundOverview>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.fund.overview(params as Record<string, unknown>),
    queryFn: () => getFundOverview(params),
    staleTime: 1000 * 60 * 5, // 5 minutes cache
    ...options,
  });
}

/**
 * 获取资金分布（按项目）
 *
 * @param params - 分页和排序参数
 * @param options - React Query 选项
 * @returns 按项目的资金分布查询结果
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useFundByProject({
 *   page: 1,
 *   page_size: 20,
 *   sort_by: 'topup',
 *   order: 'desc'
 * });
 * ```
 */
export function useFundByProject(
  params: FundDistributionParams = {},
  options?: Omit<UseQueryOptions<FundByProjectResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.fund.byProject(params as Record<string, unknown>),
    queryFn: () => getFundByProject(params),
    staleTime: 1000 * 60 * 5, // 5 minutes cache
    ...options,
  });
}

/**
 * 获取资金分布（按渠道）
 *
 * @param params - 分页和排序参数
 * @param options - React Query 选项
 * @returns 按渠道的资金分布查询结果
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useFundByChannel({
 *   sort_by: 'spend',
 *   order: 'desc'
 * });
 * ```
 */
export function useFundByChannel(
  params: FundDistributionParams = {},
  options?: Omit<UseQueryOptions<FundByChannelResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.fund.byChannel(params as Record<string, unknown>),
    queryFn: () => getFundByChannel(params),
    staleTime: 1000 * 60 * 5, // 5 minutes cache
    ...options,
  });
}

/**
 * 获取应收款列表
 *
 * @param options - React Query 选项
 * @returns 应收款明细查询结果
 */
export function useReceivables(
  options?: Omit<UseQueryOptions<ReceivablesResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.fund.receivables(),
    queryFn: getReceivables,
    staleTime: 1000 * 60 * 5, // 5 minutes cache
    ...options,
  });
}

/**
 * 获取回款记录
 *
 * @param options - React Query 选项
 * @returns 回款记录查询结果
 */
export function usePayments(
  options?: Omit<UseQueryOptions<PaymentsResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.fund.payments(),
    queryFn: getPayments,
    staleTime: 1000 * 60 * 5, // 5 minutes cache
    ...options,
  });
}

// ========== Refresh Hook ==========

/**
 * 刷新资金总览数据
 * SoT: A2-fund-overview.md §2.4 数据刷新策略
 *
 * @example
 * ```tsx
 * const { refreshAll, refreshOverview } = useRefreshFundOverview();
 * // 刷新所有数据
 * refreshAll();
 * // 仅刷新概览
 * refreshOverview();
 * ```
 */
export function useRefreshFundOverview() {
  const queryClient = useQueryClient();

  return {
    /** 刷新所有资金数据 */
    refreshAll: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.fund.all });
    },
    /** 刷新资金概览 */
    refreshOverview: () => {
      queryClient.invalidateQueries({ queryKey: ['fund', 'overview'] });
    },
    /** 刷新按项目分布 */
    refreshByProject: () => {
      queryClient.invalidateQueries({ queryKey: ['fund', 'byProject'] });
    },
    /** 刷新按渠道分布 */
    refreshByChannel: () => {
      queryClient.invalidateQueries({ queryKey: ['fund', 'byChannel'] });
    },
    /** 刷新应收款 */
    refreshReceivables: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.fund.receivables() });
    },
    /** 刷新回款记录 */
    refreshPayments: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.fund.payments() });
    },
  };
}
