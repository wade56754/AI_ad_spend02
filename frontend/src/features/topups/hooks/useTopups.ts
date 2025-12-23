/**
 * Topups React Query Hooks
 *
 * TanStack Query v5 hooks for topup request management
 *
 * SoT: docs/10.module-specs/B1-topup-approval.md §5 API 接口
 * SoT: STATE_MACHINE.md v2.6 Section 3 (充值 7 状态机)
 * SoT: API_SOT.md v9.0 Section 5.6 (Topup endpoints)
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
  createTopup,
  reviewTopup,
  approveTopup,
  rejectTopup,
  completeTopup,
  cancelTopup,
  getTopupStats,
} from '../services';
import type {
  TopupRequest,
  TopupListParams,
  TopupCreateInput,
  TopupApproveInput,
  TopupRejectInput,
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
  options?: Omit<UseQueryOptions<{ by_status: Record<TopupStatus, number>; total_amount: number; pending_count: number }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...queryKeys.topups.all, 'stats', params],
    queryFn: () => getTopupStats(params),
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
 * Approve topup mutation
 */
export function useApproveTopup(
  options?: UseMutationOptions<TopupRequest, Error, { id: string; input?: TopupApproveInput }>
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
export function useCompleteTopup(
  options?: UseMutationOptions<TopupRequest, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: completeTopup,
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
export function useCancelTopup(
  options?: UseMutationOptions<TopupRequest, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelTopup,
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
 * SoT: STATE_MACHINE.md v2.6 Section 3
 */
export function useReviewTopup(
  options?: UseMutationOptions<TopupRequest, Error, { id: string; input?: TopupApproveInput }>
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
