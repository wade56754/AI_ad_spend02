/**
 * Topups API Service
 *
 * Aligned with API_SOT.md v9.0 Section 5.6 (Topup endpoints)
 */

import { apiFetch, apiFetchPaginated } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';
import type {
  TopupRequest,
  TopupListParams,
  TopupCreateInput,
  TopupApproveInput,
  TopupRejectInput,
  TopupStatus,
} from '../types';

const BASE_PATH = '/api/v1/topups';

// === Query Functions ===

/**
 * Get paginated list of topup requests
 * GET /api/v1/topups
 */
export async function getTopups(
  params: TopupListParams = {}
): Promise<PaginatedResponse<TopupRequest>> {
  const searchParams = new URLSearchParams();

  if (params.tenant_id) searchParams.set('tenant_id', params.tenant_id);
  if (params.project_id) searchParams.set('project_id', params.project_id);
  if (params.status) {
    const statuses = Array.isArray(params.status) ? params.status : [params.status];
    statuses.forEach((s) => searchParams.append('status', s));
  }
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.min_amount) searchParams.set('min_amount', String(params.min_amount));
  if (params.max_amount) searchParams.set('max_amount', String(params.max_amount));
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.sort_order) searchParams.set('sort_order', params.sort_order);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  return apiFetchPaginated<TopupRequest>(url);
}

/**
 * Get single topup request by ID
 * GET /api/v1/topups/:id
 */
export async function getTopup(id: string): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}`);
}

/**
 * Get topup requests by project
 * GET /api/v1/projects/:projectId/topups
 */
export async function getTopupsByProject(
  projectId: string,
  params: Omit<TopupListParams, 'project_id'> = {}
): Promise<PaginatedResponse<TopupRequest>> {
  return getTopups({ ...params, project_id: projectId });
}

// === Mutation Functions ===

/**
 * Create new topup request
 * POST /api/v1/topups
 */
export async function createTopup(
  input: TopupCreateInput
): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
}

/**
 * Approve topup request
 * POST /api/v1/topups/:id/approve
 * pending → approved
 */
export async function approveTopup(
  id: string,
  input?: TopupApproveInput
): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/approve`, {
    method: 'POST',
    body: input ?? {},
  });
}

/**
 * Reject topup request
 * POST /api/v1/topups/:id/reject
 * pending → rejected
 */
export async function rejectTopup(
  id: string,
  input: TopupRejectInput
): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/reject`, {
    method: 'POST',
    body: input,
  });
}

/**
 * Complete topup (creates ledger entry)
 * POST /api/v1/topups/:id/complete
 * approved → completed
 */
export async function completeTopup(id: string): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/complete`, {
    method: 'POST',
  });
}

/**
 * Cancel topup request
 * POST /api/v1/topups/:id/cancel
 * pending | approved → cancelled
 */
export async function cancelTopup(id: string): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/cancel`, {
    method: 'POST',
  });
}

// === Statistics ===

/**
 * Get topup statistics
 * GET /api/v1/topups/stats
 */
export async function getTopupStats(params: {
  project_id?: string;
  start_date?: string;
  end_date?: string;
}): Promise<{
  by_status: Record<TopupStatus, number>;
  total_amount: number;
  pending_count: number;
}> {
  const searchParams = new URLSearchParams();
  if (params.project_id) searchParams.set('project_id', params.project_id);
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/stats?${query}` : `${BASE_PATH}/stats`;

  return apiFetch(url);
}
