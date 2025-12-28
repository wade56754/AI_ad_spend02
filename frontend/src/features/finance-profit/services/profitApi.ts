/**
 * Finance Profit API Service
 *
 * SoT: docs/10.module-specs/A3-project-pnl.md §5 API 接口
 * SoT: MASTER.md v4.4 §6.5 页面 3 项目盈亏字段集
 * SoT: BUSINESS_RULES.md v3.2: 利润计算公式
 *   - revenue = conversions_final × unit_price
 *   - cost = real_spend + fee
 *   - profit = revenue - cost
 *   - profit_margin = profit / revenue × 100
 *
 * 使用真实后端 API 获取数据
 *
 * @module features/finance-profit/services
 */

import { apiFetch } from '@/lib/api';
import type {
  ProfitSummaryResponse,
  ProfitByProjectResponse,
  ProfitByAccountResponse,
  ProfitByChannelResponse,
  ProfitTrendResponse,
  ProfitCompareResponse,
  ProfitOverviewResponse,
  ProfitSummaryParams,
  ProfitByDimensionParams,
  ProfitTrendParams,
  ProfitCompareParams,
} from '../types/profit.types';

const BASE_PATH = '/api/v1/finance/profit';

// ========== Query Functions ==========

/**
 * Get profit summary
 * GET /api/v1/finance/profit/summary
 * SoT: A3-project-pnl.md §5.1
 *
 * @param params.year - 年份 (2020-2099)
 * @param params.month - 月份 (1-12)
 */
export async function getProfitSummary(
  params: ProfitSummaryParams
): Promise<ProfitSummaryResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set('year', String(params.year));
  searchParams.set('month', String(params.month));
  const url = `${BASE_PATH}/summary?${searchParams.toString()}`;
  return apiFetch<ProfitSummaryResponse>(url);
}

/**
 * Get profit overview
 * GET /api/v1/finance/profit/overview
 * SoT: A3-project-pnl.md §5.1
 */
export async function getProfitOverview(): Promise<ProfitOverviewResponse> {
  return apiFetch<ProfitOverviewResponse>(`${BASE_PATH}/overview`);
}

/**
 * Get profit by project
 * GET /api/v1/finance/profit/by-project
 * SoT: A3-project-pnl.md §5.1
 */
export async function getProfitByProject(
  params: ProfitByDimensionParams = {}
): Promise<ProfitByProjectResponse> {
  const searchParams = new URLSearchParams();
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.limit) searchParams.set('limit', String(params.limit));
  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/by-project?${query}` : `${BASE_PATH}/by-project`;
  return apiFetch<ProfitByProjectResponse>(url);
}

/**
 * Get profit by account
 * GET /api/v1/finance/profit/by-account
 * SoT: A3-project-pnl.md §5.1
 */
export async function getProfitByAccount(
  params: ProfitByDimensionParams = {}
): Promise<ProfitByAccountResponse> {
  const searchParams = new URLSearchParams();
  if (params.project_id) searchParams.set('project_id', String(params.project_id));
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.limit) searchParams.set('limit', String(params.limit));
  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/by-account?${query}` : `${BASE_PATH}/by-account`;
  return apiFetch<ProfitByAccountResponse>(url);
}

/**
 * Get profit by channel
 * GET /api/v1/finance/profit/by-channel
 * SoT: A3-project-pnl.md §5.1
 */
export async function getProfitByChannel(
  params: ProfitByDimensionParams = {}
): Promise<ProfitByChannelResponse> {
  const searchParams = new URLSearchParams();
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.limit) searchParams.set('limit', String(params.limit));
  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/by-channel?${query}` : `${BASE_PATH}/by-channel`;
  return apiFetch<ProfitByChannelResponse>(url);
}

/**
 * Get profit trend
 * GET /api/v1/finance/profit/trend
 * SoT: A3-project-pnl.md §5.1
 */
export async function getProfitTrend(
  params: ProfitTrendParams = {}
): Promise<ProfitTrendResponse> {
  const searchParams = new URLSearchParams();
  if (params.project_id) searchParams.set('project_id', String(params.project_id));
  if (params.channel_id) searchParams.set('channel_id', String(params.channel_id));
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.granularity) searchParams.set('granularity', params.granularity);
  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/trend?${query}` : `${BASE_PATH}/trend`;
  return apiFetch<ProfitTrendResponse>(url);
}

/**
 * Compare profit across projects
 * POST /api/v1/finance/profit/compare
 * SoT: A3-project-pnl.md §5.1
 */
export async function compareProfits(
  params: ProfitCompareParams
): Promise<ProfitCompareResponse> {
  const searchParams = new URLSearchParams();
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/compare?${query}` : `${BASE_PATH}/compare`;
  return apiFetch<ProfitCompareResponse>(url, {
    method: 'POST',
    body: { project_ids: params.project_ids },
  });
}
