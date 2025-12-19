/**
 * Transfers React Query Hooks
 *
 * TanStack Query v5 hooks for transfers module
 * SoT 对齐: STATE_MACHINE.md v2.6 第12章
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
  getTransfers,
  getTransfer,
  createTransfer,
  submitTransfer,
  approveTransfer,
  rejectTransfer,
  completeTransfer,
} from '../services';
import type {
  Transfer,
  TransferListParams,
  TransferCreateInput,
  TransferApproveInput,
  TransferRejectInput,
} from '../types';

// ========== Query Hooks ==========

/**
 * 获取迁移申请列表
 */
export function useTransfers(
  params: TransferListParams = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<Transfer>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.transfers.list(params as Record<string, any>),
    queryFn: () => getTransfers(params),
    ...options,
  });
}

/**
 * 获取迁移申请详情
 */
export function useTransfer(
  id: number,
  options?: Omit<UseQueryOptions<Transfer>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.transfers.detail(String(id)),
    queryFn: () => getTransfer(id),
    enabled: !!id,
    ...options,
  });
}

// ========== Mutation Hooks ==========

/**
 * 创建迁移申请
 */
export function useCreateTransfer(
  options?: UseMutationOptions<Transfer, Error, TransferCreateInput>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createTransfer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.transfers.all });
    },
    ...options,
  });
}

/**
 * 提交迁移申请
 * State transition: draft -> pending_review
 */
export function useSubmitTransfer(
  options?: UseMutationOptions<Transfer, Error, number>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: submitTransfer,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.transfers.detail(String(id)), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.transfers.lists() });
    },
    ...options,
  });
}

/**
 * 审批迁移申请
 * State transition: pending_review -> approved
 */
export function useApproveTransfer(
  options?: UseMutationOptions<Transfer, Error, { id: number; input: TransferApproveInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => approveTransfer(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.transfers.detail(String(id)), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.transfers.lists() });
    },
    ...options,
  });
}

/**
 * 拒绝迁移申请
 * State transition: pending_review -> rejected
 */
export function useRejectTransfer(
  options?: UseMutationOptions<Transfer, Error, { id: number; input: TransferRejectInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => rejectTransfer(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.transfers.detail(String(id)), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.transfers.lists() });
    },
    ...options,
  });
}

/**
 * 完成迁移
 * State transition: approved -> completed
 */
export function useCompleteTransfer(
  options?: UseMutationOptions<Transfer, Error, number>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: completeTransfer,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.transfers.detail(String(id)), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.transfers.lists() });
      // Also invalidate ledger queries since completion creates entries
      queryClient.invalidateQueries({ queryKey: queryKeys.ledger.all });
    },
    ...options,
  });
}
