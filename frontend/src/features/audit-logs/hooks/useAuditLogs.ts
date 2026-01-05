/**
 * Audit Logs Hooks
 *
 * React Query hooks for audit logs data fetching
 */

import { useQuery } from '@tanstack/react-query';
import {
  getAuditLogs,
  getAuditLogById,
  getAuditLogStatistics,
  getAuditLogActions,
  getAuditLogResourceTypes,
} from '../services';
import type { AuditLogListParams } from '../types';

/**
 * Hook to fetch paginated audit logs
 */
export function useAuditLogs(params: AuditLogListParams = {}) {
  return useQuery({
    queryKey: ['audit-logs', params],
    queryFn: () => getAuditLogs(params),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook to fetch a single audit log by ID
 */
export function useAuditLog(id: number | undefined) {
  return useQuery({
    queryKey: ['audit-logs', id],
    queryFn: () => getAuditLogById(id!),
    enabled: !!id,
  });
}

/**
 * Hook to fetch audit log statistics
 */
export function useAuditLogStatistics() {
  return useQuery({
    queryKey: ['audit-logs', 'statistics'],
    queryFn: getAuditLogStatistics,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch available actions for filtering
 */
export function useAuditLogActions() {
  return useQuery({
    queryKey: ['audit-logs', 'actions'],
    queryFn: getAuditLogActions,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to fetch available resource types for filtering
 */
export function useAuditLogResourceTypes() {
  return useQuery({
    queryKey: ['audit-logs', 'resource-types'],
    queryFn: getAuditLogResourceTypes,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}
