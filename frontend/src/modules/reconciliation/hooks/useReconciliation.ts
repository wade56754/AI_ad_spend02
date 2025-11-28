/**
 * Reconciliation React Query Hooks
 *
 * TanStack Query v5 hooks for reconciliation management
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
  getReconciliations,
  getReconciliation,
  getReconciliationMismatches,
  getReconciliationsByProject,
  createReconciliation,
  runReconciliation,
  retryReconciliation,
  resolveMismatch,
  getReconciliationStats,
  getLatestReconciliation,
} from '../services';
import type {
  Reconciliation,
  ReconciliationListParams,
  ReconciliationCreateInput,
  ReconciliationMismatch,
  MismatchResolveInput,
  ReconciliationStatus,
  ReconciliationType,
} from '../types';

// === Query Hooks ===

/**
 * Fetch paginated reconciliations
 */
export function useReconciliations(
  params: ReconciliationListParams = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<Reconciliation>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.reconciliations.list(params),
    queryFn: () => getReconciliations(params),
    ...options,
  });
}

/**
 * Fetch single reconciliation
 */
export function useReconciliation(
  id: string,
  options?: Omit<UseQueryOptions<Reconciliation>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.reconciliations.detail(id),
    queryFn: () => getReconciliation(id),
    enabled: !!id,
    ...options,
  });
}

/**
 * Fetch reconciliation mismatches
 */
export function useReconciliationMismatches(
  reconciliationId: string,
  options?: Omit<UseQueryOptions<ReconciliationMismatch[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...queryKeys.reconciliations.detail(reconciliationId), 'mismatches'],
    queryFn: () => getReconciliationMismatches(reconciliationId),
    enabled: !!reconciliationId,
    ...options,
  });
}

/**
 * Fetch reconciliations by project
 */
export function useReconciliationsByProject(
  projectId: string,
  params: Omit<ReconciliationListParams, 'project_id'> = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<Reconciliation>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.reconciliations.byProject(projectId, params),
    queryFn: () => getReconciliationsByProject(projectId, params),
    enabled: !!projectId,
    ...options,
  });
}

/**
 * Fetch latest reconciliation for a project
 */
export function useLatestReconciliation(
  projectId: string,
  options?: Omit<UseQueryOptions<Reconciliation | null>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...queryKeys.reconciliations.all, 'latest', projectId],
    queryFn: () => getLatestReconciliation(projectId),
    enabled: !!projectId,
    ...options,
  });
}

/**
 * Fetch reconciliation statistics
 */
export function useReconciliationStats(
  params: { tenant_id?: string; project_id?: string; start_date?: string; end_date?: string } = {},
  options?: Omit<UseQueryOptions<{ by_status: Record<ReconciliationStatus, number>; by_type: Record<ReconciliationType, number>; total_discrepancy: number; threshold_exceeded_count: number; average_match_rate: number }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...queryKeys.reconciliations.all, 'stats', params],
    queryFn: () => getReconciliationStats(params),
    ...options,
  });
}

// === Mutation Hooks ===

/**
 * Create reconciliation mutation
 */
export function useCreateReconciliation(
  options?: UseMutationOptions<Reconciliation, Error, ReconciliationCreateInput>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createReconciliation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.reconciliations.all });
    },
    ...options,
  });
}

/**
 * Run reconciliation mutation
 */
export function useRunReconciliation(
  options?: UseMutationOptions<Reconciliation, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: runReconciliation,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.reconciliations.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.reconciliations.lists() });
    },
    ...options,
  });
}

/**
 * Retry reconciliation mutation
 */
export function useRetryReconciliation(
  options?: UseMutationOptions<Reconciliation, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: retryReconciliation,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.reconciliations.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.reconciliations.lists() });
    },
    ...options,
  });
}

/**
 * Resolve mismatch mutation
 */
export function useResolveMismatch(
  options?: UseMutationOptions<
    ReconciliationMismatch,
    Error,
    { reconciliationId: string; mismatchId: string; input: MismatchResolveInput }
  >
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ reconciliationId, mismatchId, input }) =>
      resolveMismatch(reconciliationId, mismatchId, input),
    onSuccess: (_, { reconciliationId }) => {
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.reconciliations.detail(reconciliationId), 'mismatches'],
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.reconciliations.detail(reconciliationId),
      });
    },
    ...options,
  });
}
