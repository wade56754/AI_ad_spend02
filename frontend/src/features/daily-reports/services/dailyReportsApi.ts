/**
 * Daily Reports API Service
 *
 * SoT: docs/10.module-specs/B2-daily-report-review.md §5 API 接口
 * SoT: STATE_MACHINE.md v2.6 Section 8 (日报 8 状态机)
 * SoT: API_SOT.md v9.0 Section 5.4 (Daily Reports endpoints)
 *
 * 一句话定义: 管理日报的创建、审核、确认、锁定流程
 *
 * 日报 8 状态机:
 *   raw_submitted → trend_pending → trend_ok/trend_flagged
 *   → trend_resolved → final_pending → final_confirmed → final_locked
 *
 * 使用真实后端 API 获取数据
 *
 * @module features/daily-reports/services
 */

import { apiFetch, apiFetchPaginated, apiDownload } from '@/lib/api';
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

// ========== Query Functions ==========

/**
 * 获取日报列表
 * GET /api/v1/daily-reports
 * SoT: B2-daily-report-review.md §5.1
 */
export async function getDailyReports(
  params: DailyReportListParams = {}
): Promise<PaginatedResponse<DailyReport>> {
  const searchParams = new URLSearchParams();
  if (params.project_id) searchParams.set('project_id', String(params.project_id));
  if (params.ad_account_id) searchParams.set('ad_account_id', String(params.ad_account_id));
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
  if (params.region) searchParams.set('region', params.region);
  if (params.platform) searchParams.set('platform', params.platform);
  if (params.team_id) searchParams.set('team_id', params.team_id);
  if (params.submitter_name) searchParams.set('submitter_name', params.submitter_name);
  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  // 使用 apiFetchPaginated 正确处理分页响应格式
  // 后端返回: { success, data: [...items], meta: { pagination: {...} } }
  return apiFetchPaginated<DailyReport>(url);
}

/**
 * 获取单个日报详情
 * GET /api/v1/daily-reports/:id
 * SoT: B2-daily-report-review.md §5.1
 */
export async function getDailyReport(id: string): Promise<DailyReport> {
  // apiFetch 自动解包 envelope，返回 data 部分
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}`);
}

/**
 * 按项目获取日报列表
 * GET /api/v1/projects/:projectId/daily-reports
 * SoT: B2-daily-report-review.md §5.1
 */
export async function getDailyReportsByProject(
  projectId: string | number,
  params: Omit<DailyReportListParams, 'project_id'> = {}
): Promise<PaginatedResponse<DailyReport>> {
  return getDailyReports({ ...params, project_id: Number(projectId) });
}

// ========== Mutation Functions ==========

/**
 * 创建日报
 * POST /api/v1/daily-reports
 * SoT: B2-daily-report-review.md §5.1
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
 * 更新日报 (仅 raw_submitted 状态可更新)
 * PATCH /api/v1/daily-reports/:id
 * SoT: B2-daily-report-review.md §5.1
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
 * 删除日报 (仅 raw_submitted 状态可删除)
 * DELETE /api/v1/daily-reports/:id
 * SoT: B2-daily-report-review.md §5.1
 */
export async function deleteDailyReport(id: string): Promise<void> {
  return apiFetch<void>(`${BASE_PATH}/${id}`, {
    method: 'DELETE',
  });
}

// ========== State Transition Functions ==========
// SoT: STATE_MACHINE.md v2.6 Section 8 (日报 8 状态机)

/**
 * 提交趋势审核
 * POST /api/v1/daily-reports/:id/submit-trend
 * raw_submitted → trend_pending
 */
export async function submitForTrend(id: string): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/submit-trend`, {
    method: 'POST',
  });
}

/**
 * 趋势通过
 * POST /api/v1/daily-reports/:id/approve-trend
 * trend_pending → trend_ok
 */
export async function approveTrend(id: string): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/approve-trend`, {
    method: 'POST',
  });
}

/**
 * 标记异常
 * POST /api/v1/daily-reports/:id/flag-trend
 * trend_pending → trend_flagged
 * SoT: B2-daily-report-review.md §3.5 趋势风控规则 (TF-001/002/003)
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
 * 处理异常
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
 * 提交终审
 * POST /api/v1/daily-reports/:id/submit-final
 * trend_ok | trend_resolved → final_pending
 */
export async function submitForFinal(id: string): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/submit-final`, {
    method: 'POST',
  });
}

/**
 * 终审确认
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
 * 锁定入账
 * POST /api/v1/daily-reports/:id/lock
 * final_confirmed → final_locked
 * SoT: LEDGER_SOT.md v1.1 (账本记录规则)
 */
export async function lockReport(id: string): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/lock`, {
    method: 'POST',
  });
}

// ========== Bulk Operations ==========

/**
 * 批量提交趋势审核
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

// ========== Statistics ==========

/**
 * 获取日报状态统计
 * GET /api/v1/daily-reports/stats
 * SoT: B2-daily-report-review.md §5.1
 */
export async function getDailyReportStats(params: {
  project_id?: string;
  start_date?: string;
  end_date?: string;
} = {}): Promise<Record<DailyReportStatus, number>> {
  const searchParams = new URLSearchParams();
  if (params.project_id) searchParams.set('project_id', params.project_id);
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/stats?${query}` : `${BASE_PATH}/stats`;

  // apiFetch 自动解包 envelope，返回 data 部分
  return apiFetch<Record<DailyReportStatus, number>>(url);
}
