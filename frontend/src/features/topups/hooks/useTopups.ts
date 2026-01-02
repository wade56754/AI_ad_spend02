/**
 * Topups React Query Hooks
 *
 * TanStack Query v5 hooks for topup request management
 *
 * SoT: API_SOT.md v9.7 Section 10 (Topup Requests API)
 * SoT: STATE_MACHINE.md v2.9 Section 9 (充值 7 状态机)
 *
 * 一句话定义: 管理充值申请的数据获取和状态变更
 *
 * @module features/topups/hooks
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
  getTopups,
  getTopup,
  getTopupsByProject,
  getTopupLogs,
  createTopup,
  submitTopup,
  reviewTopup,
  approveTopup,
  payTopup,
  confirmPaidTopup,
  rejectTopup,
  completeTopup,
  cancelTopup,
  uploadReceipt,
  getTopupStats,
  getTopupDashboard,
  getAccountBalance,
} from '../services';
import type {
  TopupRequest,
  TopupListParams,
  TopupCreateInput,
  TopupSubmitInput,
  TopupDataReviewInput,
  TopupFinanceApproveInput,
  TopupCompleteInput,
  TopupRejectInput,
  TopupCancelInput,
  TopupApprovalLog,
  TopupStatistics,
  TopupStatus,
} from '../types';

// ========== Query Hooks ==========

/**
 * Fetch paginated topup list
 */
export function useTopups(
  params: TopupListParams = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<TopupRequest>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.topups.list(params),
    queryFn: () => getTopups(params),
    ...options,
  });
}

/**
 * Fetch single topup by ID
 */
export function useTopup(
  id: string,
  options?: Omit<UseQueryOptions<TopupRequest>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.topups.detail(id),
    queryFn: () => getTopup(id),
    enabled: !!id,
    ...options,
  });
}

/**
 * Fetch topups by project
 */
export function useTopupsByProject(
  projectId: string,
  params: Omit<TopupListParams, 'project_id'> = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<TopupRequest>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.topups.byProject(projectId, params),
    queryFn: () => getTopupsByProject(projectId, params),
    enabled: !!projectId,
    ...options,
  });
}

/**
 * Fetch topup statistics
 */
export function useTopupStats(
  params: { project_id?: string; start_date?: string; end_date?: string } = {},
  options?: Omit<UseQueryOptions<TopupStatistics>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...queryKeys.topups.all, 'stats', params],
    queryFn: () => getTopupStats(params),
    ...options,
  });
}

/**
 * Fetch topup approval logs
 */
export function useTopupLogs(
  id: string,
  options?: Omit<UseQueryOptions<TopupApprovalLog[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...queryKeys.topups.detail(id), 'logs'],
    queryFn: () => getTopupLogs(id),
    enabled: !!id,
    ...options,
  });
}

/**
 * Fetch topup dashboard data
 */
export function useTopupDashboard(
  params: { project_id?: string; start_date?: string; end_date?: string } = {},
  options?: Omit<
    UseQueryOptions<{
      pending_count: number;
      today_amount: number;
      week_amount: number;
      month_amount: number;
      by_status: Record<TopupStatus, number>;
      recent_requests: TopupRequest[];
    }>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery({
    queryKey: [...queryKeys.topups.all, 'dashboard', params],
    queryFn: () => getTopupDashboard(params),
    ...options,
  });
}

/**
 * Fetch account balance
 */
export function useAccountBalance(
  accountId: string,
  options?: Omit<
    UseQueryOptions<{
      account_id: string;
      available_balance: number;
      pending_topups: number;
      total_topups: number;
      last_topup_at?: string;
    }>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery({
    queryKey: [...queryKeys.topups.all, 'accounts', accountId, 'balance'],
    queryFn: () => getAccountBalance(accountId),
    enabled: !!accountId,
    ...options,
  });
}

// === Mutation Hooks ===

/**
 * Create topup mutation
 */
export function useCreateTopup(
  options?: UseMutationOptions<TopupRequest, Error, TopupCreateInput>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createTopup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.topups.all });
    },
    ...options,
  });
}

/**
 * Approve topup mutation (财务终审通过)
 * finance_approve → paid
 * SoT: STATE_MACHINE.md v2.9 Section 9
 */
export function useApproveTopup(
  options?: UseMutationOptions<
    TopupRequest,
    Error,
    { id: string; input?: TopupFinanceApproveInput }
  >
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => approveTopup(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.topups.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.topups.lists() });
    },
    ...options,
  });
}

/**
 * Reject topup mutation
 */
export function useRejectTopup(
  options?: UseMutationOptions<TopupRequest, Error, { id: string; input: TopupRejectInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => rejectTopup(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.topups.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.topups.lists() });
    },
    ...options,
  });
}

/**
 * Complete topup mutation
 */
export function useCompleteTopup(options?: UseMutationOptions<TopupRequest, Error, string>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => completeTopup(id),
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.topups.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.topups.lists() });
      // Also invalidate ledger queries since completion creates an entry
      queryClient.invalidateQueries({ queryKey: queryKeys.ledger.all });
    },
    ...options,
  });
}

/**
 * 取消充值申请
 * draft | pending_review | finance_approve → cancelled
 * SoT: STATE_MACHINE.md v2.6 Section 3
 */
export function useCancelTopup(options?: UseMutationOptions<TopupRequest, Error, string>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => cancelTopup(id),
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.topups.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.topups.lists() });
    },
    ...options,
  });
}

/**
 * 数据复核通过
 * pending_review → finance_approve
 * SoT: STATE_MACHINE.md v2.9 Section 9
 */
export function useReviewTopup(
  options?: UseMutationOptions<TopupRequest, Error, { id: string; input?: TopupDataReviewInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => reviewTopup(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.topups.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.topups.lists() });
    },
    ...options,
  });
}

/**
 * 提交审批
 * draft → pending_review
 * SoT: STATE_MACHINE.md v2.9 Section 9
 */
export function useSubmitTopup(
  options?: UseMutationOptions<TopupRequest, Error, { id: string; input?: TopupSubmitInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => submitTopup(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.topups.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.topups.lists() });
    },
    ...options,
  });
}

/**
 * 记录付款信息
 * SoT: API_SOT.md v9.7 §10.1
 */
export function usePayTopup(
  options?: UseMutationOptions<
    TopupRequest,
    Error,
    { id: string; input: { payment_reference: string; paid_at?: string } }
  >
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => payTopup(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.topups.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.topups.lists() });
    },
    ...options,
  });
}

/**
 * 确认到账完成
 * paid → completed
 * SoT: STATE_MACHINE.md v2.9 Section 9
 */
export function useConfirmPaidTopup(
  options?: UseMutationOptions<TopupRequest, Error, { id: string; input?: TopupCompleteInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => confirmPaidTopup(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.topups.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.topups.lists() });
      // Also invalidate ledger queries since completion creates an entry
      queryClient.invalidateQueries({ queryKey: queryKeys.ledger.all });
    },
    ...options,
  });
}

/**
 * 上传付款凭证
 * SoT: API_SOT.md v9.7 §10.1
 */
export function useUploadReceipt(
  options?: UseMutationOptions<{ url: string }, Error, { id: string; file: File }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, file }) => uploadReceipt(id, file),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.topups.detail(id) });
    },
    ...options,
  });
}

// ========== Refresh Hook ==========

/**
 * 刷新充值申请数据
 * SoT: B1-topup-approval.md §2.4 数据刷新策略
 *
 * @example
 * ```tsx
 * const { refreshAll, refreshList, refreshStats } = useRefreshTopups();
 * // 刷新所有充值数据
 * refreshAll();
 * // 仅刷新列表
 * refreshList();
 * ```
 */
export function useRefreshTopups() {
  const queryClient = useQueryClient();

  return {
    /** 刷新所有充值数据 */
    refreshAll: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.topups.all });
    },
    /** 刷新充值列表 */
    refreshList: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.topups.lists() });
    },
    /** 刷新充值统计 */
    refreshStats: () => {
      queryClient.invalidateQueries({ queryKey: [...queryKeys.topups.all, 'stats'] });
    },
    /** 刷新单个充值详情 */
    refreshDetail: (id: string) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.topups.detail(id) });
    },
    /** 刷新项目充值列表 */
    refreshByProject: (projectId: string) => {
      queryClient.invalidateQueries({ queryKey: ['topups', 'byProject', projectId] });
    },
  };
}
