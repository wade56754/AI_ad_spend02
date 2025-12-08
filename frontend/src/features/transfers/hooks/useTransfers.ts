/**
 * Transfers Hooks
 *
 * TanStack Query v5 hooks for transfers module
 * SoT 对齐: STATE_MACHINE.md v2.6 第12章
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
  TransferListParams,
  TransferCreateInput,
  TransferApproveInput,
  TransferRejectInput,
} from '../types';

/** Query Keys */
export const transfersKeys = {
  all: ['transfers'] as const,
  lists: () => [...transfersKeys.all, 'list'] as const,
  list: (params?: TransferListParams) => [...transfersKeys.lists(), params] as const,
  details: () => [...transfersKeys.all, 'detail'] as const,
  detail: (id: number) => [...transfersKeys.details(), id] as const,
};

/** 获取迁移申请列表 */
export function useTransfers(params?: TransferListParams) {
  return useQuery({
    queryKey: transfersKeys.list(params),
    queryFn: () => getTransfers(params),
  });
}

/** 获取迁移申请详情 */
export function useTransfer(id: number) {
  return useQuery({
    queryKey: transfersKeys.detail(id),
    queryFn: () => getTransfer(id),
    enabled: !!id,
  });
}

/** 创建迁移申请 */
export function useCreateTransfer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: TransferCreateInput) => createTransfer(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: transfersKeys.lists() });
    },
  });
}

/** 提交迁移申请 */
export function useSubmitTransfer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => submitTransfer(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: transfersKeys.lists() });
      queryClient.invalidateQueries({ queryKey: transfersKeys.detail(id) });
    },
  });
}

/** 审批迁移申请 */
export function useApproveTransfer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: TransferApproveInput }) =>
      approveTransfer(id, input),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: transfersKeys.lists() });
      queryClient.invalidateQueries({ queryKey: transfersKeys.detail(id) });
    },
  });
}

/** 拒绝迁移申请 */
export function useRejectTransfer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: TransferRejectInput }) =>
      rejectTransfer(id, input),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: transfersKeys.lists() });
      queryClient.invalidateQueries({ queryKey: transfersKeys.detail(id) });
    },
  });
}

/** 完成迁移 */
export function useCompleteTransfer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => completeTransfer(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: transfersKeys.lists() });
      queryClient.invalidateQueries({ queryKey: transfersKeys.detail(id) });
    },
  });
}
