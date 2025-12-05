/**
 * Dashboard Mock 数据
 */

import { Wallet, CheckCircle2, TrendingUp, AlertTriangle } from 'lucide-react';
import type { KpiMetric, TrendChartData, RiskAlert, TodoTask, FundsOverview } from '../types';

// 图表数据
export const MOCK_CHART_DATA: TrendChartData[] = [
  { date: '11-27', spend: 1200, roi: 1.8 },
  { date: '11-28', spend: 1800, roi: 2.1 },
  { date: '11-29', spend: 1600, roi: 2.4 },
  { date: '11-30', spend: 2200, roi: 3.2 },
  { date: '12-01', spend: 2100, roi: 3.1 },
  { date: '12-02', spend: 1950, roi: 2.8 },
  { date: '12-03', spend: 2400, roi: 3.4 },
];

// 风险预警数据
export const MOCK_ALERTS: RiskAlert[] = [
  { 
    id: 1, 
    account: 'FB_Acc_092', 
    type: '余额不足', 
    level: 'critical', 
    msg: '余额 < $50，已暂停',
    project: 'ABC公司Q4项目',
    timestamp: '2024-12-03 10:30'
  },
  { 
    id: 2, 
    account: 'Google_Ads_11', 
    type: 'ROI异常', 
    level: 'warning', 
    msg: '今日 ROI 0.5 (跌幅 80%)',
    project: 'XYZ科技投放',
    timestamp: '2024-12-03 09:15'
  },
  { 
    id: 3, 
    account: 'FB_Acc_104', 
    type: '账户被封', 
    level: 'critical', 
    msg: '检测到 Policy Violation',
    project: 'DEF品牌推广',
    timestamp: '2024-12-03 08:00'
  },
];

// KPI 指标数据（区分 Primary 和 Secondary）
export const MOCK_KPI_METRICS: KpiMetric[] = [
  {
    id: 'spend_today',
    title: '今日总消耗',
    value: '$12,845',
    change: 8.2,
    changeType: 'up',
    description: '相比昨日',
    icon: Wallet,
    color: 'primary',
    priority: 'primary' // 主要指标
  },
  {
    id: 'roi',
    title: '整体 ROI',
    value: '3.24',
    change: 4.6,
    changeType: 'up',
    description: '投资回报率',
    icon: TrendingUp,
    color: 'info',
    priority: 'primary' // 主要指标
  },
  {
    id: 'active_projects',
    title: '活跃项目数',
    value: '24',
    change: 3,
    changeType: 'up',
    description: '个新立项',
    icon: CheckCircle2,
    color: 'success',
    priority: 'secondary' // 次要指标
  },
  {
    id: 'pending_reports',
    title: '待审日报',
    value: '18',
    change: -5,
    changeType: 'down',
    description: '需优先处理',
    icon: AlertTriangle,
    color: 'warning',
    priority: 'secondary' // 次要指标，但需要高亮
  }
];

// 今日待办数据
export const MOCK_TODO_TASKS: TodoTask[] = [
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
    title: '跟进异常账户解封',
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

// 资金概览数据
export const MOCK_FUNDS_OVERVIEW: FundsOverview = {
  totalBalance: 1234567,
  availableBalance: 987654,
  pendingTopups: {
    count: 3,
    totalAmount: 50000
  },
  recentTransactions: [
    { id: 'tx-001', type: '充值', amount: 100000, timestamp: '2024-12-03 10:00' },
    { id: 'tx-002', type: '消耗', amount: -50000, timestamp: '2024-12-03 09:30' }
  ]
};
