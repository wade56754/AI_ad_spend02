/**
 * Commission Rules API Service
 *
 * TASK-PRJ-003: 提成配置
 * SoT 对齐:
 * - API_SOT.md v9.3 §7.4 Commission Rules API
 * - backend/routers/reconciliation_control.py
 */

import { apiFetch } from '@/lib/api';
import type {
  // CommissionRule - exported but not directly used in this file
  CommissionRuleListParams,
  CommissionRuleCreateInput,
  CommissionRuleUpdateInput,
  CommissionRuleListResponse,
  CommissionRuleResponse,
  CommissionCalculationResponse,
} from '../types/commissionRule.types';

const BASE_PATH = '/api/v1/reconciliation-control/commission-rules';

// ========== Query Functions ==========

/**
 * Get paginated list of commission rules
 * GET /api/v1/reconciliation-control/commission-rules
 */
export async function getCommissionRules(
  params: CommissionRuleListParams = {}
): Promise<CommissionRuleListResponse> {
  const searchParams = new URLSearchParams();

  if (params.effective_date) searchParams.set('effective_date', params.effective_date);
  if (params.skip !== undefined) searchParams.set('skip', String(params.skip));
  if (params.limit !== undefined) searchParams.set('limit', String(params.limit));

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  return apiFetch<CommissionRuleListResponse>(url);
}

/**
 * Get single commission rule by ID
 * GET /api/v1/reconciliation-control/commission-rules/:id
 */
export async function getCommissionRule(id: number): Promise<CommissionRuleResponse> {
  return apiFetch<CommissionRuleResponse>(`${BASE_PATH}/${id}`);
}

/**
 * Get default commission rule
 * GET /api/v1/reconciliation-control/commission-rules/default
 */
export async function getDefaultCommissionRule(): Promise<CommissionRuleResponse> {
  return apiFetch<CommissionRuleResponse>(`${BASE_PATH}/default`);
}

/**
 * Get effective commission rule for a project
 * GET /api/v1/reconciliation-control/projects/:projectId/effective-commission-rule
 */
export async function getProjectEffectiveRule(
  projectId: number,
  targetDate?: string
): Promise<CommissionRuleResponse> {
  const params = targetDate ? `?target_date=${targetDate}` : '';
  return apiFetch<CommissionRuleResponse>(
    `/api/v1/reconciliation-control/projects/${projectId}/effective-commission-rule${params}`
  );
}

// ========== Mutation Functions ==========

/**
 * Create new commission rule
 * POST /api/v1/reconciliation-control/commission-rules
 */
export async function createCommissionRule(
  input: CommissionRuleCreateInput
): Promise<CommissionRuleResponse> {
  return apiFetch<CommissionRuleResponse>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
}

/**
 * Update commission rule
 * PATCH /api/v1/reconciliation-control/commission-rules/:id
 */
export async function updateCommissionRule(
  id: number,
  input: CommissionRuleUpdateInput
): Promise<CommissionRuleResponse> {
  return apiFetch<CommissionRuleResponse>(`${BASE_PATH}/${id}`, {
    method: 'PATCH',
    body: input,
  });
}

/**
 * Delete commission rule (soft delete)
 * DELETE /api/v1/reconciliation-control/commission-rules/:id
 */
export async function deleteCommissionRule(id: number): Promise<{ message: string }> {
  return apiFetch<{ message: string }>(`${BASE_PATH}/${id}`, {
    method: 'DELETE',
  });
}

// ========== Actions ==========

/**
 * Calculate commission for given conversions
 * POST /api/v1/reconciliation-control/commission-rules/:id/calculate
 */
export async function calculateCommission(
  ruleId: number,
  conversions: number
): Promise<CommissionCalculationResponse> {
  return apiFetch<CommissionCalculationResponse>(
    `${BASE_PATH}/${ruleId}/calculate?conversions=${conversions}`,
    { method: 'POST' }
  );
}

/**
 * Set rule as default
 */
export async function setAsDefault(id: number): Promise<CommissionRuleResponse> {
  return updateCommissionRule(id, { is_default: true });
}
