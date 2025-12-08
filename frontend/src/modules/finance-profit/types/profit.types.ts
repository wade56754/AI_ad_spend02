/**
 * Finance Profit Types - 财务利润类型定义
 *
 * SoT 对齐:
 * - BUSINESS_RULES.md v3.1: 利润计算公式
 *   - revenue = conversions_final × unit_price
 *   - cost = real_spend + fee
 *   - profit = revenue - cost
 *   - profit_margin = profit / revenue × 100
 * - backend/schemas/finance.py
 */

// ========== 枚举 ==========

export enum ProfitDimension {
  PROJECT = 'project',
  ACCOUNT = 'account',
  CHANNEL = 'channel',
  DATE = 'date',
}

export enum TrendGranularity {
  DAILY = 'daily',
  WEEKLY = 'weekly',
  MONTHLY = 'monthly',
}

// ========== 基础项接口 ==========

export interface ProfitSummaryItem {
  report_date: string;
  project_id: number;
  project_name: string;
  conversions_final: number;
  unit_price: number;
  revenue: number;
  real_spend: number;
  fee: number;
  cost: number;
  profit: number;
  profit_margin: number;
}

export interface ProfitByProjectItem {
  project_id: number;
  project_name: string;
  total_conversions: number;
  avg_unit_price: number;
  total_revenue: number;
  total_spend: number;
  total_fee: number;
  total_cost: number;
  total_profit: number;
  profit_margin: number;
  report_count: number;
}

export interface ProfitByAccountItem {
  ad_account_id: number;
  account_name: string;
  project_id: number;
  project_name: string;
  total_conversions: number;
  total_revenue: number;
  total_spend: number;
  total_cost: number;
  total_profit: number;
  profit_margin: number;
}

export interface ProfitByChannelItem {
  channel_id: number;
  channel_name: string;
  total_accounts: number;
  total_conversions: number;
  total_revenue: number;
  total_spend: number;
  total_cost: number;
  total_profit: number;
  profit_margin: number;
}

export interface ProfitTrendItem {
  period: string;
  period_start: string;
  period_end: string;
  total_conversions: number;
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  profit_margin: number;
  profit_change: number | null;
  profit_change_rate: number | null;
}

export interface ProfitCompareItem {
  project_id: number;
  project_name: string;
  total_conversions: number;
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  profit_margin: number;
  rank_by_profit: number;
  rank_by_margin: number;
}

// ========== 响应接口 ==========

export interface ProfitSummaryResponse {
  items: ProfitSummaryItem[];
  total_conversions: number;
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  overall_profit_margin: number;
}

export interface ProfitByProjectResponse {
  items: ProfitByProjectItem[];
  total_projects: number;
  total_conversions: number;
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  overall_profit_margin: number;
}

export interface ProfitByAccountResponse {
  items: ProfitByAccountItem[];
  total_accounts: number;
  total_conversions: number;
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  overall_profit_margin: number;
}

export interface ProfitByChannelResponse {
  items: ProfitByChannelItem[];
  total_channels: number;
  total_conversions: number;
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  overall_profit_margin: number;
}

export interface ProfitTrendResponse {
  items: ProfitTrendItem[];
  granularity: string;
  period_count: number;
  avg_profit: number;
  max_profit: number;
  min_profit: number;
  profit_volatility: number;
}

export interface ProfitCompareResponse {
  items: ProfitCompareItem[];
  compare_count: number;
  best_profit_project: string | null;
  best_margin_project: string | null;
  total_profit: number;
  avg_profit_margin: number;
}

export interface ProfitOverviewResponse {
  // 今日数据
  today_revenue: number;
  today_cost: number;
  today_profit: number;
  today_profit_margin: number;
  // 本周数据
  week_revenue: number;
  week_cost: number;
  week_profit: number;
  week_profit_margin: number;
  // 本月数据
  month_revenue: number;
  month_cost: number;
  month_profit: number;
  month_profit_margin: number;
  // 环比变化
  profit_change_from_yesterday: number | null;
  profit_change_from_last_week: number | null;
  profit_change_from_last_month: number | null;
  // Top 项目
  top_profit_projects: Array<{
    project_id: number;
    project_name: string;
    total_profit: number;
    profit_margin: number;
  }>;
}

// ========== 请求参数接口 ==========

export interface ProfitSummaryParams {
  project_id?: number;
  start_date?: string;
  end_date?: string;
}

export interface ProfitByDimensionParams {
  project_id?: number;
  channel_id?: number;
  start_date?: string;
  end_date?: string;
  limit?: number;
}

export interface ProfitTrendParams {
  project_id?: number;
  channel_id?: number;
  start_date?: string;
  end_date?: string;
  granularity?: TrendGranularity;
}

export interface ProfitCompareParams {
  project_ids: number[];
  start_date?: string;
  end_date?: string;
}

// ========== UI 配置 ==========

export const TREND_GRANULARITY_CONFIG: Record<TrendGranularity, {
  label: string;
  description: string;
}> = {
  [TrendGranularity.DAILY]: {
    label: '按日',
    description: '每日利润趋势',
  },
  [TrendGranularity.WEEKLY]: {
    label: '按周',
    description: '每周利润趋势',
  },
  [TrendGranularity.MONTHLY]: {
    label: '按月',
    description: '每月利润趋势',
  },
};

export const PROFIT_DIMENSION_CONFIG: Record<ProfitDimension, {
  label: string;
  icon: string;
}> = {
  [ProfitDimension.PROJECT]: {
    label: '按项目',
    icon: 'folder',
  },
  [ProfitDimension.ACCOUNT]: {
    label: '按账户',
    icon: 'user',
  },
  [ProfitDimension.CHANNEL]: {
    label: '按渠道',
    icon: 'share2',
  },
  [ProfitDimension.DATE]: {
    label: '按日期',
    icon: 'calendar',
  },
};
