/**
 * Settlements API Service
 *
 * SoT 对齐:
 * - API_SOT.md v9.0 (API conventions)
 * - LEDGER_SOT.md v1.1 (ledger integration)
 * - backend/routers/settlements.py
 */

import { apiFetch, apiFetchPaginated } from '@/lib/api';
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
} from '../types/settlement.types';

const BASE_PATH = '/api/v1/settlements';

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
export async function getSettlementPayments(
  settlementId: number
): Promise<SettlementPayment[]> {
  return apiFetch<SettlementPayment[]>(`${BASE_PATH}/${settlementId}/payments`);
}

// ========== Mutation Functions ==========

/**
 * Create new settlement
 * POST /api/v1/settlements
 */
export async function createSettlement(
  input: SettlementCreateInput
): Promise<Settlement> {
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
export async function cancelSettlement(
  id: number,
  reason?: string
): Promise<Settlement> {
  const searchParams = new URLSearchParams();
  if (reason) searchParams.set('reason', reason);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/${id}/cancel?${query}` : `${BASE_PATH}/${id}/cancel`;

  return apiFetch<Settlement>(url, {
    method: 'POST',
  });
}
