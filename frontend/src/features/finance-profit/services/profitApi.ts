/**
 * Finance Profit API Service
 *
 * SoT 对齐:
 * - BUSINESS_RULES.md v3.1: 利润计算公式
 * - backend/routers/finance_profit.py
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
  TrendGranularity,
} from '../types/profit.types';

const BASE_PATH = '/api/v1/finance/profit';

// ========== Query Functions ==========

/**
 * Get profit summary
 * GET /api/v1/finance/profit/summary
 */
export async function getProfitSummary(
  params: ProfitSummaryParams = {}
): Promise<ProfitSummaryResponse> {
  const searchParams = new URLSearchParams();

  if (params.project_id) searchParams.set('project_id', String(params.project_id));
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/summary?${query}` : `${BASE_PATH}/summary`;

  return apiFetch<ProfitSummaryResponse>(url);
}

/**
 * Get profit overview
 * GET /api/v1/finance/profit/overview
 */
export async function getProfitOverview(): Promise<ProfitOverviewResponse> {
  return apiFetch<ProfitOverviewResponse>(`${BASE_PATH}/overview`);
}

/**
 * Get profit by project
 * GET /api/v1/finance/profit/by-project
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
