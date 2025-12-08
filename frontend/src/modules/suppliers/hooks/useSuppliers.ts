/**
 * Suppliers React Query Hooks
 *
 * TanStack Query v5 hooks for supplier management
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
import type { PaginatedResponse } from '@/lib/api';
import {
  getSuppliers,
  getSupplier,
  getSupplierStatistics,
  getSupplierAccounts,
  getSupplierLedgerSummary,
  createSupplier,
  updateSupplier,
  deleteSupplier,
  activateSupplier,
  deactivateSupplier,
  suspendSupplier,
} from '../services';
import type {
  Supplier,
  SupplierListParams,
  SupplierCreateInput,
  SupplierUpdateInput,
  SupplierStatistics,
  SupplierLedgerSummary,
  SupplierAccount,
} from '../types';

// ========== Query Hooks ==========

/**
 * Fetch paginated supplier list
 */
export function useSuppliers(
  params: SupplierListParams = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<Supplier>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.suppliers.list(params),
    queryFn: () => getSuppliers(params),
    ...options,
  });
}

/**
 * Fetch single supplier by ID
 */
export function useSupplier(
  id: number,
  options?: Omit<UseQueryOptions<Supplier>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.suppliers.detail(id),
    queryFn: () => getSupplier(id),
    enabled: !!id,
    ...options,
  });
}

/**
 * Fetch supplier statistics
 */
export function useSupplierStatistics(
  options?: Omit<UseQueryOptions<SupplierStatistics>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.suppliers.statistics(),
    queryFn: getSupplierStatistics,
    ...options,
  });
}

/**
 * Fetch supplier's related accounts
 */
export function useSupplierAccounts(
  supplierId: number,
  params: { page?: number; page_size?: number } = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<SupplierAccount>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.suppliers.accounts(supplierId),
    queryFn: () => getSupplierAccounts(supplierId, params),
    enabled: !!supplierId,
    ...options,
  });
}

/**
 * Fetch supplier's ledger summary
 */
export function useSupplierLedgerSummary(
  supplierId: number,
  options?: Omit<UseQueryOptions<SupplierLedgerSummary>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.suppliers.ledgerSummary(supplierId),
    queryFn: () => getSupplierLedgerSummary(supplierId),
    enabled: !!supplierId,
    ...options,
  });
}

// ========== Mutation Hooks ==========

/**
 * Create supplier mutation
 */
export function useCreateSupplier(
  options?: UseMutationOptions<Supplier, Error, SupplierCreateInput>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createSupplier,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.suppliers.all });
    },
    ...options,
  });
}

/**
 * Update supplier mutation
 */
export function useUpdateSupplier(
  options?: UseMutationOptions<Supplier, Error, { id: number; input: SupplierUpdateInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => updateSupplier(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.suppliers.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.suppliers.lists() });
    },
    ...options,
  });
}

/**
 * Delete supplier mutation
 */
export function useDeleteSupplier(
  options?: UseMutationOptions<void, Error, number>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteSupplier,
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: queryKeys.suppliers.detail(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.suppliers.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.suppliers.statistics() });
    },
    ...options,
  });
}

// ========== Status Action Hooks ==========

/**
 * Activate supplier mutation
 */
export function useActivateSupplier(
  options?: UseMutationOptions<Supplier, Error, number>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: activateSupplier,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.suppliers.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.suppliers.lists() });
    },
    ...options,
  });
}

/**
 * Deactivate supplier mutation
 */
export function useDeactivateSupplier(
  options?: UseMutationOptions<Supplier, Error, number>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deactivateSupplier,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.suppliers.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.suppliers.lists() });
    },
    ...options,
  });
}

/**
 * Suspend supplier mutation
 */
export function useSuspendSupplier(
  options?: UseMutationOptions<Supplier, Error, number>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: suspendSupplier,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.suppliers.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.suppliers.lists() });
    },
    ...options,
  });
}
