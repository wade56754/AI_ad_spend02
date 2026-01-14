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

// 格式化金额（人民币）
export const formatMoney = (amount: number | undefined | null): string => {
  const num = Number(amount) || 0;
  if (Math.abs(num) >= 10000) {
    return `¥${(num / 10000).toFixed(2)} 万`;
  }
  return `¥${num.toLocaleString()}`;
};

/**
 * 格式化货币金额
 * 使用 Intl.NumberFormat 提供标准格式
 *
 * @param value 金额数值
 * @param currency 货币类型：'CNY' | 'USD'，默认 'USD'
 * @returns 格式化后的字符串，如 "$1,234.56" 或 "¥1,234.56"
 */
export function formatCurrency(
  value: number | undefined | null,
  currency: 'CNY' | 'USD' = 'USD'
): string {
  const num = Number(value) || 0;
  return new Intl.NumberFormat(currency === 'CNY' ? 'zh-CN' : 'en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(num);
}

/**
 * 格式化简洁货币金额（用于图表等空间有限的地方）
 * 自动转换为 K/M 等单位
 *
 * @param value 金额数值
 * @param currency 货币类型
 * @returns 格式化后的字符串，如 "$1.2k" 或 "$1.5M"
 */
export function formatCurrencyCompact(
  value: number | undefined | null,
  currency: 'CNY' | 'USD' = 'USD'
): string {
  const num = Number(value) || 0;
  const symbol = currency === 'CNY' ? '¥' : '$';

  if (Math.abs(num) >= 1000000) {
    return `${symbol}${(num / 1000000).toFixed(1)}M`;
  }
  if (Math.abs(num) >= 1000) {
    return `${symbol}${(num / 1000).toFixed(0)}k`;
  }
  return `${symbol}${num.toFixed(0)}`;
}

/**
 * 格式化百分比
 *
 * @param value 小数值（如 0.15 表示 15%）
 * @param decimals 小数位数，默认 1
 * @returns 格式化后的字符串，如 "15.0%"
 */
export function formatPercent(
  value: number | undefined | null,
  decimals: number = 1
): string {
  const num = Number(value) || 0;
  return `${(num * 100).toFixed(decimals)}%`;
}

/**
 * 格式化变化百分比（带正负号）
 *
 * @param value 变化百分比值
 * @returns 格式化后的字符串，如 "+15.0%" 或 "-5.0%" 或 "-"
 */
export function formatChange(value: number | undefined | null): string {
  if (value === null || value === undefined) return '-';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
}

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
