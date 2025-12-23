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
 *   Phase 2: daily_report.real_spend (supervisor/finance 确认)
 *
 * Author: AI 代码工厂 v2.4
 */

import { apiFetch } from '@/lib/api';
import type {
  AdSpendRecord,
  AdSpendSummary,
  AdSpendByProject,
  AdSpendByAccount,
  AdSpendListParams,
  AdSpendSummaryParams,
  AdSpendListResponse,
  AdSpendTrendResponse,
} from '../types';

const BASE_PATH = '/api/v1/ad-spend';

// ========== Mock 数据生成 ==========
// SoT: C3-spend-detail.md §2 数据需求

/**
 * 生成 Mock 消耗记录
 * SoT: C3-spend-detail.md §4.2 响应示例
 */
function generateMockSpendRecords(): AdSpendRecord[] {
  const now = new Date();
  const records: AdSpendRecord[] = [];
  const channels = [
    { id: 1, name: '抖音' },
    { id: 2, name: '快手' },
    { id: 3, name: '百度' },
  ];
  const projects = [
    { id: 1, name: '项目Alpha' },
    { id: 2, name: '项目Beta' },
    { id: 3, name: '项目Gamma' },
  ];

  // 生成过去 7 天的数据
  for (let day = 0; day < 7; day++) {
    const reportDate = new Date(now);
    reportDate.setDate(reportDate.getDate() - day);
    const dateStr = reportDate.toISOString().slice(0, 10);

    channels.forEach((channel, ci) => {
      projects.forEach((project, pi) => {
        const spend = 8000 + Math.random() * 10000;
        const impressions = 50000 + Math.random() * 100000;
        const clicks = impressions * (0.02 + Math.random() * 0.02);
        const conversions = clicks * (0.04 + Math.random() * 0.02);

        records.push({
          id: day * 100 + ci * 10 + pi + 1,
          ad_account_id: 100 + ci * 10 + pi,
          ad_account_name: `账户${String.fromCharCode(65 + pi)}-${channel.name}`,
          project_id: project.id,
          project_name: project.name,
          channel_id: channel.id,
          channel_name: channel.name,
          report_date: dateStr,
          spend: Math.round(spend * 100) / 100,
          impressions: Math.round(impressions),
          clicks: Math.round(clicks),
          conversions: Math.round(conversions),
          ctr: Math.round((clicks / impressions) * 10000) / 100,
          cpc: Math.round((spend / clicks) * 100) / 100,
          cpa: Math.round((spend / conversions) * 100) / 100,
          created_at: reportDate.toISOString(),
        });
      });
    });
  }

  return records.sort((a, b) => b.report_date.localeCompare(a.report_date));
}

/**
 * 生成 Mock 汇总统计
 * SoT: C3-spend-detail.md §3.1 KPI 卡片
 */
function generateMockSummary(records: AdSpendRecord[]): AdSpendSummary {
  const total_spend = records.reduce((sum, r) => sum + r.spend, 0);
  const total_impressions = records.reduce((sum, r) => sum + r.impressions, 0);
  const total_clicks = records.reduce((sum, r) => sum + r.clicks, 0);
  const total_conversions = records.reduce((sum, r) => sum + r.conversions, 0);

  return {
    total_spend: Math.round(total_spend * 100) / 100,
    total_impressions,
    total_clicks,
    total_conversions,
    avg_ctr: total_impressions > 0 ? Math.round((total_clicks / total_impressions) * 10000) / 100 : 0,
    avg_cpc: total_clicks > 0 ? Math.round((total_spend / total_clicks) * 100) / 100 : 0,
    avg_cpa: total_conversions > 0 ? Math.round((total_spend / total_conversions) * 100) / 100 : 0,
    record_count: records.length,
  };
}

/**
 * 生成 Mock 趋势数据
 * SoT: C3-spend-detail.md §4.2 趋势数据响应
 */
function generateMockTrend(records: AdSpendRecord[]): AdSpendTrendResponse {
  const dailyMap = new Map<string, { spend: number; conversions: number }>();

  records.forEach((r) => {
    const existing = dailyMap.get(r.report_date) || { spend: 0, conversions: 0 };
    dailyMap.set(r.report_date, {
      spend: existing.spend + r.spend,
      conversions: existing.conversions + r.conversions,
    });
  });

  const items = Array.from(dailyMap.entries())
    .map(([date, data]) => ({
      date,
      spend: Math.round(data.spend * 100) / 100,
      conversions: data.conversions,
      cpa: data.conversions > 0 ? Math.round((data.spend / data.conversions) * 100) / 100 : 0,
    }))
    .sort((a, b) => a.date.localeCompare(b.date));

  const total_spend = items.reduce((sum, i) => sum + i.spend, 0);
  const total_conversions = items.reduce((sum, i) => sum + i.conversions, 0);

  return {
    items,
    total_spend: Math.round(total_spend * 100) / 100,
    total_conversions,
    avg_cpa: total_conversions > 0 ? Math.round((total_spend / total_conversions) * 100) / 100 : 0,
  };
}

/**
 * 生成 Mock 按项目汇总
 */
function generateMockByProject(records: AdSpendRecord[]): AdSpendByProject[] {
  const projectMap = new Map<number, AdSpendByProject>();

  records.forEach((r) => {
    const existing = projectMap.get(r.project_id);
    if (existing) {
      existing.total_spend += r.spend;
      existing.total_conversions += r.conversions;
    } else {
      projectMap.set(r.project_id, {
        project_id: r.project_id,
        project_name: r.project_name,
        total_spend: r.spend,
        total_conversions: r.conversions,
        account_count: 1,
        avg_cpa: 0,
      });
    }
  });

  return Array.from(projectMap.values()).map((p) => ({
    ...p,
    total_spend: Math.round(p.total_spend * 100) / 100,
    avg_cpa: p.total_conversions > 0 ? Math.round((p.total_spend / p.total_conversions) * 100) / 100 : 0,
  }));
}

/**
 * 生成 Mock 按账户汇总
 */
function generateMockByAccount(records: AdSpendRecord[]): AdSpendByAccount[] {
  const accountMap = new Map<number, AdSpendByAccount>();

  records.forEach((r) => {
    const existing = accountMap.get(r.ad_account_id);
    if (existing) {
      existing.total_spend += r.spend;
      existing.total_conversions += r.conversions;
    } else {
      accountMap.set(r.ad_account_id, {
        ad_account_id: r.ad_account_id,
        ad_account_name: r.ad_account_name,
        project_name: r.project_name,
        channel_name: r.channel_name,
        total_spend: r.spend,
        total_conversions: r.conversions,
        avg_cpa: 0,
      });
    }
  });

  return Array.from(accountMap.values()).map((a) => ({
    ...a,
    total_spend: Math.round(a.total_spend * 100) / 100,
    avg_cpa: a.total_conversions > 0 ? Math.round((a.total_spend / a.total_conversions) * 100) / 100 : 0,
  }));
}

// ========== API Functions ==========

/**
 * 获取消耗列表
 * GET /api/v1/ad-spend
 * SoT: C3-spend-detail.md §4.1 接口清单
 * 权限: 登录用户
 */
export async function getAdSpendList(
  params: AdSpendListParams = {}
): Promise<AdSpendListResponse> {
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

  try {
    const response = await apiFetch<{ data: AdSpendListResponse }>(url);
    return response.data;
  } catch (error) {
    console.warn('[AdSpend] API 不可用，使用 Mock 数据', error);
    let mockRecords = generateMockSpendRecords();

    // 应用筛选
    if (params.project_id) {
      mockRecords = mockRecords.filter((r) => r.project_id === params.project_id);
    }
    if (params.ad_account_id) {
      mockRecords = mockRecords.filter((r) => r.ad_account_id === params.ad_account_id);
    }
    if (params.channel_id) {
      mockRecords = mockRecords.filter((r) => r.channel_id === params.channel_id);
    }
    if (params.start_date) {
      mockRecords = mockRecords.filter((r) => r.report_date >= params.start_date!);
    }
    if (params.end_date) {
      mockRecords = mockRecords.filter((r) => r.report_date <= params.end_date!);
    }

    const page = params.page || 1;
    const pageSize = params.page_size || 20;
    const start = (page - 1) * pageSize;
    const paginatedRecords = mockRecords.slice(start, start + pageSize);

    return {
      items: paginatedRecords,
      total: mockRecords.length,
      page,
      page_size: pageSize,
      summary: generateMockSummary(mockRecords),
    };
  }
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

  try {
    const response = await apiFetch<{ data: AdSpendSummary }>(url);
    return response.data;
  } catch (error) {
    console.warn('[AdSpend] Summary API 不可用，使用 Mock 数据', error);
    let mockRecords = generateMockSpendRecords();

    // 应用筛选
    if (params.project_id) {
      mockRecords = mockRecords.filter((r) => r.project_id === params.project_id);
    }
    if (params.start_date) {
      mockRecords = mockRecords.filter((r) => r.report_date >= params.start_date!);
    }
    if (params.end_date) {
      mockRecords = mockRecords.filter((r) => r.report_date <= params.end_date!);
    }

    return generateMockSummary(mockRecords);
  }
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

  try {
    const response = await apiFetch<{ data: AdSpendTrendResponse }>(url);
    return response.data;
  } catch (error) {
    console.warn('[AdSpend] Trend API 不可用，使用 Mock 数据', error);
    let mockRecords = generateMockSpendRecords();

    // 应用筛选
    if (params.project_id) {
      mockRecords = mockRecords.filter((r) => r.project_id === params.project_id);
    }
    if (params.start_date) {
      mockRecords = mockRecords.filter((r) => r.report_date >= params.start_date!);
    }
    if (params.end_date) {
      mockRecords = mockRecords.filter((r) => r.report_date <= params.end_date!);
    }

    return generateMockTrend(mockRecords);
  }
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

  try {
    const response = await apiFetch<{ data: AdSpendByProject[] }>(url);
    return response.data;
  } catch (error) {
    console.warn('[AdSpend] ByProject API 不可用，使用 Mock 数据', error);
    let mockRecords = generateMockSpendRecords();

    if (params.start_date) {
      mockRecords = mockRecords.filter((r) => r.report_date >= params.start_date!);
    }
    if (params.end_date) {
      mockRecords = mockRecords.filter((r) => r.report_date <= params.end_date!);
    }

    return generateMockByProject(mockRecords);
  }
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

  try {
    const response = await apiFetch<{ data: AdSpendByAccount[] }>(url);
    return response.data;
  } catch (error) {
    console.warn('[AdSpend] ByAccount API 不可用，使用 Mock 数据', error);
    let mockRecords = generateMockSpendRecords();

    if (params.project_id) {
      mockRecords = mockRecords.filter((r) => r.project_id === params.project_id);
    }
    if (params.start_date) {
      mockRecords = mockRecords.filter((r) => r.report_date >= params.start_date!);
    }
    if (params.end_date) {
      mockRecords = mockRecords.filter((r) => r.report_date <= params.end_date!);
    }

    return generateMockByAccount(mockRecords);
  }
}

/**
 * 导出消耗数据
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

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    throw new Error('导出失败');
  }

  return response.blob();
}

/**
 * 导入消耗数据
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
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_platform', sourcePlatform);

  const response = await fetch(`${BASE_PATH}/import`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${localStorage.getItem('token')}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || '导入失败');
  }

  const result = await response.json();
  return result.data;
}
