/**
 * Reconciliation API Service
 *
 * Aligned with API_SOT.md v9.0 Section 5.8 (Reconciliation endpoints)
 */

import { apiFetch, apiFetchPaginated } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';
import type {
  Reconciliation,
  ReconciliationListParams,
  ReconciliationCreateInput,
  ReconciliationMismatch,
  MismatchResolveInput,
  ReconciliationStatus,
  ReconciliationType,
} from '../types';

const BASE_PATH = '/api/v1/reconciliations';

// === Query Functions ===

/**
 * Get paginated list of reconciliations
 * GET /api/v1/reconciliations
 */
export async function getReconciliations(
  params: ReconciliationListParams = {}
): Promise<PaginatedResponse<Reconciliation>> {
  const searchParams = new URLSearchParams();

  if (params.tenant_id) searchParams.set('tenant_id', params.tenant_id);
  if (params.project_id) searchParams.set('project_id', params.project_id);
  if (params.type) {
    const types = Array.isArray(params.type) ? params.type : [params.type];
    types.forEach((t) => searchParams.append('type', t));
  }
  if (params.status) {
    const statuses = Array.isArray(params.status) ? params.status : [params.status];
    statuses.forEach((s) => searchParams.append('status', s));
  }
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.threshold_exceeded !== undefined) {
    searchParams.set('threshold_exceeded', String(params.threshold_exceeded));
  }
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.sort_order) searchParams.set('sort_order', params.sort_order);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  return apiFetchPaginated<Reconciliation>(url);
}

/**
 * Get single reconciliation by ID
 * GET /api/v1/reconciliations/:id
 */
export async function getReconciliation(id: string): Promise<Reconciliation> {
  return apiFetch<Reconciliation>(`${BASE_PATH}/${id}`);
}

/**
 * Get reconciliation mismatches
 * GET /api/v1/reconciliations/:id/mismatches
 */
export async function getReconciliationMismatches(
  reconciliationId: string
): Promise<ReconciliationMismatch[]> {
  return apiFetch<ReconciliationMismatch[]>(`${BASE_PATH}/${reconciliationId}/mismatches`);
}

/**
 * Get reconciliations by project
 * GET /api/v1/projects/:projectId/reconciliations
 */
export async function getReconciliationsByProject(
  projectId: string,
  params: Omit<ReconciliationListParams, 'project_id'> = {}
): Promise<PaginatedResponse<Reconciliation>> {
  return getReconciliations({ ...params, project_id: projectId });
}

// === Mutation Functions ===

/**
 * Create new reconciliation
 * POST /api/v1/reconciliations
 */
export async function createReconciliation(
  input: ReconciliationCreateInput
): Promise<Reconciliation> {
  return apiFetch<Reconciliation>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
}

/**
 * Run reconciliation (start execution)
 * POST /api/v1/reconciliations/:id/run
 * pending → in_progress → completed | failed
 */
export async function runReconciliation(id: string): Promise<Reconciliation> {
  return apiFetch<Reconciliation>(`${BASE_PATH}/${id}/run`, {
    method: 'POST',
  });
}

/**
 * Retry failed reconciliation
 * POST /api/v1/reconciliations/:id/retry
 * failed → in_progress
 */
export async function retryReconciliation(id: string): Promise<Reconciliation> {
  return apiFetch<Reconciliation>(`${BASE_PATH}/${id}/retry`, {
    method: 'POST',
  });
}

/**
 * Resolve mismatch
 * POST /api/v1/reconciliations/:reconciliationId/mismatches/:mismatchId/resolve
 */
export async function resolveMismatch(
  reconciliationId: string,
  mismatchId: string,
  input: MismatchResolveInput
): Promise<ReconciliationMismatch> {
  return apiFetch<ReconciliationMismatch>(
    `${BASE_PATH}/${reconciliationId}/mismatches/${mismatchId}/resolve`,
    {
      method: 'POST',
      body: input,
    }
  );
}

// === Statistics ===

/**
 * Get reconciliation statistics
 * GET /api/v1/reconciliations/stats
 */
export async function getReconciliationStats(params: {
  tenant_id?: string;
  project_id?: string;
  start_date?: string;
  end_date?: string;
}): Promise<{
  by_status: Record<ReconciliationStatus, number>;
  by_type: Record<ReconciliationType, number>;
  total_discrepancy: number;
  threshold_exceeded_count: number;
  average_match_rate: number;
}> {
  const searchParams = new URLSearchParams();
  if (params.tenant_id) searchParams.set('tenant_id', params.tenant_id);
  if (params.project_id) searchParams.set('project_id', params.project_id);
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/stats?${query}` : `${BASE_PATH}/stats`;

  return apiFetch(url);
}

/**
 * Get latest reconciliation for a project
 * GET /api/v1/projects/:projectId/reconciliations/latest
 */
export async function getLatestReconciliation(
  projectId: string
): Promise<Reconciliation | null> {
  return apiFetch<Reconciliation | null>(`/api/v1/projects/${projectId}/reconciliations/latest`);
}
