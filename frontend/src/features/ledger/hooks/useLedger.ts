/**
 * Ledger React Query Hooks
 *
 * TanStack Query v5 hooks for ledger data (READ-ONLY)
 * CRITICAL: No mutation hooks - ledger entries are created only through
 * backend workflows, never directly from frontend
 */

import {
  useQuery,
  type UseQueryOptions,
} from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';
import {
  getLedgerEntries,
  getLedgerEntry,
  getTenantBalance,
  getProjectBalance,
  getTenantProjectBalances,
  getLedgerEntriesByReference,
  getLedgerStats,
  verifyBalanceIntegrity,
} from '../services';
import type {
  LedgerEntry,
  LedgerListParams,
  TenantBalance,
  ProjectBalance,
  LedgerEntryType,
} from '../types';

// === Query Hooks ===

/**
 * Fetch paginated ledger entries
 */
export function useLedgerEntries(
  params: LedgerListParams = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<LedgerEntry>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.ledger.list(params as Record<string, unknown>),
    queryFn: () => getLedgerEntries(params),
    ...options,
  });
}

/**
 * Fetch single ledger entry
 */
export function useLedgerEntry(
  id: string,
  options?: Omit<UseQueryOptions<LedgerEntry>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.ledger.detail(id),
    queryFn: () => getLedgerEntry(id),
    enabled: !!id,
    ...options,
  });
}

/**
 * Fetch tenant balance
 */
export function useTenantBalance(
  tenantId: string,
  options?: Omit<UseQueryOptions<TenantBalance>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.ledger.tenantBalance(tenantId),
    queryFn: () => getTenantBalance(tenantId),
    enabled: !!tenantId,
    ...options,
  });
}

/**
 * Fetch project balance
 */
export function useProjectBalance(
  projectId: string,
  options?: Omit<UseQueryOptions<ProjectBalance>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.ledger.projectBalance(projectId),
    queryFn: () => getProjectBalance(projectId),
    enabled: !!projectId,
    ...options,
  });
}

/**
 * Fetch all project balances for a tenant
 */
export function useTenantProjectBalances(
  tenantId: string,
  options?: Omit<UseQueryOptions<ProjectBalance[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...queryKeys.ledger.all, 'tenant-projects', tenantId],
    queryFn: () => getTenantProjectBalances(tenantId),
    enabled: !!tenantId,
    ...options,
  });
}

/**
 * Fetch ledger entries by reference document
 */
export function useLedgerEntriesByReference(
  referenceType: 'topup' | 'daily_report' | 'transfer' | 'manual',
  referenceId: string,
  options?: Omit<UseQueryOptions<LedgerEntry[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...queryKeys.ledger.all, 'by-reference', referenceType, referenceId],
    queryFn: () => getLedgerEntriesByReference(referenceType, referenceId),
    enabled: !!referenceType && !!referenceId,
    ...options,
  });
}

/**
 * Fetch ledger statistics
 */
export function useLedgerStats(
  params: { tenant_id?: string; project_id?: string; start_date?: string; end_date?: string } = {},
  options?: Omit<UseQueryOptions<{ by_type: Record<LedgerEntryType, { count: number; total_amount: number }>; total_entries: number; net_flow: number }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...queryKeys.ledger.all, 'stats', params],
    queryFn: () => getLedgerStats(params),
    ...options,
  });
}

/**
 * Verify balance integrity (admin only)
 */
export function useVerifyBalanceIntegrity(
  tenantId: string,
  options?: Omit<UseQueryOptions<{ is_valid: boolean; expected_balance: number; actual_balance: number; discrepancy: number; entries_count: number }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...queryKeys.ledger.all, 'verify', tenantId],
    queryFn: () => verifyBalanceIntegrity(tenantId),
    enabled: !!tenantId,
    // Don't auto-refetch verification - it's expensive
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}
