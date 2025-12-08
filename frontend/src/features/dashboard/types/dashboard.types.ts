/**
 * Dashboard Types
 */

export interface DashboardStats {
  // 今日数据
  today_spend: number;
  today_conversions: number;
  today_revenue: number;
  today_profit: number;

  // 待处理项
  pending_topups: number;
  pending_settlements: number;
  pending_reconciliations: number;
  pending_imports: number;

  // 账户统计
  active_projects: number;
  active_accounts: number;
  total_balance: number;

  // 环比变化
  spend_change: number | null;
  conversions_change: number | null;
  profit_change: number | null;
}

export interface DashboardTrendItem {
  date: string;
  spend: number;
  conversions: number;
  profit: number;
}

export interface DashboardAlert {
  id: string;
  type: 'warning' | 'error' | 'info';
  title: string;
  message: string;
  created_at: string;
  is_read: boolean;
}

export interface QuickAction {
  id: string;
  label: string;
  icon: string;
  href: string;
  color: string;
}

export const QUICK_ACTIONS: QuickAction[] = [
  { id: 'daily-report', label: '新建日报', icon: 'file-plus', href: '/daily-reports/new', color: 'blue' },
  { id: 'topup', label: '充值申请', icon: 'plus-circle', href: '/topups/new', color: 'green' },
  { id: 'import', label: '导入数据', icon: 'upload', href: '/import-jobs', color: 'purple' },
  { id: 'reconcile', label: '对账管理', icon: 'check-square', href: '/reconciliation', color: 'orange' },
];
