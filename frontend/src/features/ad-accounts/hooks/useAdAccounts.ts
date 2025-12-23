/**
 * Ad Accounts React Query Hooks
 *
 * TanStack Query v5 hooks for ad account management
 * SoT 对齐: DATA_SCHEMA.md v5.2
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import {
  getAdAccounts,
  getAdAccount,
  createAdAccount,
  updateAdAccountStatus,
  deleteAdAccount,
} from '../services';
import type {
  AdAccount,
  AdAccountListParams,
  AdAccountCreateInput,
  AdAccountStatusUpdateInput,
} from '../types';

// ========== Query Hooks ==========

export function useAdAccounts(
  params: AdAccountListParams = {},
  options?: Omit<UseQueryOptions<{
    items: AdAccount[];
    meta: { pagination: { page: number; page_size: number; total: number; total_pages: number } };
  }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.adAccounts.list(params as Record<string, unknown>),
    queryFn: () => getAdAccounts(params),
    ...options,
  });
}

export function useAdAccount(
  id: string,
  options?: Omit<UseQueryOptions<{ data: AdAccount }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.adAccounts.detail(id),
    queryFn: () => getAdAccount(id),
    enabled: !!id,
    ...options,
  });
}

// ========== Mutation Hooks ==========

export function useCreateAdAccount(
  options?: UseMutationOptions<{ data: AdAccount }, Error, AdAccountCreateInput>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createAdAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adAccounts.all });
    },
    ...options,
  });
}

export function useUpdateAdAccountStatus(
  options?: UseMutationOptions<{ data: AdAccount }, Error, { id: string; input: AdAccountStatusUpdateInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => updateAdAccountStatus(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adAccounts.all });
    },
    ...options,
  });
}

export function useDeleteAdAccount(
  options?: UseMutationOptions<void, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteAdAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adAccounts.all });
    },
    ...options,
  });
}
