/**
 * Topups API Service
 *
 * SoT: API_SOT.md v9.7 Section 10 (Topup Requests API)
 * SoT: STATE_MACHINE.md v2.9 Section 9 (充值 7 状态机)
 *
 * 一句话定义: 管理充值申请的创建、审批、支付、完成流程
 *
 * @module features/topups/services
 */

import { apiFetch, apiFetchPaginated, apiDownload, apiUpload } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';
import type {
  TopupRequest,
  TopupListParams,
  TopupCreateInput,
  TopupSubmitInput,
  TopupDataReviewInput,
  TopupFinanceApproveInput,
  TopupCompleteInput,
  TopupRejectInput,
  TopupCancelInput,
  TopupApprovalLog,
  TopupStatistics,
  TopupStatus,
} from '../types';

const BASE_PATH = '/api/v1/topups';

// ========== Query Functions ==========

/**
 * 获取充值申请列表
 * GET /api/v1/topups
 * SoT: API_SOT.md v9.7 §10.1
 */
export async function getTopups(
  params: TopupListParams = {}
): Promise<PaginatedResponse<TopupRequest>> {
  const searchParams = new URLSearchParams();

  if (params.tenant_id) searchParams.set('tenant_id', params.tenant_id);
  if (params.project_id) searchParams.set('project_id', params.project_id);
  if (params.ad_account_id) searchParams.set('ad_account_id', params.ad_account_id);
  if (params.requested_by) searchParams.set('requested_by', params.requested_by);

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
 * 获取单个充值申请详情
 * GET /api/v1/topups/{request_id}
 * SoT: API_SOT.md v9.7 §10.1
 */
export async function getTopup(id: string): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}`);
}

/**
 * 按项目获取充值申请列表
 * GET /api/v1/topups?project_id={projectId}
 * SoT: API_SOT.md v9.7 §10.1
 */
export async function getTopupsByProject(
  projectId: string,
  params: Omit<TopupListParams, 'project_id'> = {}
): Promise<PaginatedResponse<TopupRequest>> {
  return getTopups({ ...params, project_id: projectId });
}

/**
 * 获取充值审批日志
 * GET /api/v1/topups/{request_id}/logs
 * SoT: API_SOT.md v9.7 §10.1
 */
export async function getTopupLogs(id: string): Promise<TopupApprovalLog[]> {
  return apiFetch<TopupApprovalLog[]>(`${BASE_PATH}/${id}/logs`);
}

// ========== Mutation Functions ==========

/**
 * 创建充值申请
 * POST /api/v1/topups
 * 初始状态: draft
 * SoT: API_SOT.md v9.7 §10.2
 */
export async function createTopup(input: TopupCreateInput): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
}

/**
 * 提交审批
 * POST /api/v1/topups/{request_id}/submit
 * draft → pending_review
 * SoT: STATE_MACHINE.md v2.9 Section 9
 */
export async function submitTopup(id: string, input?: TopupSubmitInput): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/submit`, {
    method: 'POST',
    body: input ?? {},
  });
}

/**
 * 数据复核通过
 * POST /api/v1/topups/{request_id}/review
 * pending_review → finance_approve
 * SoT: STATE_MACHINE.md v2.9 Section 9
 */
export async function reviewTopup(id: string, input?: TopupDataReviewInput): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/review`, {
    method: 'POST',
    body: input ?? {},
  });
}

/**
 * 财务终审通过
 * POST /api/v1/topups/{request_id}/approve
 * finance_approve → paid
 * SoT: STATE_MACHINE.md v2.9 Section 9
 */
export async function approveTopup(
  id: string,
  input?: TopupFinanceApproveInput
): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/approve`, {
    method: 'POST',
    body: input ?? {},
  });
}

/**
 * 记录付款信息
 * PUT /api/v1/topups/{request_id}/pay
 * SoT: API_SOT.md v9.7 §10.1
 */
export async function payTopup(
  id: string,
  input: { payment_reference: string; paid_at?: string }
): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/pay`, {
    method: 'PUT',
    body: input,
  });
}

/**
 * 确认到账完成
 * POST /api/v1/topups/{request_id}/confirm-paid
 * paid → completed (创建 ledger_entry)
 * SoT: STATE_MACHINE.md v2.9 Section 9
 * SoT: LEDGER_SOT.md v1.1 (账本记录规则)
 */
export async function confirmPaidTopup(
  id: string,
  input?: TopupCompleteInput
): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/confirm-paid`, {
    method: 'POST',
    body: input ?? {},
  });
}

/**
 * 确认到账完成 (别名，保持向后兼容)
 * POST /api/v1/topups/{request_id}/confirm-paid
 */
export async function completeTopup(id: string, input?: TopupCompleteInput): Promise<TopupRequest> {
  return confirmPaidTopup(id, input);
}

/**
 * 拒绝充值申请
 * POST /api/v1/topups/{request_id}/reject
 * pending_review | finance_approve → rejected
 * SoT: STATE_MACHINE.md v2.9 Section 9
 */
export async function rejectTopup(id: string, input: TopupRejectInput): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/reject`, {
    method: 'POST',
    body: input,
  });
}

/**
 * 取消充值申请
 * POST /api/v1/topups/{request_id}/cancel
 * draft | pending_review | finance_approve → cancelled
 * SoT: STATE_MACHINE.md v2.9 Section 9
 */
export async function cancelTopup(id: string, input?: TopupCancelInput): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/cancel`, {
    method: 'POST',
    body: input ?? {},
  });
}

/**
 * 上传付款凭证
 * POST /api/v1/topups/{request_id}/receipt
 * SoT: API_SOT.md v9.7 §10.1
 */
export async function uploadReceipt(id: string, file: File): Promise<{ url: string }> {
  return apiUpload<{ url: string }>(`${BASE_PATH}/${id}/receipt`, file, {
    fieldName: 'file',
  });
}

// ========== Statistics & Dashboard ==========

/**
 * 获取充值统计数据
 * GET /api/v1/topups/statistics
 * SoT: API_SOT.md v9.7 §10.1
 */
export async function getTopupStats(
  params: {
    project_id?: string;
    start_date?: string;
    end_date?: string;
  } = {}
): Promise<TopupStatistics> {
  const searchParams = new URLSearchParams();

  if (params.project_id) searchParams.set('project_id', params.project_id);
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/statistics?${query}` : `${BASE_PATH}/statistics`;

  return apiFetch<TopupStatistics>(url);
}

/**
 * 获取充值仪表盘数据
 * GET /api/v1/topups/dashboard
 * SoT: API_SOT.md v9.7 §10.1
 */
export async function getTopupDashboard(
  params: {
    project_id?: string;
    start_date?: string;
    end_date?: string;
  } = {}
): Promise<{
  pending_count: number;
  today_amount: number;
  week_amount: number;
  month_amount: number;
  by_status: Record<TopupStatus, number>;
  recent_requests: TopupRequest[];
}> {
  const searchParams = new URLSearchParams();

  if (params.project_id) searchParams.set('project_id', params.project_id);
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/dashboard?${query}` : `${BASE_PATH}/dashboard`;

  return apiFetch(url);
}

/**
 * 获取账户余额
 * GET /api/v1/topups/accounts/{account_id}/balance
 * SoT: API_SOT.md v9.7 §10.1
 */
export async function getAccountBalance(accountId: string): Promise<{
  account_id: string;
  available_balance: number;
  pending_topups: number;
  total_topups: number;
  last_topup_at?: string;
}> {
  return apiFetch(`${BASE_PATH}/accounts/${accountId}/balance`);
}

/**
 * 导出充值数据
 * GET /api/v1/topups/export
 * SoT: API_SOT.md v9.7 §10.1
 */
export async function exportTopups(
  params: {
    project_id?: string;
    status?: TopupStatus | TopupStatus[];
    start_date?: string;
    end_date?: string;
    format?: 'csv' | 'xlsx';
  } = {}
): Promise<Blob> {
  const searchParams = new URLSearchParams();

  if (params.project_id) searchParams.set('project_id', params.project_id);
  if (params.status) {
    const statuses = Array.isArray(params.status) ? params.status : [params.status];
    statuses.forEach((s) => searchParams.append('status', s));
  }
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.format) searchParams.set('format', params.format);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/export?${query}` : `${BASE_PATH}/export`;

  return apiDownload(url);
}
