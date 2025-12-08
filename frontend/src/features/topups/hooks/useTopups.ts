/**
 * Topups React Query Hooks
 *
 * TanStack Query v5 hooks for topup requests
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

// === Query Hooks ===

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
 * Cancel topup mutation
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
