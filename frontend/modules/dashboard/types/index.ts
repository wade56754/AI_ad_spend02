/**
 * Dashboard 模块类型定义
 */

export interface KpiMetric {
  id: string;
  title: string;
  value: string;
  change?: number;
  changeType?: 'up' | 'down' | 'neutral';
  description?: string;
  icon: React.ComponentType<{ className?: string }>;
  color: 'primary' | 'success' | 'warning' | 'error' | 'info';
  priority?: 'primary' | 'secondary'; // 区分主要指标和次要指标
}

export interface TrendChartData {
  date: string;
  spend: number;
  roi: number;
}

export interface RiskAlert {
  id: number;
  account: string;
  type: string;
  level: 'critical' | 'warning';
  msg: string;
  project?: string;
  timestamp?: string;
}

export interface TodoTask {
  id: string;
  title: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'completed';
  assignee: string;
  project?: string;
  dueTime: string;
  relatedEntityType?: 'daily_report' | 'topup_request' | 'reconciliation';
}

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

