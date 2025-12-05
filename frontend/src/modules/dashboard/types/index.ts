/**
 * Dashboard 模块类型定义
 *
 * 结构设计为未来对接 daily_reports / finance_profit API 预留
 */

// 筛选器状态（重命名避免与组件同名）
export interface DashboardFiltersState {
  dateRange: 'today' | '7d' | '30d' | 'custom';
  projectId?: string;
  startDate?: string;
  endDate?: string;
}

/** @deprecated 使用 DashboardFiltersState 代替 */
export type DashboardFilters = DashboardFiltersState;

// KPI 指标数据
export interface KpiMetric {
  id: string;
  title: string;
  value: string | number;
  change?: number;
  changeType?: 'up' | 'down' | 'neutral';
  description?: string;
  icon: React.ComponentType<{ className?: string }>;
  color: 'primary' | 'success' | 'warning' | 'error' | 'info';
  priority?: 'primary' | 'secondary'; // 区分主要指标和次要指标
}

// 趋势数据点
export interface TrendDataPoint {
  label: string;
  value: number;
  date?: string;
}

// 趋势图表数据（简化版，用于组合图）
export interface TrendChartData {
  date: string;
  spend: number;
  roi: number;
}

// 趋势图表数据（完整版，保留向后兼容）
export interface TrendChartDataFull {
  title: string;
  description?: string;
  trend: {
    value: number;
    isPositive: boolean;
  };
  dataPoints: TrendDataPoint[];
}

/**
 * 待办任务（UI 展示层）
 *
 * SoT 映射说明（参考 STATE_MACHINE.md v2.6）:
 * - 此 status 是 UI 层聚合状态，非直接映射 SoT 表状态
 * - daily_report: 8 状态机 → pending (trend_pending/final_pending)
 * - topup_request: 7 状态机 → pending (pending_review)
 * - reconciliation: 5 状态机 → pending (pending_review)
 *
 * UI Status 映射规则:
 * - 'pending': 需要当前用户处理的待办
 * - 'in_progress': 用户已开始处理
 * - 'completed': 已完成或已流转到下一状态
 */
export interface TodoTask {
  id: string;
  title: string;
  priority: 'high' | 'medium' | 'low';
  /** UI 聚合状态，非 SoT 表原始状态 */
  status: 'pending' | 'in_progress' | 'completed';
  assignee?: string;
  project?: string;
  dueTime?: string;
  /** 关联的业务实体类型 */
  relatedEntityType?: 'daily_report' | 'topup_request' | 'reconciliation';
  /** 关联的业务实体 ID，用于跳转详情 */
  relatedEntityId?: string;
}

// Dashboard 整体数据结构
export interface DashboardData {
  kpiMetrics: KpiMetric[];
  spendTrend: TrendChartData;
  roiTrend: TrendChartData;
  todoTasks: TodoTask[];
  lastUpdated: string;
}

// 项目选项（用于筛选器）
export interface ProjectOption {
  id: string;
  name: string;
}

// 风险预警
export interface RiskAlert {
  id: number;
  account: string;
  type: string;
  level: 'critical' | 'warning';
  msg: string;
  project?: string;
  timestamp?: string;
}

// 资金概览
export interface FundsOverview {
  totalBalance: number;
  availableBalance: number;
  pendingTopups: {
    count: number;
    totalAmount: number;
  };
  recentTransactions?: Array<{
    id: string;
    type: string;
    amount: number;
    timestamp: string;
  }>;
}

export type TimeRange = '7d' | '30d' | '90d' | 'custom';
