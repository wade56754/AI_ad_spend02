/**
 * Finance Helper Functions
 *
 * 从 FinancePage.tsx 提取的辅助函数和配置
 */

import {
  CreditCard,
  FileText,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react';

// 格式化金额
export const formatMoney = (amount: number | undefined | null): string => {
  const num = Number(amount) || 0;
  if (Math.abs(num) >= 10000) {
    return `¥${(num / 10000).toFixed(2)} 万`;
  }
  return `¥${num.toLocaleString()}`;
};

// 待办类型配置
export type TodoType = 'topup' | 'settlement' | 'reconciliation' | 'alert';

export const todoConfig: Record<TodoType, {
  icon: typeof CreditCard;
  color: string;
  bg: string;
}> = {
  topup: { icon: CreditCard, color: 'text-blue-600', bg: 'bg-blue-100' },
  settlement: { icon: FileText, color: 'text-purple-600', bg: 'bg-purple-100' },
  reconciliation: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100' },
  alert: { icon: AlertTriangle, color: 'text-orange-600', bg: 'bg-orange-100' },
};

// 优先级颜色
export type Priority = 'high' | 'medium' | 'low';

export const priorityColors: Record<Priority, string> = {
  high: 'bg-red-100 text-red-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-gray-100 text-gray-800',
};

export const priorityLabels: Record<Priority, string> = {
  high: '紧急',
  medium: '一般',
  low: '低',
};

// 交易类型配置
export type TransactionType = 'topup' | 'consume' | 'settlement' | 'refund';

export const transactionTypeConfig: Record<TransactionType, {
  label: string;
  className: string;
}> = {
  topup: { label: '充值', className: 'bg-green-100 text-green-800' },
  consume: { label: '消耗', className: 'bg-blue-100 text-blue-800' },
  settlement: { label: '结算', className: 'bg-purple-100 text-purple-800' },
  refund: { label: '退款', className: 'bg-gray-100 text-gray-800' },
};

// 类型定义
export interface FinanceOverview {
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  profit_margin: number;
  pending_settlements: number;
  pending_topups: number;
}

export interface TrendDataPoint {
  date: string;
  revenue: number;
  cost: number;
  profit: number;
}

export interface PlatformSpend {
  platform: string;
  spend: number;
  percentage: number;
  trend: 'up' | 'stable' | 'down';
}

export interface FinanceTodo {
  id: number;
  type: TodoType;
  title: string;
  amount?: number;
  priority: Priority;
  created_at: string;
}

export interface LowBalanceAccount {
  id: number;
  name: string;
  platform: string;
  balance: number;
  status: 'critical' | 'low';
}

export interface Transaction {
  id: number;
  type: TransactionType;
  account_name: string;
  amount: number;
  status: string;
  created_at: string;
}
