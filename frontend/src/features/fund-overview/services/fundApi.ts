/**
 * Fund Overview API Service
 *
 * SoT: docs/10.module-specs/A2-fund-overview.md §5 API 接口
 * SoT: MASTER.md v4.4 §4.5.5 资金口径定义
 * SoT: MASTER.md v4.4 §6.5 页面 2 资金总览字段集
 *
 * 一句话定义: 资金总览数据获取服务
 *
 * @module features/fund-overview/services
 */

import { apiFetch } from '@/lib/api';
import type {
  FundOverview,
  FundOverviewResponse,
  FundOverviewParams,
  FundByProjectResponse,
  FundByChannelResponse,
  FundDistributionParams,
  ReceivablesResponse,
  PaymentsResponse,
} from '../types';

const BASE_PATH = '/api/v1/fund';

// ========== Query Functions ==========

/**
 * 获取资金概览
 * GET /api/v1/fund/overview
 * SoT: A2-fund-overview.md §5.2
 *
 * @param params - 查询参数（可选日期范围）
 * @returns 资金概览数据
 */
export async function getFundOverview(params: FundOverviewParams = {}): Promise<FundOverview> {
  const searchParams = new URLSearchParams();

  if (params.date_from) searchParams.set('date_from', params.date_from);
  if (params.date_to) searchParams.set('date_to', params.date_to);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/overview?${query}` : `${BASE_PATH}/overview`;

  const response = await apiFetch<FundOverviewResponse>(url);
  return response.data;
}

/**
 * 获取资金分布（按项目）
 * GET /api/v1/fund/distribution/projects
 * SoT: A2-fund-overview.md §5.2
 *
 * @param params - 分页和排序参数
 * @returns 按项目的资金分布列表
 */
export async function getFundByProject(
  params: FundDistributionParams = {}
): Promise<FundByProjectResponse> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.order) searchParams.set('order', params.order);

  const query = searchParams.toString();
  const url = query
    ? `${BASE_PATH}/distribution/projects?${query}`
    : `${BASE_PATH}/distribution/projects`;

  return apiFetch<FundByProjectResponse>(url);
}

/**
 * 获取资金分布（按渠道）
 * GET /api/v1/fund/distribution/channels
 * SoT: A2-fund-overview.md §5.2
 *
 * @param params - 分页和排序参数
 * @returns 按渠道的资金分布列表
 */
export async function getFundByChannel(
  params: FundDistributionParams = {}
): Promise<FundByChannelResponse> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.order) searchParams.set('order', params.order);

  const query = searchParams.toString();
  const url = query
    ? `${BASE_PATH}/distribution/channels?${query}`
    : `${BASE_PATH}/distribution/channels`;

  return apiFetch<FundByChannelResponse>(url);
}

/**
 * 获取应收款列表
 * GET /api/v1/fund/receivables
 * SoT: A2-fund-overview.md §5.1
 *
 * @returns 应收款明细列表
 */
export async function getReceivables(): Promise<ReceivablesResponse> {
  return apiFetch<ReceivablesResponse>(`${BASE_PATH}/receivables`);
}

/**
 * 获取回款记录
 * GET /api/v1/fund/payments
 * SoT: A2-fund-overview.md §5.1
 *
 * @returns 回款记录列表
 */
export async function getPayments(): Promise<PaymentsResponse> {
  return apiFetch<PaymentsResponse>(`${BASE_PATH}/payments`);
}
