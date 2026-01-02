/**
 * Ad Spend API Service
 *
 * TanStack Query v5 API 服务层
 *
 * SoT: docs/10.module-specs/C3-spend-detail.md §4 API 接口
 * SoT: MASTER.md v4.4 §4.5.7 - 消耗 SoT = ad_spend_daily.spend
 * SoT: API_SOT.md v9.0
 *
 * 一句话定义: 广告消耗数据获取和导入导出服务
 *
 * 消耗 SoT 约束 (C3-spend-detail.md §1.4):
 *   Phase 1: ad_spend_daily.spend (Excel 导入)
 *   Phase 2: daily_report.real_spend (project_owner/finance 确认)
 *
 * Author: AI 代码工厂 v2.4
 */

import { apiFetch, apiDownload, apiUpload } from '@/lib/api';
import type {
  // AdSpendRecord - exported but not directly used in this file
  AdSpendSummary,
  AdSpendByProject,
  AdSpendByAccount,
  AdSpendListParams,
  AdSpendSummaryParams,
  AdSpendListResponse,
  AdSpendTrendResponse,
} from '../types';

const BASE_PATH = '/api/v1/ad-spend';

// ========== API Functions ==========

/**
 * 获取消耗列表
 * GET /api/v1/ad-spend
 * SoT: C3-spend-detail.md §4.1 接口清单
 * 权限: 登录用户
 */
export async function getAdSpendList(params: AdSpendListParams = {}): Promise<AdSpendListResponse> {
  const searchParams = new URLSearchParams();

  if (params.project_id) searchParams.set('project_id', String(params.project_id));
  if (params.ad_account_id) searchParams.set('ad_account_id', String(params.ad_account_id));
  if (params.channel_id) searchParams.set('channel_id', String(params.channel_id));
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  return apiFetch<AdSpendListResponse>(url);
}

/**
 * 获取消耗汇总统计
 * GET /api/v1/ad-spend/summary
 * SoT: C3-spend-detail.md §4.1 接口清单
 * 权限: 登录用户
 */
export async function getAdSpendSummary(
  params: AdSpendSummaryParams = {}
): Promise<AdSpendSummary> {
  const searchParams = new URLSearchParams();

  if (params.project_id) searchParams.set('project_id', String(params.project_id));
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/summary?${query}` : `${BASE_PATH}/summary`;

  return apiFetch<AdSpendSummary>(url);
}

/**
 * 获取消耗趋势数据
 * GET /api/v1/ad-spend/trend
 * SoT: C3-spend-detail.md §4.1 接口清单
 * 权限: 登录用户
 */
export async function getAdSpendTrend(
  params: AdSpendSummaryParams = {}
): Promise<AdSpendTrendResponse> {
  const searchParams = new URLSearchParams();

  if (params.project_id) searchParams.set('project_id', String(params.project_id));
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/trend?${query}` : `${BASE_PATH}/trend`;

  return apiFetch<AdSpendTrendResponse>(url);
}

/**
 * 获取按项目汇总的消耗
 * GET /api/v1/ad-spend/by-project
 * SoT: C3-spend-detail.md §4.1 接口清单
 * 权限: 登录用户
 */
export async function getAdSpendByProject(
  params: AdSpendSummaryParams = {}
): Promise<AdSpendByProject[]> {
  const searchParams = new URLSearchParams();

  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/by-project?${query}` : `${BASE_PATH}/by-project`;

  return apiFetch<AdSpendByProject[]>(url);
}

/**
 * 获取按账户汇总的消耗
 * GET /api/v1/ad-spend/by-account
 * SoT: C3-spend-detail.md §4.1 接口清单
 * 权限: 登录用户
 */
export async function getAdSpendByAccount(
  params: AdSpendSummaryParams = {}
): Promise<AdSpendByAccount[]> {
  const searchParams = new URLSearchParams();

  if (params.project_id) searchParams.set('project_id', String(params.project_id));
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/by-account?${query}` : `${BASE_PATH}/by-account`;

  return apiFetch<AdSpendByAccount[]>(url);
}

/**
 * 导出消耗数据
 * GET /api/v1/ad-spend/export
 */
export async function exportAdSpend(params: AdSpendListParams = {}): Promise<Blob> {
  const searchParams = new URLSearchParams();

  if (params.project_id) searchParams.set('project_id', String(params.project_id));
  if (params.ad_account_id) searchParams.set('ad_account_id', String(params.ad_account_id));
  if (params.channel_id) searchParams.set('channel_id', String(params.channel_id));
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/export?${query}` : `${BASE_PATH}/export`;

  return apiDownload(url);
}

/**
 * 导入消耗数据
 * POST /api/v1/ad-spend/import
 */
export async function importAdSpend(
  file: File,
  sourcePlatform: string
): Promise<{
  imported_count: number;
  skipped_count: number;
  error_count: number;
  import_job_id: string;
}> {
  return apiUpload(`${BASE_PATH}/import`, file, {
    additionalData: { source_platform: sourcePlatform },
  });
}
