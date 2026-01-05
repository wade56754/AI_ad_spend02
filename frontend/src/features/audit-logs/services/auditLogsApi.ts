/**
 * Audit Logs API Service
 *
 * SoT: API_SOT.md v9.0 Section 5.9 (Audit Logs endpoints)
 */

import { apiGet } from '@/lib/api';
import type { AuditLog, AuditLogListParams, AuditLogStatistics } from '../types';
import type { PaginatedResponse } from '@/types';

const BASE_PATH = '/api/v1/audit-logs';

/**
 * Get paginated audit logs list
 */
export async function getAuditLogs(
  params: AuditLogListParams = {}
): Promise<PaginatedResponse<AuditLog>> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.user_id) searchParams.set('user_id', params.user_id);
  if (params.action) searchParams.set('action', params.action);
  if (params.resource_type) searchParams.set('resource_type', params.resource_type);
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  return apiGet<PaginatedResponse<AuditLog>>(`${BASE_PATH}?${query}`);
}

/**
 * Get audit log by ID
 */
export async function getAuditLogById(id: number): Promise<AuditLog> {
  return apiGet<AuditLog>(`${BASE_PATH}/${id}`);
}

/**
 * Get audit log statistics
 */
export async function getAuditLogStatistics(): Promise<AuditLogStatistics> {
  return apiGet<AuditLogStatistics>(`${BASE_PATH}/statistics`);
}

/**
 * Get available actions for filtering
 */
export async function getAuditLogActions(): Promise<string[]> {
  return apiGet<string[]>(`${BASE_PATH}/actions`);
}

/**
 * Get available resource types for filtering
 */
export async function getAuditLogResourceTypes(): Promise<string[]> {
  return apiGet<string[]>(`${BASE_PATH}/resource-types`);
}
