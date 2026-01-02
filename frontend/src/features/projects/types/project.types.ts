/**
 * Project Types
 *
 * SoT 对齐:
 * - STATE_MACHINE.md v2.8 Section 5
 * - DATA_SCHEMA.md v5.6 (projects entity)
 * - BR-PROJ.md v1.0 (定价规则)
 */

// === Status Enum ===

// SoT 对齐: STATE_MACHINE.md v2.8 Section 5 - 项目状态机
export type ProjectStatus =
  | 'planning' // 规划中 (初始状态)
  | 'active' // 进行中
  | 'paused' // 已暂停
  | 'completed' // 已完成 (终态)
  | 'cancelled'; // 已取消 (终态)

// SoT: BR-PROJ.md v1.0 §BR-PROJ-002 - 结算类型
export type SettlementType = 'fixed' | 'tiered' | 'markup';

export const SETTLEMENT_TYPE_CONFIG: Record<
  SettlementType,
  {
    label: string;
    description: string;
  }
> = {
  fixed: { label: '按粉计费', description: '收入 = 进粉数 × 单粉价格' },
  tiered: { label: '阶梯计价', description: '根据进粉数量分段计价' },
  markup: { label: '加成计价', description: '收入 = 消耗 × (1 + 加成比例)' },
};

// === Entity Types ===

export interface Project {
  id: number;
  name: string;
  client_name: string;
  client_company: string;
  description?: string;
  status: ProjectStatus;
  budget: number;
  currency: string;
  start_date?: string;
  end_date?: string;
  // 新增: MASTER.md v4.4 §6.2 - 项目负责人
  owner_id?: number;
  owner_name?: string;
  // 新增: 目标 CPL 和单粉价格
  target_cpl?: number | null;
  unit_price?: number | null;
  // 新增: 结算配置 (BR-PROJ.md v1.0)
  settlement_type?: SettlementType;
  settlement_rules_id?: number | null;
  // 新增: 提成配置 (TASK-PRJ-003)
  commission_rules_id?: number | null;
  // 新增: 地区和聚合进粉数
  region?: string | null;
  total_follows?: number; // 从日报聚合的总进粉数
  // 兼容旧字段
  account_manager_id?: number;
  account_manager_name?: string;
  total_spent: number;
  total_accounts: number;
  active_accounts: number;
  created_by?: string;
  created_by_name: string;
  created_at: string;
  updated_at: string;
  // Computed
  remaining_budget?: number;
  budget_usage_percent?: number;
}

export interface ProjectMember {
  id: number;
  user_id: string;
  user_name: string;
  user_email: string;
  user_role: string;
  project_role: string;
  joined_at: string;
}

export interface ProjectExpense {
  id: number;
  expense_type: string;
  amount: number;
  description?: string;
  expense_date: string;
  created_by_name: string;
  created_at: string;
}

export interface ProjectStatistics {
  total_projects: number;
  active_projects: number;
  paused_projects: number;
  completed_projects: number;
  cancelled_projects: number;
  total_budget: number;
  total_spent: number;
  total_clients: number;
  avg_project_value: number;
  top_performers: Array<{ id: number; name: string; roi: number }>;
}

// === List/Filter Types ===

export interface ProjectListParams {
  page?: number;
  page_size?: number;
  status?: ProjectStatus;
  manager_id?: number;
  client_name?: string;
}

// === Form Types ===

export interface ProjectCreateInput {
  name: string;
  client_name: string;
  client_company: string;
  description?: string;
  budget?: number;
  currency?: string;
  start_date?: string;
  end_date?: string;
  // 新增: 项目负责人、目标CPL、单价
  owner_id?: number;
  target_cpl?: number;
  unit_price?: number;
  // 新增: 结算配置 (BR-PROJ.md v1.0)
  settlement_type?: SettlementType;
  settlement_rules_id?: number | null;
  // 新增: 提成配置 (TASK-PRJ-003)
  commission_rules_id?: number | null;
  // 兼容旧字段
  account_manager_id?: number;
}

export interface ProjectUpdateInput {
  name?: string;
  client_name?: string;
  client_company?: string;
  description?: string;
  status?: ProjectStatus;
  budget?: number;
  start_date?: string;
  end_date?: string;
  // 新增: 项目负责人、目标CPL、单价
  owner_id?: number;
  target_cpl?: number;
  unit_price?: number;
  // 新增: 结算规则 (BR-PROJ.md v1.0) - 注意: settlement_type 不可修改
  settlement_rules_id?: number | null;
  // 新增: 提成规则 (TASK-PRJ-003)
  commission_rules_id?: number | null;
  // 兼容旧字段
  account_manager_id?: number;
}

export interface ProjectMemberAssignInput {
  user_id: string | number;
  role: 'account_manager' | 'pitcher' | 'analyst';
}

// === Status Display Config ===

export const PROJECT_STATUS_CONFIG: Record<
  ProjectStatus,
  {
    label: string;
    variant: 'default' | 'success' | 'warning' | 'error';
    description: string;
  }
> = {
  planning: { label: '规划中', variant: 'default', description: '项目准备阶段' },
  active: { label: '进行中', variant: 'success', description: '正常投放' },
  paused: { label: '已暂停', variant: 'warning', description: '暂停投放' },
  completed: { label: '已完成', variant: 'default', description: '项目结束' },
  cancelled: { label: '已取消', variant: 'error', description: '项目取消' },
};

export const PROJECT_ROLE_CONFIG: Record<string, { label: string }> = {
  account_manager: { label: '户管' },
  pitcher: { label: '投手' },
  analyst: { label: '数据分析师' },
};

// === Dashboard Types (TASK-PRJ-004) ===

export interface DailyTrendItem {
  date: string;
  spend: number;
  follows: number;
  conversions: number;
  cpl: number | null;
}

export interface AccountPerformance {
  account_id: number;
  account_name: string;
  platform: string | null;
  status: string;
  spend: number;
  follows: number;
  conversions: number;
  cpl: number | null;
}

export interface ProjectDashboard {
  total_spend: number;
  total_follows: number;
  total_conversions: number;
  avg_cpl: number | null;
  budget_usage_percent: number;
  daily_trend: DailyTrendItem[];
  account_performance: AccountPerformance[];
  period_start: string | null;
  period_end: string | null;
}

export interface ProjectDashboardParams {
  days?: number;
}

// === Prepayment Types (TASK-PRJ-005) ===

/**
 * 预付款流水类型
 * SoT: DATA_SCHEMA.md v5.7 (project_prepayments entity)
 */
export type PrepaymentEntryType = 'TOPUP' | 'REVERSAL';

export const PREPAYMENT_ENTRY_TYPE_CONFIG: Record<
  PrepaymentEntryType,
  { label: string; variant: 'success' | 'error' }
> = {
  TOPUP: { label: '入账', variant: 'success' },
  REVERSAL: { label: '红冲', variant: 'error' },
};

/**
 * 预付款记录
 */
export interface PrepaymentEntry {
  id: number;
  project_id: number;
  project_name?: string;
  entry_type: PrepaymentEntryType;
  amount: number;
  balance_after: number;
  entry_date: string;
  reference_id?: number | null;
  notes?: string | null;
  created_by?: number | null;
  operator_name?: string | null;
  created_at: string;
}

/**
 * 预付款余额响应
 */
export interface PrepaymentBalance {
  project_id: number;
  project_name?: string;
  balance: number;
  total_topup: number;
  total_reversal: number;
  entry_count: number;
  last_entry_date?: string | null;
}

/**
 * 预付款入账请求
 */
export interface PrepaymentCreateInput {
  amount: number;
  entry_date: string;
  notes?: string;
}

/**
 * 预付款红冲请求
 */
export interface PrepaymentReversalInput {
  reference_id: number;
  amount: number; // 必须为负数
  entry_date: string;
  notes?: string;
}

/**
 * 预付款列表查询参数
 */
export interface PrepaymentListParams {
  page?: number;
  page_size?: number;
  entry_type?: PrepaymentEntryType;
}
