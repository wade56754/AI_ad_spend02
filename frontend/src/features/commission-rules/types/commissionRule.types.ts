/**
 * Commission Rules Types - 提成规则类型定义
 *
 * TASK-PRJ-003: 提成配置
 * SoT 对齐:
 * - DATA_SCHEMA.md v5.7 §3.5.8 (commission_rules entity)
 * - BUSINESS_RULES.md v4.8 BR-COM-*
 * - backend/schemas/reconciliation.py (CommissionRule*)
 */

// ========== 基础接口 ==========

/**
 * 提成阶梯配置
 *
 * Example:
 *   { min: 1, max: 50, rate: 1.0 }    // 1-50 粉: 每粉 $1
 *   { min: 51, max: 100, rate: 1.5 }  // 51-100 粉: 每粉 $1.5
 *   { min: 101, max: null, rate: 2.0 } // 101+ 粉: 每粉 $2
 */
export interface CommissionTier {
  min: number; // 最小进粉数 (≥1)
  max: number | null; // 最大进粉数 (null=无上限)
  rate: number; // 单粉提成金额
}

/**
 * 提成规则配置 JSON 结构
 */
export interface CommissionConfig {
  tiers: CommissionTier[];
}

/**
 * Commission Rule entity - 对齐 backend CommissionRuleResponse schema
 */
export interface CommissionRule {
  id: number;
  name: string;
  config: CommissionConfig;
  effective_from: string; // YYYY-MM-DD
  effective_to: string | null; // YYYY-MM-DD or null
  is_default: boolean;
  is_effective?: boolean; // 计算字段
  created_by: string | null; // UUID
  created_at: string;
  updated_at: string;
}

// ========== 请求接口 ==========

/**
 * Create input - 对齐 backend CommissionRuleCreate schema
 */
export interface CommissionRuleCreateInput {
  name: string;
  config: CommissionConfig;
  effective_from: string; // YYYY-MM-DD
  effective_to?: string | null; // YYYY-MM-DD
  is_default?: boolean;
}

/**
 * Update input - 对齐 backend CommissionRuleUpdate schema
 */
export interface CommissionRuleUpdateInput {
  name?: string;
  config?: CommissionConfig;
  effective_to?: string | null;
  is_default?: boolean;
}

export interface CommissionRuleListParams {
  effective_date?: string; // YYYY-MM-DD
  skip?: number;
  limit?: number;
}

// ========== 响应接口 ==========

export interface CommissionRuleListResponse {
  data: {
    items: CommissionRule[];
    meta: {
      total: number;
      skip: number;
      limit: number;
    };
  };
  message?: string;
}

export interface CommissionRuleResponse {
  data: CommissionRule;
  message?: string;
}

/**
 * 提成计算结果
 */
export interface CommissionCalculation {
  rule_id: number;
  rule_name: string;
  conversions: number;
  total_commission: number;
  currency: string;
  breakdown: CommissionBreakdownItem[];
}

export interface CommissionBreakdownItem {
  tier: CommissionTier;
  count: number;
  amount: number;
}

export interface CommissionCalculationResponse {
  data: CommissionCalculation;
  message?: string;
}

// ========== UI 配置 ==========

export const COMMISSION_RULE_STATUS_CONFIG = {
  effective: {
    label: '生效中',
    color: 'success' as const,
    description: '规则当前有效',
  },
  expired: {
    label: '已过期',
    color: 'default' as const,
    description: '规则已过期',
  },
  future: {
    label: '未生效',
    color: 'warning' as const,
    description: '规则尚未生效',
  },
};

/**
 * 获取规则状态
 */
export function getRuleStatus(rule: CommissionRule): 'effective' | 'expired' | 'future' {
  const today = new Date().toISOString().split('T')[0];

  if (rule.effective_from > today) {
    return 'future';
  }

  if (rule.effective_to && rule.effective_to < today) {
    return 'expired';
  }

  return 'effective';
}

/**
 * 格式化阶梯显示
 */
export function formatTierRange(tier: CommissionTier): string {
  if (tier.max === null) {
    return `${tier.min}+`;
  }
  return `${tier.min}-${tier.max}`;
}

/**
 * 格式化金额
 */
export function formatCommissionAmount(amount: number, currency = 'CNY'): string {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(amount);
}
