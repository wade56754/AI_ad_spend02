/**
 * Dashboard API Service
 *
 * SoT: docs/10.module-specs/A1-dashboard.md §5 API 接口
 * SoT: API_SOT.md v9.0 (待实现后端 API)
 *
 * 注意: 当前使用 mock 数据，后端 API 实现后需要对接
 */

import { apiFetch } from '@/lib/api';
import type {
  DashboardOverviewResponse,
  DashboardTrendResponse,
  DashboardTopProjectsResponse,
  DashboardPendingCountsResponse,
  DashboardOverviewParams,
  DashboardTrendParams,
} from '../types/dashboard.types';

const BASE_URL = '/api/v1/dashboard';

// ============ Mock 数据生成器 ============

/**
 * 生成 mock overview 数据
 * 用于开发阶段，后端 API 实现后移除
 */
function generateMockOverview(): DashboardOverviewResponse['data'] {
  return {
    // MASTER.md §6.5 必须字段
    total_spend: 2856800.00,
    total_conversions: 72580,
    total_revenue: 3625000.00,
    total_profit: 568000.00,
    cpl: 39.36,
    // 变化率
    spend_change: 12.5,
    conversions_change: 8.3,
    revenue_change: 10.8,
    profit_change: 15.2,
    // 运营状态
    active_projects: 12,
    abnormal_projects: 3,
    pending_topups: 3,
    // 扩展字段
    cpl_target: 35.00,
    today_spend: 125680.50,
    today_conversions: 3256,
    today_revenue: 162500.00,
    today_profit: 36819.50,
  };
}

/**
 * 生成 mock 趋势数据
 */
function generateMockTrend(days: number): DashboardTrendResponse['data'] {
  const points = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);

    const trendFactor = 1 + (days - i) * 0.002;
    const seed = i * 12345;
    const randomFactor = (offset: number) => {
      const x = Math.sin(seed + offset) * 10000;
      return 1 + (x - Math.floor(x) - 0.5) * 0.15;
    };

    const spend = Math.round(120000 * randomFactor(0) * trendFactor);
    const revenue = Math.round(160000 * randomFactor(1) * trendFactor);
    const profit = revenue - spend;
    const conversions = Math.round(3000 * randomFactor(2) * trendFactor);

    points.push({
      date: date.toISOString().split('T')[0],
      spend,
      revenue,
      profit,
      conversions,
    });
  }

  // 计算趋势总结
  const lastValue = points[points.length - 1]?.spend || 0;
  const firstValue = points[0]?.spend || 0;
  const changePercent = firstValue > 0 ? ((lastValue - firstValue) / firstValue) * 100 : 0;

  return {
    points,
    summary: {
      trend: changePercent > 1 ? 'up' : changePercent < -1 ? 'down' : 'stable',
      change_percent: Math.round(changePercent * 10) / 10,
      description: changePercent > 0 ? `近${days}日消耗稳定上升` : `近${days}日消耗平稳`,
    },
  };
}

/**
 * 生成 mock Top 列表数据
 */
function generateMockTopProjects(): DashboardTopProjectsResponse['data'] {
  return {
    top_spend: [
      { id: '1', name: '保险-养老险', spend: 285600, change: 12.5 },
      { id: '2', name: '教育-成人考证', spend: 198400, change: 8.3 },
      { id: '3', name: '金融-信用卡', spend: 156800, change: -2.1 },
      { id: '4', name: '汽车-新能源', spend: 125600, change: 15.8 },
      { id: '5', name: '医美-抗衰老', spend: 98500, change: 5.6 },
    ],
    worst_roas: [
      { id: '6', name: '装修-全屋定制', roas: 0.65, spend: 45600 },
      { id: '7', name: '旅游-出境游', roas: 0.72, spend: 32100 },
      { id: '8', name: '电商-女装', roas: 0.85, spend: 28900 },
      { id: '9', name: '餐饮-加盟', roas: 0.91, spend: 21500 },
      { id: '10', name: '房产-新房', roas: 0.95, spend: 18200 },
    ],
  };
}

/**
 * 生成 mock 待处理数据
 */
function generateMockPendingCounts(): DashboardPendingCountsResponse['data'] {
  return {
    pending_topups: 3,
    pending_settlements: 2,
    pending_reconciliations: 5,
    pending_imports: 1,
  };
}

// ============ API 服务 ============

/**
 * Dashboard API 服务
 * SoT: A1-dashboard.md §5.1 接口清单
 */
export const dashboardApi = {
  /**
   * 获取驾驶舱概览数据
   * SoT: A1-dashboard.md §5.2 GET /api/v1/dashboard/overview
   */
  async getOverview(params: DashboardOverviewParams): Promise<DashboardOverviewResponse> {
    // TODO: 后端 API 实现后取消注释
    // const queryParams = new URLSearchParams({
    //   date_from: params.date_from,
    //   date_to: params.date_to,
    // });
    // return apiFetch<DashboardOverviewResponse>(`${BASE_URL}/overview?${queryParams}`);

    // Mock 响应
    return {
      success: true,
      data: generateMockOverview(),
      message: 'success',
    };
  },

  /**
   * 获取趋势数据
   * SoT: A1-dashboard.md §5.2 GET /api/v1/dashboard/trend
   */
  async getTrend(params: DashboardTrendParams): Promise<DashboardTrendResponse> {
    // TODO: 后端 API 实现后取消注释
    // const queryParams = new URLSearchParams({
    //   date_from: params.date_from,
    //   date_to: params.date_to,
    // });
    // if (params.metrics) {
    //   params.metrics.forEach(m => queryParams.append('metrics', m));
    // }
    // return apiFetch<DashboardTrendResponse>(`${BASE_URL}/trend?${queryParams}`);

    // 计算天数
    const dateFrom = new Date(params.date_from);
    const dateTo = new Date(params.date_to);
    const days = Math.ceil((dateTo.getTime() - dateFrom.getTime()) / (1000 * 60 * 60 * 24)) + 1;

    // Mock 响应
    return {
      success: true,
      data: generateMockTrend(days),
      message: 'success',
    };
  },

  /**
   * 获取 Top 项目列表
   * SoT: A1-dashboard.md §5.1 GET /api/v1/dashboard/top-projects
   */
  async getTopProjects(): Promise<DashboardTopProjectsResponse> {
    // TODO: 后端 API 实现后取消注释
    // return apiFetch<DashboardTopProjectsResponse>(`${BASE_URL}/top-projects`);

    // Mock 响应
    return {
      success: true,
      data: generateMockTopProjects(),
      message: 'success',
    };
  },

  /**
   * 获取待处理数量
   * SoT: A1-dashboard.md §5.1 GET /api/v1/dashboard/pending-counts
   */
  async getPendingCounts(): Promise<DashboardPendingCountsResponse> {
    // TODO: 后端 API 实现后取消注释
    // return apiFetch<DashboardPendingCountsResponse>(`${BASE_URL}/pending-counts`);

    // Mock 响应
    return {
      success: true,
      data: generateMockPendingCounts(),
      message: 'success',
    };
  },
};

export default dashboardApi;
