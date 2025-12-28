/**
 * Finance API Service
 *
 * SoT: docs/10.module-specs/A2-fund-overview.md §5 API 接口
 * SoT: LEDGER_SOT.md v1.1 - 账本规则
 *
 * 使用真实后端 API 获取数据
 *
 * @module features/finance/services
 */

import { apiFetch } from '@/lib/api';

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

// ========== Query Functions ==========

/**
 * 获取资金概览
 * GET /api/v1/fund/overview
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
// V2 API - 任务规格重构
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
 */
export async function getFundOverviewV2(
  params: FundOverviewParams = {}
): Promise<FundOverviewData> {
  const searchParams = new URLSearchParams();
  if (params.period) searchParams.set('period', params.period);
  if (params.date) searchParams.set('date', params.date);
  const query = searchParams.toString();
  const url = query ? `${FUND_V2_PATH}/overview?${query}` : `${FUND_V2_PATH}/overview`;
  return apiFetch<FundOverviewData>(url);
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
 */
export async function getProfitOverviewV2(
  params: ProfitOverviewParams = {}
): Promise<ProfitOverviewData> {
  const searchParams = new URLSearchParams();
  if (params.period) searchParams.set('period', params.period);
  const query = searchParams.toString();
  const url = query ? `${PROFIT_V2_PATH}/overview?${query}` : `${PROFIT_V2_PATH}/overview`;
  return apiFetch<ProfitOverviewData>(url);
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
