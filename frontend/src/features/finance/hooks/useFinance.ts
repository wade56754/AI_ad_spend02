/**
 * Finance Hooks - 财务模块数据钩子
 *
 * SoT References:
 * - API_SOT.md v9.4 §5.7 (财务 API 契约)
 * - BR-FIN.md v1.1 (财务流程规则)
 * - BR-PROFIT.md v1.2 (利润统计规则)
 *
 * Hook 版本说明:
 * - V1 Hooks (useFundOverview, useProfitSummary 等): 已废弃，请迁移到 V2
 * - V2 Hooks (useFundOverviewV2, useProfitOverviewV2 等): 推荐使用
 *
 * Query Key 层级化规范:
 * - ['fund', 'overview', params]          - 资金概览
 * - ['fund', 'distribution', group, params] - 资金分布
 * - ['fund', 'receivables', params]       - 应收明细
 * - ['profit', 'overview', params]        - 盈亏概览
 * - ['profit', 'projects', params]        - 项目利润
 * - ['profit', 'trend', params]           - 利润趋势
 *
 * @module features/finance/hooks
 */

import { useQuery } from '@tanstack/react-query';
import {
  getFundOverview,
  getProjectDistribution,
  getChannelDistribution,
  getReceivables,
  getPayments,
  getFundAlerts,
  getProfitSummary,
  getProfitTrend,
} from '../services/financeApi';

// ============================================================================
// V1 Hooks (已废弃 - Deprecated)
// 请使用下方 V2 Hooks
// ============================================================================

/**
 * 获取资金概览
 * @deprecated 请使用 useFundOverviewV2()
 */
export function useFundOverview(params?: { period_start?: string; period_end?: string }) {
  return useQuery({
    queryKey: ['fund', 'overview', params],
    queryFn: () => getFundOverview(params),
    staleTime: 30000, // 30秒缓存
  });
}

/**
 * 获取项目资金分布
 */
export function useProjectDistribution(params?: {
  period_start?: string;
  period_end?: string;
  top_n?: number;
}) {
  return useQuery({
    queryKey: ['fund', 'distribution', 'projects', params],
    queryFn: () => getProjectDistribution(params),
    staleTime: 30000,
  });
}

/**
 * 获取渠道资金分布
 */
export function useChannelDistribution(params?: {
  period_start?: string;
  period_end?: string;
}) {
  return useQuery({
    queryKey: ['fund', 'distribution', 'channels', params],
    queryFn: () => getChannelDistribution(params),
    staleTime: 30000,
  });
}

/**
 * 获取应收明细
 */
export function useReceivables(params?: {
  status?: 'pending' | 'overdue' | 'paid';
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: ['fund', 'receivables', params],
    queryFn: () => getReceivables(params),
    staleTime: 30000,
  });
}

/**
 * 获取回款记录
 */
export function usePayments(params?: { page?: number; page_size?: number }) {
  return useQuery({
    queryKey: ['fund', 'payments', params],
    queryFn: () => getPayments(params),
    staleTime: 30000,
  });
}

/**
 * 获取资金预警
 */
export function useFundAlerts() {
  return useQuery({
    queryKey: ['fund', 'alerts'],
    queryFn: () => getFundAlerts(),
    staleTime: 30000,
  });
}

/**
 * 获取利润概览
 */
export function useProfitSummary(params?: { period_start?: string; period_end?: string }) {
  return useQuery({
    queryKey: ['profit', 'summary', params],
    queryFn: () => getProfitSummary(params),
    staleTime: 30000,
  });
}

/**
 * 获取利润趋势
 */
export function useProfitTrend(params?: {
  period_start?: string;
  period_end?: string;
  granularity?: 'day' | 'week' | 'month';
}) {
  return useQuery({
    queryKey: ['profit', 'trend', params],
    queryFn: () => getProfitTrend(params),
    staleTime: 30000,
  });
}

// ============================================================================
// V2 Hooks (推荐使用 - Recommended)
// 符合 API_SOT.md v9.4 和最佳实践规范
// ============================================================================

import {
  getFundOverviewV2,
  getReceivablesV2,
  getFundDistributionV2,
  getProfitOverviewV2,
  getProjectProfitsV2,
  getSupplierCostsV2,
  getProfitTrendV2,
} from '../services/financeApi';
import type {
  FundOverviewParams,
  ReceivablesParams,
  FundDistributionParams,
  ProfitOverviewParams,
  ProjectProfitsParams,
  SupplierCostsParams,
  ProfitTrendParams,
} from '../types/finance.types';

// ---------- 资金总览 V2 Hooks ----------

/**
 * 获取资金概览 V2
 *
 * SoT: BR-FIN.md v1.1 §BR-FIN-006 (可用资金公式)
 * 权限: ceo, finance, admin (MASTER.md v4.9 §2.4)
 */
export function useFundOverviewV2(params?: FundOverviewParams) {
  return useQuery({
    queryKey: ['finance', 'fund', 'overview', params],
    queryFn: () => getFundOverviewV2(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * 获取应收账款明细 V2
 */
export function useReceivablesV2(params?: ReceivablesParams) {
  return useQuery({
    queryKey: ['finance', 'fund', 'receivables', params],
    queryFn: () => getReceivablesV2(params),
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * 获取资金分布 V2
 */
export function useFundDistributionV2(params?: FundDistributionParams) {
  return useQuery({
    queryKey: ['finance', 'fund', 'distribution', params],
    queryFn: () => getFundDistributionV2(params),
    staleTime: 1000 * 60 * 5,
  });
}

// ---------- 项目盈亏 V2 Hooks ----------

/**
 * 获取盈亏概览 V2
 */
export function useProfitOverviewV2(params?: ProfitOverviewParams) {
  return useQuery({
    queryKey: ['finance', 'profit', 'overview', params],
    queryFn: () => getProfitOverviewV2(params),
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * 获取项目利润明细 V2
 */
export function useProjectProfitsV2(params?: ProjectProfitsParams) {
  return useQuery({
    queryKey: ['finance', 'profit', 'projects', params],
    queryFn: () => getProjectProfitsV2(params),
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * 获取渠道成本分析 V2
 */
export function useSupplierCostsV2(params?: SupplierCostsParams) {
  return useQuery({
    queryKey: ['finance', 'profit', 'suppliers', params],
    queryFn: () => getSupplierCostsV2(params),
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * 获取利润趋势 V2
 */
export function useProfitTrendV2(params?: ProfitTrendParams) {
  return useQuery({
    queryKey: ['finance', 'profit', 'trend', params],
    queryFn: () => getProfitTrendV2(params),
    staleTime: 1000 * 60 * 5,
  });
}

// ============================================================================
// TASK-FE-FIN-002: 账本 Hook
// ============================================================================

import { apiGet } from '@/lib/api';

interface LedgerParams {
  page?: number;
  page_size?: number;
  type?: 'topup' | 'spend' | 'reversal';
  search?: string;
  start_date?: string;
  end_date?: string;
}

interface LedgerItem {
  id: string;
  type: string;
  amount: number;
  balance_after: number;
  description: string;
  account_name?: string;
  project_name?: string;
  created_at: string;
  ref_id?: string;
}

interface LedgerResponse {
  items: LedgerItem[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * 获取账本流水
 * SoT: API_SOT.md v9.7 (GET /api/v1/ledger/transactions)
 */
export function useLedger(params?: LedgerParams) {
  return useQuery({
    queryKey: ['finance', 'ledger', params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.page) searchParams.set('page', String(params.page));
      if (params?.page_size) searchParams.set('page_size', String(params.page_size));
      if (params?.type) searchParams.set('type', params.type);
      if (params?.search) searchParams.set('search', params.search);
      if (params?.start_date) searchParams.set('start_date', params.start_date);
      if (params?.end_date) searchParams.set('end_date', params.end_date);

      const query = searchParams.toString();
      return apiGet<LedgerResponse>(`/api/v1/ledger/transactions${query ? `?${query}` : ''}`);
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}
