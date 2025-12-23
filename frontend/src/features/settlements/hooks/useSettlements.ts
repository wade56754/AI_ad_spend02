/**
 * Settlements React Query Hooks
 *
 * TanStack Query v5 hooks for settlement management
 *
 * SoT: docs/10.module-specs/D1-monthly-settlement.md §6.1 前端代码块
 * SoT: DATA_SCHEMA.md v5.2
 * SoT: LEDGER_SOT.md v1.1
 *
 * 一句话定义: 管理结算的数据获取和状态变更（通用结算 + 月度结算）
 *
 * 月度结算状态机 (D1-monthly-settlement.md §2.4):
 *   pending → draft → confirmed → locked (终态)
 *
 * Author: AI 代码工厂 v2.4
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';
import {
  getSettlements,
  getSettlement,
  getSettlementStatistics,
  getOverdueSettlements,
  getSettlementPayments,
  createSettlement,
  updateSettlement,
  submitSettlement,
  approveSettlement,
  recordPayment,
  cancelSettlement,
  // 月度结算 API
  getMonthlySettlements,
  getMonthlySettlement,
  getMonthlySettlementSummary,
  generateMonthlySettlement,
  confirmMonthlySettlement,
  lockMonthlySettlement,
  unlockMonthlySettlement,
  exportMonthlySettlement,
} from '../services';
import type {
  Settlement,
  SettlementListParams,
  SettlementCreateInput,
  SettlementUpdateInput,
  SettlementApproveInput,
  SettlementPaymentInput,
  SettlementStatistics,
  SettlementPayment,
  // 月度结算类型
  MonthlySettlement,
  MonthlySettlementListParams,
  MonthlySettlementListResponse,
  MonthlySettlementSummary,
  GenerateMonthlySettlementRequest,
  MonthlySettlementActionRequest,
} from '../types';

// ========== Query Hooks ==========

/**
 * Fetch paginated settlement list
 */
export function useSettlements(
  params: SettlementListParams = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<Settlement>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.settlements.list(params),
    queryFn: () => getSettlements(params),
    ...options,
  });
}

/**
 * Fetch single settlement by ID
 */
export function useSettlement(
  id: number,
  options?: Omit<UseQueryOptions<Settlement>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.settlements.detail(id),
    queryFn: () => getSettlement(id),
    enabled: !!id,
    ...options,
  });
}

/**
 * Fetch settlement statistics
 */
export function useSettlementStatistics(
  params: { start_date?: string; end_date?: string } = {},
  options?: Omit<UseQueryOptions<SettlementStatistics>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.settlements.statistics(params),
    queryFn: () => getSettlementStatistics(params),
    ...options,
  });
}

/**
 * Fetch overdue settlements
 */
export function useOverdueSettlements(
  options?: Omit<UseQueryOptions<Settlement[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.settlements.overdue(),
    queryFn: getOverdueSettlements,
    ...options,
  });
}

/**
 * Fetch settlement payments
 */
export function useSettlementPayments(
  settlementId: number,
  options?: Omit<UseQueryOptions<SettlementPayment[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.settlements.payments(settlementId),
    queryFn: () => getSettlementPayments(settlementId),
    enabled: !!settlementId,
    ...options,
  });
}

// ========== Mutation Hooks ==========

/**
 * Create settlement mutation
 */
export function useCreateSettlement(
  options?: UseMutationOptions<Settlement, Error, SettlementCreateInput>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createSettlement,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.all });
    },
    ...options,
  });
}

/**
 * Update settlement mutation
 */
export function useUpdateSettlement(
  options?: UseMutationOptions<Settlement, Error, { id: number; input: SettlementUpdateInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => updateSettlement(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.settlements.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.lists() });
    },
    ...options,
  });
}

// ========== Workflow Action Hooks ==========

/**
 * Submit settlement for approval
 * State transition: DRAFT -> PENDING
 */
export function useSubmitSettlement(
  options?: UseMutationOptions<Settlement, Error, number>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: submitSettlement,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.settlements.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.statistics({}) });
    },
    ...options,
  });
}

/**
 * Approve settlement mutation
 * State transition: PENDING -> APPROVED / REJECTED
 */
export function useApproveSettlement(
  options?: UseMutationOptions<Settlement, Error, { id: number; input: SettlementApproveInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => approveSettlement(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.settlements.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.statistics({}) });
    },
    ...options,
  });
}

/**
 * Record payment mutation
 * Creates ledger entries per LEDGER_SOT.md v1.1
 */
export function useRecordPayment(
  options?: UseMutationOptions<Settlement, Error, { id: number; input: SettlementPaymentInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => recordPayment(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.settlements.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.statistics({}) });
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.payments(id) });
      // Invalidate ledger cache as payment creates ledger entries
      queryClient.invalidateQueries({ queryKey: queryKeys.ledger.all });
    },
    ...options,
  });
}

/**
 * Cancel settlement mutation
 * State transition: DRAFT/APPROVED -> CANCELLED
 */
export function useCancelSettlement(
  options?: UseMutationOptions<Settlement, Error, { id: number; reason?: string }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }) => cancelSettlement(id, reason),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.settlements.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.statistics({}) });
    },
    ...options,
  });
}

// ========== 月度结算 Query Hooks (D1-monthly-settlement.md §6.1) ==========

/**
 * 获取月度结算列表
 */
export function useMonthlySettlements(
  params: MonthlySettlementListParams = {},
  options?: Omit<UseQueryOptions<MonthlySettlementListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['monthlySettlements', 'list', params],
    queryFn: () => getMonthlySettlements(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}

/**
 * 获取月度结算详情
 */
export function useMonthlySettlement(
  id: number,
  options?: Omit<UseQueryOptions<MonthlySettlement>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['monthlySettlements', 'detail', id],
    queryFn: () => getMonthlySettlement(id),
    enabled: id > 0,
    ...options,
  });
}

/**
 * 获取月度结算汇总
 */
export function useMonthlySettlementSummary(
  month?: string,
  options?: Omit<UseQueryOptions<MonthlySettlementSummary>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['monthlySettlements', 'summary', month],
    queryFn: () => getMonthlySettlementSummary(month),
    staleTime: 1000 * 60 * 5,
    ...options,
  });
}

// ========== 月度结算 Mutation Hooks ==========

/**
 * 生成月度结算
 * SoT: D1-monthly-settlement.md §4.1
 */
export function useGenerateMonthlySettlement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: GenerateMonthlySettlementRequest) => generateMonthlySettlement(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monthlySettlements'] });
    },
  });
}

/**
 * 确认月度结算
 * 状态转换: draft → confirmed
 * SoT: D1-monthly-settlement.md §2.4
 */
export function useConfirmMonthlySettlement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: number; input?: MonthlySettlementActionRequest }) =>
      confirmMonthlySettlement(id, input),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['monthlySettlements'] });
      queryClient.invalidateQueries({ queryKey: ['monthlySettlements', 'detail', id] });
    },
  });
}

/**
 * 锁定月度结算
 * 状态转换: confirmed → locked (终态)
 * SoT: D1-monthly-settlement.md §2.4
 */
export function useLockMonthlySettlement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: number; input?: MonthlySettlementActionRequest }) =>
      lockMonthlySettlement(id, input),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['monthlySettlements'] });
      queryClient.invalidateQueries({ queryKey: ['monthlySettlements', 'detail', id] });
    },
  });
}

/**
 * 解锁月度结算 (admin only)
 * 状态转换: locked → confirmed
 * SoT: D1-monthly-settlement.md §4.1
 */
export function useUnlockMonthlySettlement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: number; input?: MonthlySettlementActionRequest }) =>
      unlockMonthlySettlement(id, input),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['monthlySettlements'] });
      queryClient.invalidateQueries({ queryKey: ['monthlySettlements', 'detail', id] });
    },
  });
}

/**
 * 导出月度结算报表
 */
export function useExportMonthlySettlement() {
  return useMutation({
    mutationFn: (month?: string) => exportMonthlySettlement(month),
    onSuccess: (blob, month) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `月度结算_${month || new Date().toISOString().slice(0, 7)}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
}

// ========== Refresh Hooks ==========

/**
 * 刷新结算数据
 * SoT: D1-monthly-settlement.md 数据刷新策略
 *
 * @example
 * ```tsx
 * const { refreshAll, refreshList, refreshStatistics, refreshMonthly } = useRefreshSettlements();
 * // 刷新所有结算数据
 * refreshAll();
 * // 仅刷新列表
 * refreshList();
 * // 仅刷新统计
 * refreshStatistics();
 * // 仅刷新月度结算
 * refreshMonthly();
 * ```
 */
export function useRefreshSettlements() {
  const queryClient = useQueryClient();

  return {
    /** 刷新所有结算数据 */
    refreshAll: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.all });
      queryClient.invalidateQueries({ queryKey: ['monthlySettlements'] });
    },
    /** 刷新通用结算列表 */
    refreshList: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.lists() });
    },
    /** 刷新结算统计 */
    refreshStatistics: () => {
      queryClient.invalidateQueries({ queryKey: ['settlements', 'statistics'] });
    },
    /** 刷新逾期结算 */
    refreshOverdue: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.overdue() });
    },
    /** 刷新单个结算详情 */
    refreshDetail: (id: number) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settlements.detail(id) });
    },
    /** 刷新月度结算数据 */
    refreshMonthly: () => {
      queryClient.invalidateQueries({ queryKey: ['monthlySettlements'] });
    },
    /** 刷新月度结算汇总 */
    refreshMonthlySummary: (month?: string) => {
      queryClient.invalidateQueries({ queryKey: ['monthlySettlements', 'summary', month] });
    },
  };
}
