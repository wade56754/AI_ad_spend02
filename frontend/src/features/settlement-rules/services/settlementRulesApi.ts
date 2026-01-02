/**
 * Settlement Rules API Service
 *
 * SoT: DATA_SCHEMA.md v5.6 §3.5.7 (settlement_rules entity)
 * SoT: BR-PROJ.md v1.0 (定价规则)
 * Backend: backend/routers/reconciliation_control.py
 *
 * @module features/settlement-rules/services
 */

import { apiFetch, apiFetchPaginated, type PaginatedResponse } from '@/lib/api';
import type {
  SettlementRule,
  SettlementRuleListParams,
  SettlementRuleCreateInput,
  SettlementRuleUpdateInput,
} from '../types';

const BASE_PATH = '/api/v1/reconciliation-control/settlement-rules';

// ========== Query Functions ==========

/**
 * 获取结算规则列表
 * GET /api/v1/reconciliation-control/settlement-rules
 */
export async function getSettlementRules(
  params: SettlementRuleListParams = {}
): Promise<PaginatedResponse<SettlementRule>> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.rule_type) searchParams.set('rule_type', params.rule_type);
  if (params.is_effective !== undefined)
    searchParams.set('is_effective', String(params.is_effective));
  if (params.name) searchParams.set('name', params.name);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  return apiFetchPaginated<SettlementRule>(url);
}

/**
 * 获取结算规则详情
 * GET /api/v1/reconciliation-control/settlement-rules/{id}
 */
export async function getSettlementRule(id: number): Promise<SettlementRule> {
  return apiFetch<SettlementRule>(`${BASE_PATH}/${id}`);
}

/**
 * 获取当前生效的结算规则列表 (用于下拉选择)
 * GET /api/v1/reconciliation-control/settlement-rules?is_effective=true
 */
export async function getEffectiveSettlementRules(): Promise<SettlementRule[]> {
  const response = await apiFetchPaginated<SettlementRule>(
    `${BASE_PATH}?is_effective=true&page_size=100`
  );
  return response.items;
}

// ========== Mutation Functions ==========

/**
 * 创建结算规则
 * POST /api/v1/reconciliation-control/settlement-rules
 */
export async function createSettlementRule(
  input: SettlementRuleCreateInput
): Promise<SettlementRule> {
  return apiFetch<SettlementRule>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
}

/**
 * 更新结算规则
 * PATCH /api/v1/reconciliation-control/settlement-rules/{id}
 *
 * Note: rule_type 不可修改 (BR-PROJ-002)
 */
export async function updateSettlementRule(
  id: number,
  input: SettlementRuleUpdateInput
): Promise<SettlementRule> {
  return apiFetch<SettlementRule>(`${BASE_PATH}/${id}`, {
    method: 'PATCH',
    body: input,
  });
}

/**
 * 删除结算规则 (软删除)
 * DELETE /api/v1/reconciliation-control/settlement-rules/{id}
 */
export async function deleteSettlementRule(id: number): Promise<void> {
  await apiFetch(`${BASE_PATH}/${id}`, { method: 'DELETE' });
}
