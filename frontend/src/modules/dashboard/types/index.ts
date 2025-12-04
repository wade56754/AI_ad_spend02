/**
 * Dashboard 模块类型定义
 *
 * 结构设计为未来对接 daily_reports / finance_profit API 预留
 */

// 筛选器状态
export interface DashboardFilters {
  dateRange: 'today' | '7d' | '30d' | 'custom';
  projectId?: string;
  startDate?: string;
  endDate?: string;
}

// KPI 指标数据
export interface KpiMetric {
  id: string;
  title: string;
  value: string | number;
  change: number;
  changeType: 'up' | 'down' | 'neutral';
  description?: string;
  icon: string;
  color: 'primary' | 'success' | 'warning' | 'error' | 'info';
}

// 趋势数据点
export interface TrendDataPoint {
  label: string;
  value: number;
  date?: string;
}

// 趋势图表数据
export interface TrendChartData {
  title: string;
  description?: string;
  trend: {
    value: number;
    isPositive: boolean;
  };
  dataPoints: TrendDataPoint[];
}

// 待办任务（对齐 daily_reports 状态机）
export interface TodoTask {
  id: string;
  title: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'completed';
  assignee?: string;
  project?: string;
  dueTime?: string;
  // 未来可扩展：关联 daily_report_id
  relatedEntityType?: 'daily_report' | 'topup_request' | 'reconciliation';
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
