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
 * 注意: 当前使用 mock 数据回退，后端 API 实现后需要对接
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
  ProfitByProjectItem,
  ProfitByAccountItem,
  ProfitByChannelItem,
  ProfitTrendItem,
} from '../types/profit.types';

const BASE_PATH = '/api/v1/finance/profit';

// ========== Mock 数据生成器 ==========

/**
 * 生成 mock 利润概览数据
 * SoT: A3-project-pnl.md §5.2 响应示例
 */
function generateMockOverview(): ProfitOverviewResponse {
  return {
    today_revenue: 125000,
    today_cost: 98000,
    today_profit: 27000,
    today_profit_margin: 21.6,
    week_revenue: 875000,
    week_cost: 686000,
    week_profit: 189000,
    week_profit_margin: 21.6,
    month_revenue: 3500000,
    month_cost: 2744000,
    month_profit: 756000,
    month_profit_margin: 21.6,
    profit_change_from_yesterday: 12.5,
    profit_change_from_last_week: 8.3,
    profit_change_from_last_month: 15.2,
    top_profit_projects: [
      { project_id: 1, project_name: '618大促项目', profit: 320000 },
      { project_id: 2, project_name: '品牌推广项目', profit: 180000 },
      { project_id: 3, project_name: '双十一预热', profit: 156000 },
      { project_id: 4, project_name: '年终大促', profit: 100000 },
    ],
  };
}

/**
 * 生成 mock 按项目利润数据
 * SoT: A3-project-pnl.md §5.2 + MASTER.md §6.5 is_abnormal
 */
function generateMockByProject(): ProfitByProjectItem[] {
  return [
    {
      project_id: 1,
      project_name: '618大促项目',
      owner_id: 1,
      owner_name: '张三',
      cpl: 85.5,
      cpl_target: 100,
      is_abnormal: false,
      total_conversions: 3750,
      avg_unit_price: 120,
      total_revenue: 450000,
      total_spend: 320625,
      total_fee: 9619,
      total_cost: 330244,
      total_profit: 119756,
      profit_margin: 26.6,
      report_count: 30,
    },
    {
      project_id: 2,
      project_name: '品牌推广项目',
      owner_id: 2,
      owner_name: '李四',
      cpl: 92.3,
      cpl_target: 90,
      is_abnormal: true, // CPL 超标
      total_conversions: 2800,
      avg_unit_price: 110,
      total_revenue: 308000,
      total_spend: 258440,
      total_fee: 7753,
      total_cost: 266193,
      total_profit: 41807,
      profit_margin: 13.6,
      report_count: 25,
    },
    {
      project_id: 3,
      project_name: '双十一预热',
      owner_id: 1,
      owner_name: '张三',
      cpl: 78.2,
      cpl_target: 95,
      is_abnormal: false,
      total_conversions: 4200,
      avg_unit_price: 115,
      total_revenue: 483000,
      total_spend: 328440,
      total_fee: 9853,
      total_cost: 338293,
      total_profit: 144707,
      profit_margin: 30.0,
      report_count: 35,
    },
    {
      project_id: 4,
      project_name: '年终大促',
      owner_id: 3,
      owner_name: '王五',
      cpl: 145.6,
      cpl_target: 100,
      is_abnormal: true, // CPL 严重超标
      total_conversions: 1500,
      avg_unit_price: 130,
      total_revenue: 195000,
      total_spend: 218400,
      total_fee: 6552,
      total_cost: 224952,
      total_profit: -29952,
      profit_margin: -15.4,
      report_count: 20,
    },
  ];
}

/**
 * 生成 mock 按账户利润数据
 */
function generateMockByAccount(): ProfitByAccountItem[] {
  return [
    {
      ad_account_id: 101,
      ad_account_name: 'FB-品牌主账户',
      project_id: 1,
      project_name: '618大促项目',
      total_conversions: 1500,
      total_revenue: 180000,
      total_spend: 128250,
      total_cost: 132418,
      total_profit: 47582,
      profit_margin: 26.4,
    },
    {
      ad_account_id: 102,
      ad_account_name: 'Google-搜索广告',
      project_id: 1,
      project_name: '618大促项目',
      total_conversions: 1200,
      total_revenue: 144000,
      total_spend: 102600,
      total_cost: 105678,
      total_profit: 38322,
      profit_margin: 26.6,
    },
    {
      ad_account_id: 201,
      ad_account_name: 'TikTok-A类视频',
      project_id: 2,
      project_name: '品牌推广项目',
      total_conversions: 1800,
      total_revenue: 198000,
      total_spend: 166140,
      total_cost: 171124,
      total_profit: 26876,
      profit_margin: 13.6,
    },
  ];
}

/**
 * 生成 mock 按渠道利润数据
 */
function generateMockByChannel(): ProfitByChannelItem[] {
  return [
    {
      channel_id: 1,
      channel_name: '巨量引擎',
      total_accounts: 15,
      total_conversions: 5200,
      total_revenue: 624000,
      total_spend: 445680,
      total_cost: 459050,
      total_profit: 164950,
      profit_margin: 26.4,
    },
    {
      channel_id: 2,
      channel_name: '腾讯广告',
      total_accounts: 10,
      total_conversions: 3800,
      total_revenue: 418000,
      total_spend: 351120,
      total_cost: 361654,
      total_profit: 56346,
      profit_margin: 13.5,
    },
    {
      channel_id: 3,
      channel_name: '百度营销',
      total_accounts: 8,
      total_conversions: 2800,
      total_revenue: 336000,
      total_spend: 232680,
      total_cost: 239660,
      total_profit: 96340,
      profit_margin: 28.7,
    },
  ];
}

/**
 * 生成 mock 利润趋势数据
 */
function generateMockTrend(): ProfitTrendItem[] {
  const today = new Date();
  const items: ProfitTrendItem[] = [];

  for (let i = 6; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];

    const baseProfit = 25000 + Math.random() * 10000;
    const prevProfit = i === 6 ? null : items[items.length - 1]?.total_profit || baseProfit;

    items.push({
      period: dateStr,
      period_start: dateStr,
      period_end: dateStr,
      total_conversions: Math.floor(400 + Math.random() * 200),
      total_revenue: Math.floor(baseProfit * 4.5),
      total_cost: Math.floor(baseProfit * 3.5),
      total_profit: Math.floor(baseProfit),
      profit_margin: 20 + Math.random() * 10,
      profit_change: prevProfit ? Math.floor(baseProfit - prevProfit) : null,
      profit_change_rate: prevProfit ? ((baseProfit - prevProfit) / prevProfit * 100) : null,
    });
  }

  return items;
}

// ========== Query Functions ==========

/**
 * Get profit summary
 * GET /api/v1/finance/profit/summary
 * SoT: A3-project-pnl.md §5.1
 */
export async function getProfitSummary(
  params: ProfitSummaryParams = {}
): Promise<ProfitSummaryResponse> {
  // TODO: 后端 API 实现后取消注释
  // const searchParams = new URLSearchParams();
  // if (params.project_id) searchParams.set('project_id', String(params.project_id));
  // if (params.start_date) searchParams.set('start_date', params.start_date);
  // if (params.end_date) searchParams.set('end_date', params.end_date);
  // const query = searchParams.toString();
  // const url = query ? `${BASE_PATH}/summary?${query}` : `${BASE_PATH}/summary`;
  // return apiFetch<ProfitSummaryResponse>(url);

  // Mock 响应
  const items = generateMockByProject();
  return {
    items: items.map((p) => ({
      report_date: new Date().toISOString().split('T')[0],
      project_id: p.project_id,
      project_name: p.project_name,
      conversions_final: p.total_conversions,
      unit_price: p.avg_unit_price,
      revenue: p.total_revenue,
      real_spend: p.total_spend,
      fee: p.total_fee,
      cost: p.total_cost,
      profit: p.total_profit,
      profit_margin: p.profit_margin,
    })),
    total_conversions: items.reduce((sum, i) => sum + i.total_conversions, 0),
    total_revenue: items.reduce((sum, i) => sum + i.total_revenue, 0),
    total_cost: items.reduce((sum, i) => sum + i.total_cost, 0),
    total_profit: items.reduce((sum, i) => sum + i.total_profit, 0),
    overall_profit_margin: 22.5,
  };
}

/**
 * Get profit overview
 * GET /api/v1/finance/profit/overview
 * SoT: A3-project-pnl.md §5.1
 */
export async function getProfitOverview(): Promise<ProfitOverviewResponse> {
  // TODO: 后端 API 实现后取消注释
  // return apiFetch<ProfitOverviewResponse>(`${BASE_PATH}/overview`);

  // Mock 响应
  return generateMockOverview();
}

/**
 * Get profit by project
 * GET /api/v1/finance/profit/by-project
 * SoT: A3-project-pnl.md §5.1
 */
export async function getProfitByProject(
  params: ProfitByDimensionParams = {}
): Promise<ProfitByProjectResponse> {
  // TODO: 后端 API 实现后取消注释
  // const searchParams = new URLSearchParams();
  // if (params.start_date) searchParams.set('start_date', params.start_date);
  // if (params.end_date) searchParams.set('end_date', params.end_date);
  // if (params.limit) searchParams.set('limit', String(params.limit));
  // const query = searchParams.toString();
  // const url = query ? `${BASE_PATH}/by-project?${query}` : `${BASE_PATH}/by-project`;
  // return apiFetch<ProfitByProjectResponse>(url);

  // Mock 响应
  const items = generateMockByProject();
  const abnormalCount = items.filter((i) => i.is_abnormal).length;
  return {
    items,
    total_projects: items.length,
    total_conversions: items.reduce((sum, i) => sum + i.total_conversions, 0),
    total_revenue: items.reduce((sum, i) => sum + i.total_revenue, 0),
    total_cost: items.reduce((sum, i) => sum + i.total_cost, 0),
    total_profit: items.reduce((sum, i) => sum + i.total_profit, 0),
    overall_profit_margin: 22.5,
    abnormal_count: abnormalCount,
  };
}

/**
 * Get profit by account
 * GET /api/v1/finance/profit/by-account
 * SoT: A3-project-pnl.md §5.1
 */
export async function getProfitByAccount(
  params: ProfitByDimensionParams = {}
): Promise<ProfitByAccountResponse> {
  // TODO: 后端 API 实现后取消注释
  // const searchParams = new URLSearchParams();
  // if (params.project_id) searchParams.set('project_id', String(params.project_id));
  // if (params.start_date) searchParams.set('start_date', params.start_date);
  // if (params.end_date) searchParams.set('end_date', params.end_date);
  // if (params.limit) searchParams.set('limit', String(params.limit));
  // const query = searchParams.toString();
  // const url = query ? `${BASE_PATH}/by-account?${query}` : `${BASE_PATH}/by-account`;
  // return apiFetch<ProfitByAccountResponse>(url);

  // Mock 响应
  const items = generateMockByAccount();
  return {
    items,
    total_accounts: items.length,
    total_conversions: items.reduce((sum, i) => sum + i.total_conversions, 0),
    total_revenue: items.reduce((sum, i) => sum + i.total_revenue, 0),
    total_cost: items.reduce((sum, i) => sum + i.total_cost, 0),
    total_profit: items.reduce((sum, i) => sum + i.total_profit, 0),
    overall_profit_margin: 22.5,
  };
}

/**
 * Get profit by channel
 * GET /api/v1/finance/profit/by-channel
 * SoT: A3-project-pnl.md §5.1
 */
export async function getProfitByChannel(
  params: ProfitByDimensionParams = {}
): Promise<ProfitByChannelResponse> {
  // TODO: 后端 API 实现后取消注释
  // const searchParams = new URLSearchParams();
  // if (params.start_date) searchParams.set('start_date', params.start_date);
  // if (params.end_date) searchParams.set('end_date', params.end_date);
  // if (params.limit) searchParams.set('limit', String(params.limit));
  // const query = searchParams.toString();
  // const url = query ? `${BASE_PATH}/by-channel?${query}` : `${BASE_PATH}/by-channel`;
  // return apiFetch<ProfitByChannelResponse>(url);

  // Mock 响应
  const items = generateMockByChannel();
  return {
    items,
    total_channels: items.length,
    total_conversions: items.reduce((sum, i) => sum + i.total_conversions, 0),
    total_revenue: items.reduce((sum, i) => sum + i.total_revenue, 0),
    total_cost: items.reduce((sum, i) => sum + i.total_cost, 0),
    total_profit: items.reduce((sum, i) => sum + i.total_profit, 0),
    overall_profit_margin: 22.5,
  };
}

/**
 * Get profit trend
 * GET /api/v1/finance/profit/trend
 * SoT: A3-project-pnl.md §5.1
 */
export async function getProfitTrend(
  params: ProfitTrendParams = {}
): Promise<ProfitTrendResponse> {
  // TODO: 后端 API 实现后取消注释
  // const searchParams = new URLSearchParams();
  // if (params.project_id) searchParams.set('project_id', String(params.project_id));
  // if (params.channel_id) searchParams.set('channel_id', String(params.channel_id));
  // if (params.start_date) searchParams.set('start_date', params.start_date);
  // if (params.end_date) searchParams.set('end_date', params.end_date);
  // if (params.granularity) searchParams.set('granularity', params.granularity);
  // const query = searchParams.toString();
  // const url = query ? `${BASE_PATH}/trend?${query}` : `${BASE_PATH}/trend`;
  // return apiFetch<ProfitTrendResponse>(url);

  // Mock 响应
  const items = generateMockTrend();
  const profits = items.map((i) => i.total_profit);
  return {
    items,
    granularity: params.granularity || 'daily',
    period_count: items.length,
    avg_profit: profits.reduce((a, b) => a + b, 0) / profits.length,
    max_profit: Math.max(...profits),
    min_profit: Math.min(...profits),
    profit_volatility: 15.5,
  };
}

/**
 * Compare profit across projects
 * POST /api/v1/finance/profit/compare
 * SoT: A3-project-pnl.md §5.1
 */
export async function compareProfits(
  params: ProfitCompareParams
): Promise<ProfitCompareResponse> {
  // TODO: 后端 API 实现后取消注释
  // const searchParams = new URLSearchParams();
  // if (params.start_date) searchParams.set('start_date', params.start_date);
  // if (params.end_date) searchParams.set('end_date', params.end_date);
  // const query = searchParams.toString();
  // const url = query ? `${BASE_PATH}/compare?${query}` : `${BASE_PATH}/compare`;
  // return apiFetch<ProfitCompareResponse>(url, {
  //   method: 'POST',
  //   body: { project_ids: params.project_ids },
  // });

  // Mock 响应
  const allProjects = generateMockByProject();
  const items = allProjects
    .filter((p) => params.project_ids.includes(p.project_id))
    .map((p, idx) => ({
      project_id: p.project_id,
      project_name: p.project_name,
      total_conversions: p.total_conversions,
      total_revenue: p.total_revenue,
      total_cost: p.total_cost,
      total_profit: p.total_profit,
      profit_margin: p.profit_margin,
      rank_by_profit: idx + 1,
      rank_by_margin: idx + 1,
    }));

  return {
    items,
    compare_count: items.length,
    best_profit_project: items[0]?.project_name || null,
    best_margin_project: items[0]?.project_name || null,
    total_profit: items.reduce((sum, i) => sum + i.total_profit, 0),
    avg_profit_margin: items.length > 0
      ? items.reduce((sum, i) => sum + i.profit_margin, 0) / items.length
      : 0,
  };
}
