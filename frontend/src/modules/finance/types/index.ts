/**
 * Finance 模块类型定义
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3, FRONTEND_MODULE_SHELL_PATTERN v1.0
 */

// =============================================================================
// 筛选状态类型
// =============================================================================

export type TopupStatus = 'pending' | 'approved' | 'rejected' | 'completed';

export interface FinanceFiltersState {
  /** 搜索关键词 */
  search: string;
  /** 状态筛选 */
  status: TopupStatus | 'all';
  /** 当前激活的 Tab */
  activeTab: 'overview' | 'topup' | 'analysis' | 'team';
}

// =============================================================================
// 充值申请类型
// =============================================================================

export interface TopupRequest {
  id: number;
  user_name: string;
  user_role: string;
  account_name: string;
  platform: string;
  amount: number;
  currency: string;
  reason: string;
  status: TopupStatus;
  created_at: string;
  reviewed_at?: string;
  reviewed_by?: string;
  review_comment?: string;
  receipt_url?: string;
  transaction_id?: string;
  completed_at?: string;
}

// =============================================================================
// 财务汇总类型
// =============================================================================

export interface FinancialSummary {
  total_balance: number;
  currency: string;
  this_month_spending: number;
  last_month_spending: number;
  pending_topups: number;
  approved_topups: number;
  average_approval_time: number;
  success_rate: number;
  projected_spend: number;
}

// =============================================================================
// 图表数据类型
// =============================================================================

export interface SpendingTrend {
  date: string;
  spending: number;
  topups: number;
  balance: number;
}

export interface PlatformSpending {
  platform: string;
  amount: number;
  percentage: number;
  color: string;
}

export interface TeamSpending {
  user_name: string;
  role: string;
  total_spent: number;
  budget_utilization: number;
  projects_count: number;
  efficiency_score: number;
}

// =============================================================================
// 数据状态类型
// =============================================================================

export interface FinanceDataState {
  topupRequests: TopupRequest[];
  financialSummary: FinancialSummary;
  spendingTrends: SpendingTrend[];
  platformSpending: PlatformSpending[];
  teamSpending: TeamSpending[];
}
