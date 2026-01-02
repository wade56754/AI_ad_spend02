/**
 * Settlements API Service
 *
 * TanStack Query v5 API 服务层
 *
 * SoT: docs/10.module-specs/D1-monthly-settlement.md §4 API 接口
 * SoT: API_SOT.md v9.0 (API conventions)
 * SoT: LEDGER_SOT.md v1.1 (ledger integration)
 *
 * 一句话定义: 结算管理 API 服务 (通用结算 + 月度项目结算)
 *
 * 月度结算状态机 (D1-monthly-settlement.md §2.4):
 *   pending → draft → confirmed → locked (终态)
 *
 * Phase 约束 (D1-monthly-settlement.md §1.4):
 * - Phase 1: 结算可修改，用于观察
 * - Phase 2: 锁定后不可修改
 *
 * Author: AI 代码工厂 v2.4
 */

import { apiFetch, apiFetchPaginated, apiDownload } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';
import type {
  Settlement,
  SettlementListParams,
  SettlementCreateInput,
  SettlementUpdateInput,
  SettlementApproveInput,
  SettlementPaymentInput,
  SettlementStatistics,
  SettlementPayment,
  MonthlySettlement,
  MonthlySettlementListParams,
  MonthlySettlementListResponse,
  MonthlySettlementSummary,
  GenerateMonthlySettlementRequest,
  MonthlySettlementActionRequest,
} from '../types/settlement.types';

const BASE_PATH = '/api/v1/settlements';
const MONTHLY_PATH = '/api/v1/settlements/monthly';

// ========== Query Functions ==========

/**
 * Get paginated list of settlements
 * GET /api/v1/settlements
 */
export async function getSettlements(
  params: SettlementListParams = {}
): Promise<PaginatedResponse<Settlement>> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.settlement_type) searchParams.set('settlement_type', params.settlement_type);
  if (params.status) searchParams.set('status', params.status);
  if (params.payment_status) searchParams.set('payment_status', params.payment_status);
  if (params.supplier_id) searchParams.set('supplier_id', String(params.supplier_id));
  if (params.client_id) searchParams.set('client_id', String(params.client_id));
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.sort_order) searchParams.set('sort_order', params.sort_order);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  return apiFetchPaginated<Settlement>(url);
}

/**
 * Get single settlement by ID
 * GET /api/v1/settlements/:id
 */
export async function getSettlement(id: number): Promise<Settlement> {
  return apiFetch<Settlement>(`${BASE_PATH}/${id}`);
}

/**
 * Get settlement statistics
 * GET /api/v1/settlements/statistics
 */
export async function getSettlementStatistics(
  params: { start_date?: string; end_date?: string } = {}
): Promise<SettlementStatistics> {
  const searchParams = new URLSearchParams();

  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/statistics?${query}` : `${BASE_PATH}/statistics`;

  return apiFetch<SettlementStatistics>(url);
}

/**
 * Get overdue settlements
 * GET /api/v1/settlements/overdue
 */
export async function getOverdueSettlements(): Promise<Settlement[]> {
  return apiFetch<Settlement[]>(`${BASE_PATH}/overdue`);
}

/**
 * Get settlement payments
 * GET /api/v1/settlements/:id/payments
 */
export async function getSettlementPayments(settlementId: number): Promise<SettlementPayment[]> {
  return apiFetch<SettlementPayment[]>(`${BASE_PATH}/${settlementId}/payments`);
}

// ========== Mutation Functions ==========

/**
 * Create new settlement
 * POST /api/v1/settlements
 */
export async function createSettlement(input: SettlementCreateInput): Promise<Settlement> {
  return apiFetch<Settlement>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
}

/**
 * Update settlement
 * PUT /api/v1/settlements/:id
 */
export async function updateSettlement(
  id: number,
  input: SettlementUpdateInput
): Promise<Settlement> {
  return apiFetch<Settlement>(`${BASE_PATH}/${id}`, {
    method: 'PUT',
    body: input,
  });
}

// ========== Workflow Actions ==========

/**
 * Submit settlement for approval
 * POST /api/v1/settlements/:id/submit
 * State transition: DRAFT -> PENDING
 */
export async function submitSettlement(id: number): Promise<Settlement> {
  return apiFetch<Settlement>(`${BASE_PATH}/${id}/submit`, {
    method: 'POST',
  });
}

/**
 * Approve or reject settlement
 * POST /api/v1/settlements/:id/approve
 * State transition: PENDING -> APPROVED / REJECTED
 */
export async function approveSettlement(
  id: number,
  input: SettlementApproveInput
): Promise<Settlement> {
  return apiFetch<Settlement>(`${BASE_PATH}/${id}/approve`, {
    method: 'POST',
    body: input,
  });
}

/**
 * Record payment for settlement
 * POST /api/v1/settlements/:id/payment
 * Creates ledger entries per LEDGER_SOT.md v1.1
 */
export async function recordPayment(
  id: number,
  input: SettlementPaymentInput
): Promise<Settlement> {
  return apiFetch<Settlement>(`${BASE_PATH}/${id}/payment`, {
    method: 'POST',
    body: input,
  });
}

/**
 * Cancel settlement
 * POST /api/v1/settlements/:id/cancel
 * State transition: DRAFT/APPROVED -> CANCELLED
 */
export async function cancelSettlement(id: number, reason?: string): Promise<Settlement> {
  const searchParams = new URLSearchParams();
  if (reason) searchParams.set('reason', reason);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/${id}/cancel?${query}` : `${BASE_PATH}/${id}/cancel`;

  return apiFetch<Settlement>(url, {
    method: 'POST',
  });
}

// ========== 月度结算 API (D1-monthly-settlement.md §4) ==========

/**
 * 获取月度结算列表
 * GET /api/v1/settlements/monthly
 * SoT: D1-monthly-settlement.md §4.1 接口清单
 * 权限: finance, ceo
 */
export async function getMonthlySettlements(
  params: MonthlySettlementListParams = {}
): Promise<MonthlySettlementListResponse> {
  const searchParams = new URLSearchParams();

  if (params.month) searchParams.set('month', params.month);
  if (params.project_id) searchParams.set('project_id', String(params.project_id));
  if (params.status) searchParams.set('status', params.status);
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));

  const query = searchParams.toString();
  const url = query ? `${MONTHLY_PATH}?${query}` : MONTHLY_PATH;

  return apiFetch<MonthlySettlementListResponse>(url);
}

/**
 * 获取月度结算详情
 * GET /api/v1/settlements/monthly/:id
 * SoT: D1-monthly-settlement.md §4.1 接口清单
 * 权限: finance, ceo
 */
export async function getMonthlySettlement(id: number): Promise<MonthlySettlement> {
  return apiFetch<MonthlySettlement>(`${MONTHLY_PATH}/${id}`);
}

/**
 * 获取月度结算汇总
 * GET /api/v1/settlements/monthly/summary
 * SoT: D1-monthly-settlement.md §4.1 接口清单
 * 权限: finance, ceo
 */
export async function getMonthlySettlementSummary(
  month?: string
): Promise<MonthlySettlementSummary> {
  const url = month ? `${MONTHLY_PATH}/summary?month=${month}` : `${MONTHLY_PATH}/summary`;
  return apiFetch<MonthlySettlementSummary>(url);
}

/**
 * 生成月度结算
 * POST /api/v1/settlements/monthly/generate
 * SoT: D1-monthly-settlement.md §4.1 接口清单
 * 权限: finance
 */
export async function generateMonthlySettlement(input: GenerateMonthlySettlementRequest): Promise<{
  month: string;
  generated_count: number;
  total_spend: number;
  total_conversions: number;
}> {
  return apiFetch(`${MONTHLY_PATH}/generate`, {
    method: 'POST',
    body: input,
  });
}

/**
 * 确认月度结算
 * POST /api/v1/settlements/monthly/:id/confirm
 * SoT: D1-monthly-settlement.md §4.1 接口清单
 * 状态转换: draft → confirmed
 * 权限: finance
 */
export async function confirmMonthlySettlement(
  id: number,
  input?: MonthlySettlementActionRequest
): Promise<MonthlySettlement> {
  return apiFetch<MonthlySettlement>(`${MONTHLY_PATH}/${id}/confirm`, {
    method: 'POST',
    body: input || {},
  });
}

/**
 * 锁定月度结算
 * POST /api/v1/settlements/monthly/:id/lock
 * SoT: D1-monthly-settlement.md §4.1 接口清单
 * 状态转换: confirmed → locked (终态)
 * 权限: ceo, finance
 */
export async function lockMonthlySettlement(
  id: number,
  input?: MonthlySettlementActionRequest
): Promise<MonthlySettlement> {
  return apiFetch<MonthlySettlement>(`${MONTHLY_PATH}/${id}/lock`, {
    method: 'POST',
    body: input || {},
  });
}

/**
 * 解锁月度结算 (admin only)
 * POST /api/v1/settlements/monthly/:id/unlock
 * SoT: D1-monthly-settlement.md §4.1 接口清单
 * 状态转换: locked → confirmed
 * 权限: admin
 */
export async function unlockMonthlySettlement(
  id: number,
  input?: MonthlySettlementActionRequest
): Promise<MonthlySettlement> {
  return apiFetch<MonthlySettlement>(`${MONTHLY_PATH}/${id}/unlock`, {
    method: 'POST',
    body: input || {},
  });
}

/**
 * 导出月度结算报表
 * GET /api/v1/settlements/monthly/export
 * SoT: D1-monthly-settlement.md §4.1 接口清单
 * 权限: finance
 */
export async function exportMonthlySettlement(month?: string): Promise<Blob> {
  const url = month ? `${MONTHLY_PATH}/export?month=${month}` : `${MONTHLY_PATH}/export`;
  return apiDownload(url);
}
