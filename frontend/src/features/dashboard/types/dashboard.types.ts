/**
 * Dashboard Types
 *
 * Based on DASHBOARD_FRONTEND_DESIGN_v1.2.md
 */

// ============ 统计卡片类型 ============

export interface StatSummary {
  label: string;
  value: number;
  change?: number | null;
  format: 'currency' | 'number';
}

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

  // 环比变化 (与近7日均值对比)
  spend_change: number | null;
  conversions_change: number | null;
  revenue_change: number | null;
  profit_change: number | null;
}

// ============ 趋势图类型 ============

export interface TrendPoint {
  date: string;      // 'YYYY-MM-DD'
  value: number;
}

export interface TrendDataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface DashboardTrendItem {
  date: string;
  spend: number;
  conversions: number;
  revenue: number;
  profit: number;
}

export interface DashboardTrends {
  spendTrend: TrendPoint[];      // 消耗趋势
  conversionsTrend: TrendPoint[]; // 粉数趋势
  revenueTrend: TrendPoint[];    // 收入趋势
}

// ============ 待办事项类型 ============

export interface PendingTask {
  id: string;
  title: string;
  count: number;
  href: string;
  priority: 'high' | 'medium' | 'low';
  icon?: string;
}

// ============ 快捷操作类型 ============

export interface QuickAction {
  id: string;
  label: string;
  icon: string;
  href: string;
  color: 'blue' | 'green' | 'purple' | 'orange';
}

export const QUICK_ACTIONS: QuickAction[] = [
  { id: 'daily-report', label: '新建日报', icon: 'file-plus', href: '/daily-reports/new', color: 'blue' },
  { id: 'topup', label: '充值申请', icon: 'plus-circle', href: '/topups/new', color: 'green' },
  { id: 'import', label: '导入数据', icon: 'upload', href: '/import-jobs', color: 'purple' },
  { id: 'reconcile', label: '对账管理', icon: 'check-square', href: '/reconciliation', color: 'orange' },
];

// ============ 系统状态类型 ============

export interface SystemStatusItem {
  name: string;
  status: 'healthy' | 'warning' | 'error';
  description?: string;
}

export interface SystemStatus {
  api: SystemStatusItem;
  database: SystemStatusItem;
  scheduler: SystemStatusItem;
}

// ============ 告警类型 ============

export interface DashboardAlert {
  id: string;
  type: 'warning' | 'error' | 'info';
  title: string;
  message: string;
  created_at: string;
  is_read: boolean;
}

// ============ 完整仪表盘数据类型 ============

export interface DashboardData {
  stats: DashboardStats;
  trends: DashboardTrends;
  pendingTasks: PendingTask[];
  quickActions: QuickAction[];
  systemStatus: SystemStatus;
}

// ============ 过滤器类型 ============

export interface DashboardFilters {
  dateFrom?: string;
  dateTo?: string;
  projectId?: string;
  channel?: string;
}
