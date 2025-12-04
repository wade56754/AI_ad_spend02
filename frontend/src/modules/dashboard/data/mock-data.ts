/**
 * Dashboard Mock 数据
 *
 * 模拟后端 API 返回结构，便于未来无缝对接
 * 数据结构参考 daily_reports / finance_profit 业务模型
 */

import type {
  KpiMetric,
  TrendChartData,
  TodoTask,
  ProjectOption,
  DashboardData
} from '../types';

// 项目列表 mock
export const mockProjects: ProjectOption[] = [
  { id: 'all', name: '全部项目' },
  { id: 'proj-001', name: 'ABC公司Q4投放' },
  { id: 'proj-002', name: 'XYZ科技推广' },
  { id: 'proj-003', name: 'DEF品牌营销' },
  { id: 'proj-004', name: 'GHI电商活动' },
];

// KPI 指标 mock
export const mockKpiMetrics: KpiMetric[] = [
  {
    id: 'spend_today',
    title: '今日消耗',
    value: '¥12,845',
    change: 8.2,
    changeType: 'up',
    description: '相比昨日',
    icon: 'DollarSign',
    color: 'primary'
  },
  {
    id: 'active_projects',
    title: '活跃项目',
    value: '24',
    change: 3,
    changeType: 'up',
    description: '本周新增',
    icon: 'Target',
    color: 'success'
  },
  {
    id: 'roi',
    title: 'ROI',
    value: '3.24',
    change: 4.6,
    changeType: 'up',
    description: '投资回报率',
    icon: 'TrendingUp',
    color: 'info'
  },
  {
    id: 'pending_reports',
    title: '待审日报',
    value: '18',
    change: -5,
    changeType: 'down',
    description: '需要审核',
    icon: 'FileText',
    color: 'warning'
  }
];

// 消耗趋势 mock（7天）
export const mockSpendTrend: TrendChartData = {
  title: '消耗趋势',
  description: '近7天投放消耗',
  trend: {
    value: 12.5,
    isPositive: true
  },
  dataPoints: [
    { label: '11-27', value: 65 },
    { label: '11-28', value: 72 },
    { label: '11-29', value: 58 },
    { label: '11-30', value: 80 },
    { label: '12-01', value: 75 },
    { label: '12-02', value: 88 },
    { label: '12-03', value: 92 }
  ]
};

// ROI 趋势 mock
export const mockRoiTrend: TrendChartData = {
  title: 'ROI 趋势',
  description: '近7天投资回报率',
  trend: {
    value: 5.2,
    isPositive: true
  },
  dataPoints: [
    { label: '11-27', value: 45 },
    { label: '11-28', value: 52 },
    { label: '11-29', value: 48 },
    { label: '11-30', value: 60 },
    { label: '12-01', value: 55 },
    { label: '12-02', value: 68 },
    { label: '12-03', value: 72 }
  ]
};

// 待办任务 mock（对齐 daily_report 状态流转）
export const mockTodoTasks: TodoTask[] = [
  {
    id: 'task-001',
    title: '审核5个项目的日报',
    priority: 'high',
    status: 'pending',
    assignee: '张数据员',
    project: 'ABC公司Q4项目',
    dueTime: '14:00',
    relatedEntityType: 'daily_report'
  },
  {
    id: 'task-002',
    title: '处理3个充值申请',
    priority: 'medium',
    status: 'pending',
    assignee: '李财务',
    project: 'XYZ科技投放',
    dueTime: '16:00',
    relatedEntityType: 'topup_request'
  },
  {
    id: 'task-003',
    title: '跟进异常账户处理',
    priority: 'high',
    status: 'in_progress',
    assignee: '王户管',
    project: 'DEF品牌推广',
    dueTime: '15:00'
  },
  {
    id: 'task-004',
    title: '生成月度ROI报告',
    priority: 'low',
    status: 'pending',
    assignee: '赵经理',
    project: 'GHI电商活动',
    dueTime: '18:00'
  },
  {
    id: 'task-005',
    title: '完成对账单确认',
    priority: 'medium',
    status: 'completed',
    assignee: '钱投手',
    dueTime: '13:00',
    relatedEntityType: 'reconciliation'
  }
];

// 完整 Dashboard 数据
export const mockDashboardData: DashboardData = {
  kpiMetrics: mockKpiMetrics,
  spendTrend: mockSpendTrend,
  roiTrend: mockRoiTrend,
  todoTasks: mockTodoTasks,
  lastUpdated: new Date().toISOString()
};

// 模拟 API 调用延迟
export async function fetchDashboardData(): Promise<DashboardData> {
  await new Promise(resolve => setTimeout(resolve, 800));
  return mockDashboardData;
}

export async function fetchProjects(): Promise<ProjectOption[]> {
  await new Promise(resolve => setTimeout(resolve, 300));
  return mockProjects;
}
