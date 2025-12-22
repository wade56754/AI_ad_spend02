/**
 * Finance Module Types
 *
 * SoT 对齐: LEDGER_SOT.md v1.1, BUSINESS_RULES.md v3.2
 */

// 财务概览统计
export interface FinanceOverview {
  total_revenue: number;        // 总收入
  total_cost: number;           // 总成本
  total_profit: number;         // 总利润
  profit_margin: number;        // 利润率 (%)
  pending_settlements: number;  // 待结算金额
  pending_topups: number;       // 待审批充值
}

// 财务趋势数据
export interface FinanceTrend {
  date: string;
  revenue: number;
  cost: number;
  profit: number;
}

// 账户余额信息
export interface AccountBalance {
  account_id: number;
  account_name: string;
  platform: string;
  balance: number;
  last_topup: string;
  status: 'normal' | 'low' | 'critical';
}

// 待办事项
export interface FinanceTodo {
  id: number;
  type: 'topup' | 'settlement' | 'reconciliation' | 'alert';
  title: string;
  amount?: number;
  priority: 'high' | 'medium' | 'low';
  created_at: string;
  due_date?: string;
}

// 最近交易记录
export interface RecentTransaction {
  id: number;
  type: 'topup' | 'consume' | 'refund' | 'settlement';
  account_name: string;
  amount: number;
  status: string;
  created_at: string;
}

// 平台消耗统计
export interface PlatformSpend {
  platform: string;
  spend: number;
  percentage: number;
  trend: 'up' | 'down' | 'stable';
}
