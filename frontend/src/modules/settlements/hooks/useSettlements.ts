/**
 * Settlements React Query Hooks
 *
 * TanStack Query v5 hooks for settlement management
 * SoT 对齐: DATA_SCHEMA.md v5.2, LEDGER_SOT.md v1.1
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
