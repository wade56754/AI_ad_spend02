/**
 * Project Types
 *
 * SoT 对齐:
 * - STATE_MACHINE.md v2.6 Section 5
 * - DATA_SCHEMA.md v5.2 (projects entity)
 */

// === Status Enum ===

// SoT 对齐: STATE_MACHINE.md v2.6 Section 5 - 项目状态机
export type ProjectStatus =
  | 'planning'    // 规划中 (初始状态)
  | 'active'      // 进行中
  | 'paused'      // 已暂停
  | 'completed'   // 已完成 (终态)
  | 'cancelled';  // 已取消 (终态)

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
  // 新增: 地区和聚合进粉数
  region?: string | null;
  total_follows?: number;  // 从日报聚合的总进粉数
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
  // 兼容旧字段
  account_manager_id?: number;
}

export interface ProjectMemberAssignInput {
  user_id: string | number;
  role: 'account_manager' | 'media_buyer' | 'analyst';
}

// === Status Display Config ===

export const PROJECT_STATUS_CONFIG: Record<ProjectStatus, {
  label: string;
  variant: 'default' | 'success' | 'warning' | 'error';
  description: string;
}> = {
  planning: { label: '规划中', variant: 'default', description: '项目准备阶段' },
  active: { label: '进行中', variant: 'success', description: '正常投放' },
  paused: { label: '已暂停', variant: 'warning', description: '暂停投放' },
  completed: { label: '已完成', variant: 'default', description: '项目结束' },
  cancelled: { label: '已取消', variant: 'error', description: '项目取消' },
};

export const PROJECT_ROLE_CONFIG: Record<string, { label: string }> = {
  account_manager: { label: '项目经理' },
  media_buyer: { label: '媒介采购' },
  analyst: { label: '数据分析师' },
};
