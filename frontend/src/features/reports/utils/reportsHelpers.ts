/**
 * Reports Helper Functions
 *
 * 从 ReportsPage.tsx 提取的工具函数
 */

/**
 * 格式化货币显示
 */
export const formatCurrency = (value: number | string): string => {
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(numValue);
};

/**
 * 格式化百分比
 */
export const formatPercent = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '-';
  return `${value.toFixed(1)}%`;
};

/**
 * 报表标签页类型
 */
export type ReportTab = 'dashboard' | 'performance' | 'profit' | 'reconciliation' | 'financial';

/**
 * 日期范围类型
 */
export interface DateRange {
  start_date?: string;
  end_date?: string;
}
