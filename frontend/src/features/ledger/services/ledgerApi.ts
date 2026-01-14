/**
 * Ledger API Service
 *
 * Aligned with API_SOT.md v9.4 Section 5.7 (Ledger endpoints)
 *
 * Read Operations: All users with ledger access
 * Write Operations: admin, finance only
 *
 * SoT References:
 * - LEDGER_SOT.md v1.1 (Double-entry bookkeeping rules)
 * - BR-FIN.md v1.1 (Financial business rules)
 */

import { apiFetch, apiFetchPaginated, apiPost } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';
import type {
  LedgerEntry,
  LedgerListParams,
  TenantBalance,
  ProjectBalance,
  LedgerEntryType,
} from '../types';

const BASE_PATH = '/api/v1/ledger';

// === Transaction Types (for mutations) ===

/**
 * Transaction types supported by the backend
 * Aligned with backend/models/ledger.py TransactionType enum
 */
export type TransactionType =
  | 'TOPUP'
  | 'SPEND'
  | 'REFUND'
  | 'FEE'
  | 'ADJUSTMENT'
  | 'TRANSFER';

/**
 * Request payload for creating a transaction
 */
export interface CreateTransactionRequest {
  transaction_type: TransactionType;
  amount: number;
  currency?: string;
  project_id?: string;
  account_id?: string;
  topup_id?: string;
  reference_id?: string;
  description: string;
  metadata?: Record<string, unknown>;
}

/**
 * Response from creating a transaction
 */
export interface TransactionResponse {
  id: string;
  transaction_number: string;
  transaction_type: TransactionType;
  amount: number;
  currency: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  project_id?: string;
  account_id?: string;
  topup_id?: string;
  reference_id?: string;
  description?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at?: string;
}

// === Query Functions (READ-ONLY) ===

/**
 * Get paginated list of ledger entries
 * GET /api/v1/ledger/entries
 */
export async function getLedgerEntries(
  params: LedgerListParams = {}
): Promise<PaginatedResponse<LedgerEntry>> {
  const searchParams = new URLSearchParams();

  if (params.tenant_id) searchParams.set('tenant_id', params.tenant_id);
  if (params.project_id) searchParams.set('project_id', params.project_id);
  if (params.entry_type) {
    const types = Array.isArray(params.entry_type) ? params.entry_type : [params.entry_type];
    types.forEach((t) => searchParams.append('entry_type', t));
  }
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.min_amount) searchParams.set('min_amount', String(params.min_amount));
  if (params.max_amount) searchParams.set('max_amount', String(params.max_amount));
  if (params.reference_type) searchParams.set('reference_type', params.reference_type);
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.sort_order) searchParams.set('sort_order', params.sort_order);

  const query = searchParams.toString();
  // 后端端点是 /transactions，兼容前端 entries 概念
  const url = query ? `${BASE_PATH}/transactions?${query}` : `${BASE_PATH}/transactions`;

  return apiFetchPaginated<LedgerEntry>(url);
}

/**
 * Get single ledger entry by ID
 * GET /api/v1/ledger/entries/:id
 */
export async function getLedgerEntry(id: string): Promise<LedgerEntry> {
  return apiFetch<LedgerEntry>(`${BASE_PATH}/entries/${id}`);
}

/**
 * Get tenant balance
 * GET /api/v1/ledger/balance/tenant/:tenantId
 */
export async function getTenantBalance(tenantId: string): Promise<TenantBalance> {
  return apiFetch<TenantBalance>(`${BASE_PATH}/balance/tenant/${tenantId}`);
}

/**
 * Get project balance
 * GET /api/v1/ledger/balance/project/:projectId
 */
export async function getProjectBalance(projectId: string): Promise<ProjectBalance> {
  return apiFetch<ProjectBalance>(`${BASE_PATH}/balance/project/${projectId}`);
}

/**
 * Get all project balances for a tenant
 * GET /api/v1/ledger/balance/tenant/:tenantId/projects
 */
export async function getTenantProjectBalances(
  tenantId: string
): Promise<ProjectBalance[]> {
  return apiFetch<ProjectBalance[]>(`${BASE_PATH}/balance/tenant/${tenantId}/projects`);
}

/**
 * Get ledger entries by reference
 * GET /api/v1/ledger/entries/by-reference
 */
export async function getLedgerEntriesByReference(
  referenceType: 'topup' | 'daily_report' | 'transfer' | 'manual',
  referenceId: string
): Promise<LedgerEntry[]> {
  const params = new URLSearchParams({
    reference_type: referenceType,
    reference_id: referenceId,
  });
  return apiFetch<LedgerEntry[]>(`${BASE_PATH}/entries/by-reference?${params}`);
}

// === Statistics ===

/**
 * Get ledger statistics
 * GET /api/v1/ledger/stats
 */
export async function getLedgerStats(params: {
  tenant_id?: string;
  project_id?: string;
  start_date?: string;
  end_date?: string;
}): Promise<{
  by_type: Record<LedgerEntryType, { count: number; total_amount: number }>;
  total_entries: number;
  net_flow: number;
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
 * Verify balance integrity (admin only)
 * GET /api/v1/ledger/verify/:tenantId
 */
export async function verifyBalanceIntegrity(tenantId: string): Promise<{
  is_valid: boolean;
  expected_balance: number;
  actual_balance: number;
  discrepancy: number;
  entries_count: number;
}> {
  return apiFetch(`${BASE_PATH}/verify/${tenantId}`);
}

// === Mutation Functions (admin/finance only) ===

/**
 * Create a new transaction
 * POST /api/v1/ledger/transactions
 *
 * @permission admin, finance
 * @sot BR-FIN.md v1.1 - Financial transaction rules
 */
export async function createTransaction(
  data: CreateTransactionRequest
): Promise<TransactionResponse> {
  return apiPost<TransactionResponse>(`${BASE_PATH}/transactions`, data);
}

/**
 * Update transaction status
 * PATCH /api/v1/ledger/transactions/:id
 *
 * @permission admin, finance
 */
export async function updateTransactionStatus(
  id: string,
  data: { status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'; note?: string }
): Promise<TransactionResponse> {
  return apiFetch<TransactionResponse>(`${BASE_PATH}/transactions/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/**
 * Create a reversal (红冲) for an existing transaction
 * POST /api/v1/ledger/transactions/:id/reverse
 *
 * @permission admin, finance
 * @sot BR-FIN.md v1.1 §BR-FIN-007 红冲规则
 */
export async function createReversal(
  transactionId: string,
  data: { reason: string }
): Promise<TransactionResponse> {
  return apiPost<TransactionResponse>(
    `${BASE_PATH}/transactions/${transactionId}/reverse`,
    data
  );
}
