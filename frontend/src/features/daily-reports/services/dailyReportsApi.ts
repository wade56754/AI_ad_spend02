/**
 * Daily Reports API Service
 *
 * Aligned with API_SOT.md v9.0 Section 5.4 (Daily Reports endpoints)
 */

import { apiFetch, apiFetchPaginated } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';
import type {
  DailyReport,
  DailyReportListParams,
  DailyReportCreateInput,
  DailyReportUpdateInput,
  TrendResolveInput,
  FinalConfirmInput,
  DailyReportStatus,
} from '../types';

const BASE_PATH = '/api/v1/daily-reports';

// === Query Functions ===

/**
 * Get paginated list of daily reports
 * GET /api/v1/daily-reports
 */
export async function getDailyReports(
  params: DailyReportListParams = {}
): Promise<PaginatedResponse<DailyReport>> {
  const searchParams = new URLSearchParams();

  if (params.project_id) searchParams.set('project_id', params.project_id);
  if (params.status) {
    const statuses = Array.isArray(params.status) ? params.status : [params.status];
    statuses.forEach((s) => searchParams.append('status', s));
  }
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.search) searchParams.set('search', params.search);
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.sort_order) searchParams.set('sort_order', params.sort_order);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  return apiFetchPaginated<DailyReport>(url);
}

/**
 * Get single daily report by ID
 * GET /api/v1/daily-reports/:id
 */
export async function getDailyReport(id: string): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}`);
}

/**
 * Get daily reports by project
 * GET /api/v1/projects/:projectId/daily-reports
 */
export async function getDailyReportsByProject(
  projectId: string,
  params: Omit<DailyReportListParams, 'project_id'> = {}
): Promise<PaginatedResponse<DailyReport>> {
  return getDailyReports({ ...params, project_id: projectId });
}

// === Mutation Functions ===

/**
 * Create new daily report
 * POST /api/v1/daily-reports
 */
export async function createDailyReport(
  input: DailyReportCreateInput
): Promise<DailyReport> {
  return apiFetch<DailyReport>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
}

/**
 * Update daily report (only in raw_submitted status)
 * PATCH /api/v1/daily-reports/:id
 */
export async function updateDailyReport(
  id: string,
  input: DailyReportUpdateInput
): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}`, {
    method: 'PATCH',
    body: input,
  });
}

/**
 * Delete daily report (only in raw_submitted status)
 * DELETE /api/v1/daily-reports/:id
 */
export async function deleteDailyReport(id: string): Promise<void> {
  return apiFetch<void>(`${BASE_PATH}/${id}`, {
    method: 'DELETE',
  });
}

// === State Transition Functions ===

/**
 * Submit for trend analysis
 * POST /api/v1/daily-reports/:id/submit-trend
 * raw_submitted → trend_pending
 */
export async function submitForTrend(id: string): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/submit-trend`, {
    method: 'POST',
  });
}

/**
 * Approve trend (mark as OK)
 * POST /api/v1/daily-reports/:id/approve-trend
 * trend_pending → trend_ok
 */
export async function approveTrend(id: string): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/approve-trend`, {
    method: 'POST',
  });
}

/**
 * Flag trend anomaly
 * POST /api/v1/daily-reports/:id/flag-trend
 * trend_pending → trend_flagged
 */
export async function flagTrend(
  id: string,
  notes: string
): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/flag-trend`, {
    method: 'POST',
    body: { trend_notes: notes },
  });
}

/**
 * Resolve trend flag
 * POST /api/v1/daily-reports/:id/resolve-flag
 * trend_flagged → trend_resolved
 */
export async function resolveFlag(
  id: string,
  input: TrendResolveInput
): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/resolve-flag`, {
    method: 'POST',
    body: input,
  });
}

/**
 * Submit for final confirmation
 * POST /api/v1/daily-reports/:id/submit-final
 * trend_ok | trend_resolved → final_pending
 */
export async function submitForFinal(id: string): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/submit-final`, {
    method: 'POST',
  });
}

/**
 * Confirm final data
 * POST /api/v1/daily-reports/:id/confirm-final
 * final_pending → final_confirmed
 */
export async function confirmFinal(
  id: string,
  input: FinalConfirmInput
): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/confirm-final`, {
    method: 'POST',
    body: input,
  });
}

/**
 * Lock report (immutable)
 * POST /api/v1/daily-reports/:id/lock
 * final_confirmed → final_locked
 */
export async function lockReport(id: string): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/lock`, {
    method: 'POST',
  });
}

// === Bulk Operations ===

/**
 * Bulk submit for trend
 * POST /api/v1/daily-reports/bulk/submit-trend
 */
export async function bulkSubmitForTrend(ids: string[]): Promise<{
  success: string[];
  failed: { id: string; error: string }[];
}> {
  return apiFetch(`${BASE_PATH}/bulk/submit-trend`, {
    method: 'POST',
    body: { ids },
  });
}

/**
 * Get status statistics
 * GET /api/v1/daily-reports/stats
 */
export async function getDailyReportStats(params: {
  project_id?: string;
  start_date?: string;
  end_date?: string;
}): Promise<Record<DailyReportStatus, number>> {
  const searchParams = new URLSearchParams();
  if (params.project_id) searchParams.set('project_id', params.project_id);
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/stats?${query}` : `${BASE_PATH}/stats`;

  return apiFetch(url);
}
