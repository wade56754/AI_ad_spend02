/**
 * Settlement Rule Types
 *
 * SoT 对齐:
 * - DATA_SCHEMA.md v5.6 §3.5.7 (settlement_rules entity)
 * - BR-PROJ.md v1.0 (定价规则)
 * - MASTER.md v4.7 §6 (收入计算公式)
 */

// === Enum Types ===

/**
 * 结算规则类型
 * SoT: DATA_SCHEMA.md v5.6 §3.5.7
 */
export type SettlementRuleType = 'tiered' | 'markup';

/**
 * 加成类型 (markup 模式专用)
 */
export type MarkupType = 'percentage' | 'fixed';

// === Config Types ===

/**
 * 阶梯规则配置项
 * SoT: BR-PROJ.md v1.0 - tiered pricing
 *
 * @example
 * // 0-100 粉: ¥100/粉, 101-200 粉: ¥90/粉
 * { min: 0, max: 100, unit_price: 100 }
 * { min: 101, max: 200, unit_price: 90 }
 */
export interface TierConfig {
  min: number; // 起始数量 (含)
  max: number | null; // 结束数量 (含), null 表示无上限
  unit_price: number; // 该阶梯的单价
}

/**
 * 阶梯规则配置
 */
export interface TieredRuleConfig {
  tiers: TierConfig[];
}

/**
 * 加成规则配置
 * SoT: BR-PROJ.md v1.0 - markup pricing
 *
 * @example
 * // 消耗加成 10%
 * { markup_type: 'percentage', markup_value: 10 }
 * // 消耗加成 ¥500
 * { markup_type: 'fixed', markup_value: 500 }
 */
export interface MarkupRuleConfig {
  markup_type: MarkupType;
  markup_value: number;
}

/**
 * 规则配置联合类型
 */
export type RuleConfig = TieredRuleConfig | MarkupRuleConfig;

// === Entity Types ===

/**
 * 结算规则实体
 * SoT: DATA_SCHEMA.md v5.6 §3.5.7
 */
export interface SettlementRule {
  id: number;
  name: string;
  rule_type: SettlementRuleType;
  config: RuleConfig;
  effective_from: string; // YYYY-MM-DD
  effective_to: string | null; // YYYY-MM-DD or null
  created_by: string | null;
  created_at: string;
  updated_at: string;
  // Computed
  is_effective?: boolean;
}

// === List/Filter Types ===

export interface SettlementRuleListParams {
  page?: number;
  page_size?: number;
  rule_type?: SettlementRuleType;
  is_effective?: boolean;
  name?: string;
}

// === Form Types ===

export interface SettlementRuleCreateInput {
  name: string;
  rule_type: SettlementRuleType;
  config: RuleConfig;
  effective_from: string;
  effective_to?: string | null;
}

export interface SettlementRuleUpdateInput {
  name?: string;
  config?: RuleConfig;
  effective_to?: string | null;
}

// === Display Config ===

export const RULE_TYPE_CONFIG: Record<
  SettlementRuleType,
  {
    label: string;
    description: string;
  }
> = {
  tiered: {
    label: '阶梯计价',
    description: '按粉数分阶梯定价，累计计算',
  },
  markup: {
    label: '加成计价',
    description: '在广告消耗基础上加成',
  },
};

export const MARKUP_TYPE_CONFIG: Record<
  MarkupType,
  {
    label: string;
    unit: string;
  }
> = {
  percentage: {
    label: '百分比加成',
    unit: '%',
  },
  fixed: {
    label: '固定金额加成',
    unit: '¥',
  },
};

// === Type Guards ===

export function isTieredConfig(config: RuleConfig): config is TieredRuleConfig {
  return 'tiers' in config && Array.isArray(config.tiers);
}

export function isMarkupConfig(config: RuleConfig): config is MarkupRuleConfig {
  return 'markup_type' in config && 'markup_value' in config;
}
