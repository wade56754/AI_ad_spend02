/**
 * Finance API Service - 财务模块 API 服务
 *
 * SoT References:
 * - API_SOT.md v9.4 §5.7 (财务 API 契约)
 * - BR-FIN.md v1.1 (财务流程规则)
 * - BR-PROFIT.md v1.2 (利润统计规则)
 * - MASTER.md v4.9 §2.4 (6 角色模型)
 *
 * API 版本说明:
 * - V1 API (/api/v1/fund/*): 已废弃，请迁移到 V2
 * - V2 API (/api/v1/finance/*): 推荐使用
 *
 * @module features/finance/services
 */

import { apiFetch } from '@/lib/api';

// V1 路径 (已废弃 - Deprecated)
// @deprecated 请使用 V2 API: /api/v1/finance/fund/* 和 /api/v1/finance/profit/*
const FUND_BASE_PATH = '/api/v1/fund';
const PROFIT_BASE_PATH = '/api/v1/finance/profit';

// ========== Types ==========

export interface FundOverview {
  // 5 个核心资金指标
  total_topup: number;      // 累计充值
  total_spend: number;      // 累计消耗
  current_balance: number;  // 当前余额
  total_receivable: number; // 应收款
  total_received: number;   // 累计回款
  fund_occupied: number;    // 资金占用
  // 变化指标
  topup_change?: number;    // 充值较上月变化百分比
  spend_change?: number;    // 消耗较上月变化百分比
  balance_change?: number;  // 余额变化百分比
  occupy_rate?: number;     // 资金占用率
  pending_receivable_count?: number; // 待收款笔数
  date_from?: string;
  date_to?: string;
}

export interface ProjectDistribution {
  project_id: number;
  project_name: string;
  total_spend: number;
  total_revenue: number;
  profit: number;
  profit_margin: number;
  percentage: number;
}

export interface ChannelDistribution {
  channel_id?: string;
  channel_name: string;   // API 返回 channel_name
  channel?: string;       // 兼容旧代码
  total_topup: number;
  total_spend: number;
  balance: number;
  account_count: number;
  percentage?: number;    // API 可能不返回，需要前端计算
}

export interface Receivable {
  id: number;
  project_id: number;
  project_name: string;
  client_name: string;
  amount: number;
  due_date: string;
  status: 'pending' | 'overdue' | 'paid';
  days_overdue?: number;
}

export interface Payment {
  id: number;
  project_id: number;
  project_name: string;
  client_name: string;
  amount: number;
  payment_date: string;
  payment_method: string;
}

export interface FundAlertItem {
  alert_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  message: string;
  related_id?: number;
  related_type?: string;
  value?: number;
  threshold?: number;
}

export interface FundAlertsResponse {
  alerts: FundAlertItem[];
  total: number;
  critical_count: number;
  high_count: number;
}

export interface ProfitSummary {
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  profit_margin: number;
  period_start: string;
  period_end: string;
}

export interface ProfitTrendItem {
  date: string;
  revenue: number;
  cost: number;
  profit: number;
}

// ============================================================================
// V1 API Functions (已废弃 - Deprecated)
// 请使用下方 V2 API Functions
// ============================================================================

/**
 * 获取资金概览
 * GET /api/v1/fund/overview
 *
 * @deprecated 请使用 getFundOverviewV2()
 */
export async function getFundOverview(params: {
  period_start?: string;
  period_end?: string;
} = {}): Promise<FundOverview> {
  const searchParams = new URLSearchParams();
  if (params.period_start) searchParams.set('period_start', params.period_start);
  if (params.period_end) searchParams.set('period_end', params.period_end);
  const query = searchParams.toString();
  const url = query ? `${FUND_BASE_PATH}/overview?${query}` : `${FUND_BASE_PATH}/overview`;

  return apiFetch<FundOverview>(url);
}

/**
 * 获取按项目资金分布
 * GET /api/v1/fund/distribution/projects
 *
 * 后端返回分页格式: { items: [...], total, page, page_size, total_pages }
 */
export async function getProjectDistribution(params: {
  period_start?: string;
  period_end?: string;
  top_n?: number;
} = {}): Promise<ProjectDistribution[]> {
  const searchParams = new URLSearchParams();
  if (params.period_start) searchParams.set('period_start', params.period_start);
  if (params.period_end) searchParams.set('period_end', params.period_end);
  if (params.top_n) searchParams.set('top_n', String(params.top_n));
  const query = searchParams.toString();
  const url = query ? `${FUND_BASE_PATH}/distribution/projects?${query}` : `${FUND_BASE_PATH}/distribution/projects`;

  const response = await apiFetch<{ items: ProjectDistribution[] } | ProjectDistribution[]>(url);

  // 处理分页格式响应
  if (response && typeof response === 'object' && 'items' in response) {
    return response.items ?? [];
  }

  // 兼容直接数组格式
  return Array.isArray(response) ? response : [];
}

/**
 * 获取按渠道资金分布
 * GET /api/v1/fund/distribution/channels
 *
 * 后端返回分页格式: { items: [...], total, page, page_size, total_pages }
 */
export async function getChannelDistribution(params: {
  period_start?: string;
  period_end?: string;
} = {}): Promise<ChannelDistribution[]> {
  const searchParams = new URLSearchParams();
  if (params.period_start) searchParams.set('period_start', params.period_start);
  if (params.period_end) searchParams.set('period_end', params.period_end);
  const query = searchParams.toString();
  const url = query ? `${FUND_BASE_PATH}/distribution/channels?${query}` : `${FUND_BASE_PATH}/distribution/channels`;

  const response = await apiFetch<{ items: ChannelDistribution[] } | ChannelDistribution[]>(url);

  // 处理分页格式响应
  if (response && typeof response === 'object' && 'items' in response) {
    return response.items ?? [];
  }

  // 兼容直接数组格式
  return Array.isArray(response) ? response : [];
}

/**
 * 获取应收明细
 * GET /api/v1/fund/receivables
 */
export async function getReceivables(params: {
  status?: 'pending' | 'overdue' | 'paid';
  page?: number;
  page_size?: number;
} = {}): Promise<{ items: Receivable[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set('status', params.status);
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  const query = searchParams.toString();
  const url = query ? `${FUND_BASE_PATH}/receivables?${query}` : `${FUND_BASE_PATH}/receivables`;

  const response = await apiFetch<{
    items: Receivable[];
    meta: { pagination: { total: number } };
  }>(url);

  return {
    items: response.items ?? [],
    total: response.meta?.pagination?.total ?? 0,
  };
}

/**
 * 获取回款记录
 * GET /api/v1/fund/payments
 */
export async function getPayments(params: {
  page?: number;
  page_size?: number;
} = {}): Promise<{ items: Payment[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  const query = searchParams.toString();
  const url = query ? `${FUND_BASE_PATH}/payments?${query}` : `${FUND_BASE_PATH}/payments`;

  const response = await apiFetch<{
    items: Payment[];
    meta: { pagination: { total: number } };
  }>(url);

  return {
    items: response.items ?? [],
    total: response.meta?.pagination?.total ?? 0,
  };
}

/**
 * 获取资金预警
 * GET /api/v1/fund/alerts
 */
export async function getFundAlerts(): Promise<FundAlertsResponse> {
  return apiFetch<FundAlertsResponse>(`${FUND_BASE_PATH}/alerts`);
}

/**
 * 获取利润概览
 * GET /api/v1/profit/summary
 */
export async function getProfitSummary(params: {
  period_start?: string;
  period_end?: string;
} = {}): Promise<ProfitSummary> {
  const searchParams = new URLSearchParams();
  if (params.period_start) searchParams.set('period_start', params.period_start);
  if (params.period_end) searchParams.set('period_end', params.period_end);
  const query = searchParams.toString();
  const url = query ? `${PROFIT_BASE_PATH}/summary?${query}` : `${PROFIT_BASE_PATH}/summary`;

  return apiFetch<ProfitSummary>(url);
}

/**
 * 获取利润趋势
 * GET /api/v1/profit/trend
 */
export async function getProfitTrend(params: {
  period_start?: string;
  period_end?: string;
  granularity?: 'day' | 'week' | 'month';
} = {}): Promise<ProfitTrendItem[]> {
  const searchParams = new URLSearchParams();
  if (params.period_start) searchParams.set('period_start', params.period_start);
  if (params.period_end) searchParams.set('period_end', params.period_end);
  if (params.granularity) searchParams.set('granularity', params.granularity);
  const query = searchParams.toString();
  const url = query ? `${PROFIT_BASE_PATH}/trend?${query}` : `${PROFIT_BASE_PATH}/trend`;

  const response = await apiFetch<{ items: ProfitTrendItem[] } | ProfitTrendItem[]>(url);

  // 处理分页格式响应
  if (response && typeof response === 'object' && 'items' in response) {
    return response.items ?? [];
  }

  // 兼容直接数组格式
  return Array.isArray(response) ? response : [];
}

// ============================================================================
// V2 API Functions (推荐使用 - Recommended)
// 符合 API_SOT.md v9.4 和最佳实践规范
// ============================================================================

import type {
  FundOverviewData,
  FundOverviewParams,
  ReceivablesData,
  ReceivablesParams,
  FundDistributionData,
  FundDistributionParams,
  ProfitOverviewData,
  ProfitOverviewParams,
  ProjectProfitsData,
  ProjectProfitsParams,
  SupplierCostsData,
  SupplierCostsParams,
  ProfitTrendData,
  ProfitTrendParams,
} from '../types/finance.types';

const FUND_V2_PATH = '/api/v1/finance/fund';
const PROFIT_V2_PATH = '/api/v1/finance/profit';

// ---------- 资金总览 V2 API ----------

/**
 * 获取资金概览 V2
 * GET /api/v1/finance/fund/overview
 *
 * 注意: 后端返回扁平结构 (FundOverviewResponse)，需要转换为前端期望的嵌套结构 (FundOverviewData)
 */
export async function getFundOverviewV2(
  params: FundOverviewParams = {}
): Promise<FundOverviewData> {
  const searchParams = new URLSearchParams();
  if (params.period) searchParams.set('period', params.period);
  if (params.date) searchParams.set('date', params.date);
  const query = searchParams.toString();
  const url = query ? `${FUND_V2_PATH}/overview?${query}` : `${FUND_V2_PATH}/overview`;

  // 获取后端原始响应（嵌套结构）
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const raw = await apiFetch<any>(url);

  // 后端返回格式: { period, currency, summary: {...}, changes: {...} }
  // 直接使用后端返回的嵌套结构
  const summary = raw?.summary ?? {};
  const changes = raw?.changes ?? {};

  return {
    period: raw?.period || params.period || params.date || new Date().toISOString().slice(0, 7),
    currency: raw?.currency || 'CNY',
    summary: {
      total_income: summary.total_income ?? 0,
      total_expense: summary.total_expense ?? 0,
      total_receivable: summary.total_receivable ?? 0,
      total_received: summary.total_received ?? 0,
      outstanding: summary.outstanding ?? 0,
      outstanding_count: summary.outstanding_count ?? 0,
      available_balance: summary.available_balance ?? 0,
      opening_balance: summary.opening_balance ?? 0,
    },
    changes: {
      income_change_pct: changes.income_change_pct ?? null,
      expense_change_pct: changes.expense_change_pct ?? null,
      balance_change_pct: changes.balance_change_pct ?? null,
    },
  };
}

/**
 * 获取应收账款明细 V2
 * GET /api/v1/finance/fund/receivables
 */
export async function getReceivablesV2(
  params: ReceivablesParams = {}
): Promise<ReceivablesData> {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set('status', params.status);
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  const query = searchParams.toString();
  const url = query ? `${FUND_V2_PATH}/receivables?${query}` : `${FUND_V2_PATH}/receivables`;
  return apiFetch<ReceivablesData>(url);
}

/**
 * 获取资金分布 V2
 * GET /api/v1/finance/fund/distribution
 */
export async function getFundDistributionV2(
  params: FundDistributionParams = {}
): Promise<FundDistributionData> {
  const searchParams = new URLSearchParams();
  if (params.group_by) searchParams.set('group_by', params.group_by);
  if (params.period) searchParams.set('period', params.period);
  const query = searchParams.toString();
  const url = query ? `${FUND_V2_PATH}/distribution?${query}` : `${FUND_V2_PATH}/distribution`;
  return apiFetch<FundDistributionData>(url);
}

// ---------- 项目盈亏 V2 API ----------

/**
 * 获取盈亏概览 V2
 * GET /api/v1/finance/profit/overview
 *
 * 注意: 后端返回扁平结构 (ProfitOverviewResponse)，需要转换为前端期望的嵌套结构 (ProfitOverviewData)
 */
export async function getProfitOverviewV2(
  params: ProfitOverviewParams = {}
): Promise<ProfitOverviewData> {
  const searchParams = new URLSearchParams();
  if (params.period) searchParams.set('period', params.period);
  const query = searchParams.toString();
  const url = query ? `${PROFIT_V2_PATH}/overview?${query}` : `${PROFIT_V2_PATH}/overview`;

  // 获取后端原始响应（扁平结构）
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const raw = await apiFetch<any>(url);

  // 转换为前端期望格式（嵌套结构）
  return {
    period: params.period || new Date().toISOString().slice(0, 7),
    currency: 'CNY',
    summary: {
      total_revenue: raw?.month_revenue ?? 0,
      total_cost: raw?.month_cost ?? 0,
      total_profit: raw?.month_profit ?? 0,
      total_conversions: 0, // 后端未提供此字段
      avg_profit_rate: (raw?.month_profit_margin ?? 0) / 100, // 后端返回百分比，转为小数
      total_fee: 0, // 后端未提供此字段
    },
    changes: {
      revenue_change_pct: null, // 后端未提供
      profit_change_pct: raw?.profit_change_from_last_month ?? null,
    },
    benchmarks: {
      industry_avg_profit_rate: 0.15, // 默认行业平均利润率 15%
      company_target_profit_rate: 0.20, // 默认公司目标利润率 20%
    },
  };
}

/**
 * 获取项目利润明细 V2
 * GET /api/v1/finance/profit/projects
 */
export async function getProjectProfitsV2(
  params: ProjectProfitsParams = {}
): Promise<ProjectProfitsData> {
  const searchParams = new URLSearchParams();
  if (params.period) searchParams.set('period', params.period);
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.status) searchParams.set('status', params.status);
  const query = searchParams.toString();
  const url = query ? `${PROFIT_V2_PATH}/projects?${query}` : `${PROFIT_V2_PATH}/projects`;
  return apiFetch<ProjectProfitsData>(url);
}

/**
 * 获取渠道成本分析 V2
 * GET /api/v1/finance/profit/suppliers
 */
export async function getSupplierCostsV2(
  params: SupplierCostsParams = {}
): Promise<SupplierCostsData> {
  const searchParams = new URLSearchParams();
  if (params.period) searchParams.set('period', params.period);
  const query = searchParams.toString();
  const url = query ? `${PROFIT_V2_PATH}/suppliers?${query}` : `${PROFIT_V2_PATH}/suppliers`;
  return apiFetch<SupplierCostsData>(url);
}

/**
 * 获取利润趋势 V2
 * GET /api/v1/finance/profit/trend
 */
export async function getProfitTrendV2(
  params: ProfitTrendParams = {}
): Promise<ProfitTrendData> {
  const searchParams = new URLSearchParams();
  if (params.granularity) searchParams.set('granularity', params.granularity);
  if (params.period) searchParams.set('period', params.period);
  const query = searchParams.toString();
  const url = query ? `${PROFIT_V2_PATH}/trend?${query}` : `${PROFIT_V2_PATH}/trend`;
  return apiFetch<ProfitTrendData>(url);
}
