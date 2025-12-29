/**
 * Dashboard API Service
 *
 * SoT: docs/10.module-specs/A1-dashboard.md §5 API 接口
 * SoT: API_SOT.md v9.0
 *
 * 使用真实后端 API 获取数据
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

// 后端 API 基础路径
const BASE_URL = '/api/v1/dashboards';

// ============ 后端响应类型 ============

interface BackendKpiData {
  total_spend: string | number;
  total_conversions: number;
  total_follows: number;
  total_revenue: string | number;
  avg_cpl: string | number | null;
  roi: number | null;
  profit_margin: number | null;
  spend_change: number | null;
  conversion_change: number | null;
  cpl_change: number | null;
}

interface BackendTrendItem {
  report_date: string;
  spend: string | number;
  conversions: number;
  follows: number;
  cpl: string | number | null;
}

interface BackendProjectRankingItem {
  project_id: number;
  project_name: string;
  total_spend: string | number;
  total_follows: number;
  cost_per_follow: string | number | null;
  roas: number | null;
  rank: number;
}

interface BackendTodoItem {
  type: string;
  label: string;
  count: number;
  priority: string;
}

interface BackendCeoDetailResponse {
  success: boolean;
  data: {
    summary: {
      period: string;
      start_date: string;
      end_date: string;
      total_projects: number;
      active_projects: number;
      suspended_projects: number;
      kpi: BackendKpiData;
      pending_reports: number;
      pending_topups: number;
      trend_flagged_count: number;
      alerts: Array<{
        type: string;
        severity: string;
        message: string;
      }>;
      current_phase: number;
    };
    trend: {
      period: string;
      start_date: string;
      end_date: string;
      granularity: string;
      items: BackendTrendItem[];
    };
    top_spend_projects: BackendProjectRankingItem[];
    worst_cpl_projects: BackendProjectRankingItem[];
    todos: {
      total_count: number;
      items: BackendTodoItem[];
    };
  };
  message: string;
}

// ============ 工具函数 ============

/**
 * 安全转换为数字
 */
function toNumber(value: string | number | null | undefined): number {
  if (value === null || value === undefined) return 0;
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return isNaN(num) ? 0 : num;
}

/**
 * 格式化日期为 YYYY-MM 格式
 */
function toPeriod(dateStr: string): string {
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

// ============ 缓存 CEO Detail 响应 ============

let cachedCeoDetail: BackendCeoDetailResponse['data'] | null = null;
let cacheTimestamp: number = 0;
const CACHE_TTL = 30000; // 30秒缓存

async function fetchCeoDetail(period?: string): Promise<BackendCeoDetailResponse['data']> {
  const now = Date.now();
  if (cachedCeoDetail && (now - cacheTimestamp) < CACHE_TTL) {
    return cachedCeoDetail;
  }

  const queryParams = new URLSearchParams();
  if (period) {
    queryParams.append('period', period);
  }
  queryParams.append('top_n', '5');

  const url = `${BASE_URL}/ceo/detail${queryParams.toString() ? '?' + queryParams.toString() : ''}`;

  // apiFetch 自动解包 envelope，直接返回 data 部分
  const data = await apiFetch<BackendCeoDetailResponse['data']>(url);

  if (data) {
    cachedCeoDetail = data;
    cacheTimestamp = now;
  }

  return data;
}

// ============ API 服务 ============

/**
 * Dashboard API 服务
 * SoT: A1-dashboard.md §5.1 接口清单
 */
export const dashboardApi = {
  /**
   * 获取驾驶舱概览数据
   * 使用 /ceo/detail API 获取完整数据
   */
  async getOverview(params: DashboardOverviewParams): Promise<DashboardOverviewResponse> {
    try {
      const period = toPeriod(params.date_from);
      const detail = await fetchCeoDetail(period);

      const { summary } = detail;
      const kpi = summary.kpi;

      // 计算今日数据 (从趋势数据最后一天)
      const todayTrend = detail.trend.items[detail.trend.items.length - 1];
      const today_spend = todayTrend ? toNumber(todayTrend.spend) : 0;
      const today_conversions = todayTrend ? todayTrend.follows : 0;

      // 估算今日收入和利润 (基于整体利润率)
      const totalSpend = toNumber(kpi.total_spend);
      const totalRevenue = toNumber(kpi.total_revenue);
      const profitMargin = totalRevenue > 0 ? (totalRevenue - totalSpend) / totalRevenue : 0.2;
      const today_revenue = today_spend * (1 + profitMargin);
      const today_profit = today_revenue - today_spend;

      // 计算异常项目数 (CPL > target * 1.3)
      const avgCpl = toNumber(kpi.avg_cpl);
      const cplTarget = 35; // 默认目标
      const abnormal_projects = detail.worst_cpl_projects.filter(
        p => toNumber(p.cost_per_follow) > cplTarget * 1.3
      ).length;

      return {
        success: true,
        data: {
          total_spend: totalSpend,
          total_conversions: kpi.total_follows,
          total_revenue: totalRevenue,
          total_profit: totalRevenue - totalSpend,
          cpl: avgCpl,
          spend_change: kpi.spend_change ?? 0,
          conversions_change: kpi.conversion_change ?? 0,
          revenue_change: kpi.spend_change ?? 0, // 使用消耗变化近似
          profit_change: kpi.spend_change ? kpi.spend_change * 1.2 : 0,
          active_projects: summary.active_projects,
          abnormal_projects: abnormal_projects,
          pending_topups: summary.pending_topups,
          cpl_target: cplTarget,
          today_spend,
          today_conversions,
          today_revenue,
          today_profit,
        },
        message: 'success',
      };
    } catch (error) {
      console.error('Failed to fetch dashboard overview:', error);
      throw error;
    }
  },

  /**
   * 获取趋势数据
   * 使用 /ceo/detail 或 /trend API
   */
  async getTrend(params: DashboardTrendParams): Promise<DashboardTrendResponse> {
    try {
      const period = toPeriod(params.date_from);
      const detail = await fetchCeoDetail(period);

      const { trend } = detail;

      // 转换趋势数据格式
      const points = trend.items.map(item => ({
        date: item.report_date,
        spend: toNumber(item.spend),
        revenue: toNumber(item.spend) * 1.35, // 估算收入
        profit: toNumber(item.spend) * 0.35, // 估算利润
        conversions: item.follows,
      }));

      // 计算趋势总结
      const lastValue = points[points.length - 1]?.spend || 0;
      const firstValue = points[0]?.spend || 0;
      const changePercent = firstValue > 0 ? ((lastValue - firstValue) / firstValue) * 100 : 0;

      return {
        success: true,
        data: {
          points,
          summary: {
            trend: changePercent > 1 ? 'up' : changePercent < -1 ? 'down' : 'stable',
            change_percent: Math.round(changePercent * 10) / 10,
            description: changePercent > 0 ? `近期消耗上升 ${changePercent.toFixed(1)}%` : `近期消耗下降 ${Math.abs(changePercent).toFixed(1)}%`,
          },
        },
        message: 'success',
      };
    } catch (error) {
      console.error('Failed to fetch dashboard trend:', error);
      throw error;
    }
  },

  /**
   * 获取 Top 项目列表
   */
  async getTopProjects(): Promise<DashboardTopProjectsResponse> {
    try {
      const detail = await fetchCeoDetail();

      return {
        success: true,
        data: {
          top_spend: detail.top_spend_projects.map(p => ({
            id: String(p.project_id),
            name: p.project_name,
            spend: toNumber(p.total_spend),
            change: 0, // TODO: 需要后端支持环比
          })),
          worst_roas: detail.worst_cpl_projects.map(p => ({
            id: String(p.project_id),
            name: p.project_name,
            roas: p.roas ?? (p.cost_per_follow ? 35 / toNumber(p.cost_per_follow) : 0),
            spend: toNumber(p.total_spend),
          })),
        },
        message: 'success',
      };
    } catch (error) {
      console.error('Failed to fetch top projects:', error);
      throw error;
    }
  },

  /**
   * 获取待处理数量
   */
  async getPendingCounts(): Promise<DashboardPendingCountsResponse> {
    try {
      const detail = await fetchCeoDetail();

      // 从 todos 解析各类待处理数量
      const { todos, summary } = detail;

      let pending_reports = 0;
      let trend_flagged = 0;

      todos.items.forEach(item => {
        if (item.type === 'pending_report') {
          pending_reports = item.count;
        } else if (item.type === 'trend_flagged') {
          trend_flagged = item.count;
        }
      });

      return {
        success: true,
        data: {
          pending_topups: summary.pending_topups,
          pending_settlements: pending_reports, // 复用待审核日报数
          pending_reconciliations: trend_flagged, // 复用趋势异常数
          pending_imports: 0, // TODO: 需要后端支持
        },
        message: 'success',
      };
    } catch (error) {
      console.error('Failed to fetch pending counts:', error);
      throw error;
    }
  },

  /**
   * 清除缓存 (刷新时调用)
   */
  clearCache() {
    cachedCeoDetail = null;
    cacheTimestamp = 0;
  },
};

// ============ CEO Dashboard V3 API ============
// 核心公式: 毛利 = 收款 - 消耗 (不含手续费)

/**
 * CEO Dashboard V3 API Types
 */
export interface CeoV3OverviewResponse {
  period: string;
  currency: string;
  generated_at: string;
  formula_version: string;
  formula_note: string;
  cash_status: {
    opening_balance: number;
    closing_balance: number;
    total_income: number;
    total_expense: number;
    balance_change_pct: number;
    runway_days: number;
  };
  profit_summary: {
    total_revenue: number;
    total_cost: number;
    total_profit: number;
    profit_rate: number;
    profit_rate_pct: number;
    total_conversions: number;
    avg_cpl: number;
    target_profit_rate: number;
    profit_status: string;
  };
  project_balance_summary: {
    total_projects: number;
    prepaid_count: number;
    pending_refund_count: number;
    refunded_count: number;
    total_prepaid_balance: number;
  };
  action_items: {
    abnormal_projects_count?: number;
    pending_reports_count?: number;
    pending_refunds_count?: number;
  };
  top_projects: Array<{
    project_name: string;
    profit: number;
    profit_rate: number;
    profit_rate_pct: number;
    status: string;
  }>;
}

export interface CeoV3ProfitSummaryResponse {
  period: string;
  currency: string;
  formula: string;
  revenue: {
    total: number;
    label: string;
    conversions: number;
    avg_unit_price?: number;
    note: string;
  };
  cost: {
    total: number;
    label: string;
    note: string;
  };
  profit: {
    total: number;
    label: string;
    rate: number;
    rate_pct: number;
    target_rate: number;
    gap: number;
    status: string;
    status_label: string;
  };
  cpl: {
    overall: number;
    formula: string;
  };
  fee_reference: {
    estimated_rate: number;
    estimated_amount: number;
    note: string;
  };
}

export interface CeoV3ProjectBalanceItem {
  project_id: number;
  project_name: string;
  client_name: string | null;
  cumulative_revenue: number;
  cumulative_cost: number;
  balance: number;
  status: string;
  status_label: string;
  refund_amount?: number;
  refund_date?: string;
  note?: string;
}

export interface CeoV3ProjectBalanceResponse {
  period: string;
  currency: string;
  formula: string;
  items: CeoV3ProjectBalanceItem[];
  totals: {
    cumulative_revenue: number;
    cumulative_cost: number;
    total_balance: number;
  };
  summary: {
    total_count: number;
    prepaid_count: number;
    pending_refund_count: number;
    refunded_count: number;
    settled_count: number;
    need_topup_count: number;
  };
}

export interface CeoV3ProjectRankingItem {
  rank: number;
  project_id: number;
  project_name: string;
  client_name?: string;
  profit_status: string;
  pricing: {
    type: string;
    unit_price?: number;
    markup_rate?: number;
    note: string;
  };
  metrics: {
    conversions: number | null;
    revenue: number;
    cost: number;
    profit: number;
    profit_rate: number;
    profit_rate_pct: number;
    cpl: number | null;
  };
}

export interface CeoV3ProjectRankingResponse {
  period: string;
  currency: string;
  formula: string;
  items: CeoV3ProjectRankingItem[];
  summary: {
    total_projects: number;
    healthy_count: number;
    warning_count: number;
    danger_count: number;
    total_profit: number;
    avg_profit_rate: number;
  };
}

export interface CeoV3TrendItem {
  date: string;
  revenue: number;
  spend: number;
  profit: number;
  conversions: number;
}

export interface CeoV3TrendResponse {
  period: string;
  granularity: string;
  items: CeoV3TrendItem[];
}

export interface CeoV3ActionItemsResponse {
  abnormal_projects: {
    count: number;
    items: Array<{
      project_id: number;
      project_name: string;
      issue_type: string;
      severity: string;
      metrics: {
        revenue: number;
        cost: number;
        profit: number;
        profit_rate: number;
      };
      message: string;
      suggested_action: string;
    }>;
  };
  pending_reports: {
    count: number;
    items: Array<{
      date: string;
      count: number;
    }>;
  };
  pending_refunds: {
    count: number;
    total_amount: number;
    items: Array<{
      project_name: string;
      amount: number;
    }>;
  };
}

/**
 * CEO Dashboard V3 API
 * 核心公式: 毛利 = 收款 - 消耗 (不含手续费)
 */
export const ceoV3Api = {
  /**
   * CEO 仪表盘概览
   */
  async getOverview(period?: string): Promise<CeoV3OverviewResponse> {
    const params = new URLSearchParams();
    if (period) params.append('period', period);
    const url = `${BASE_URL}/ceo/v3/overview${params.toString() ? '?' + params.toString() : ''}`;
    return apiFetch<CeoV3OverviewResponse>(url);
  },

  /**
   * 利润概览 (毛利 = 收款 - 消耗)
   */
  async getProfitSummary(period?: string): Promise<CeoV3ProfitSummaryResponse> {
    const params = new URLSearchParams();
    if (period) params.append('period', period);
    const url = `${BASE_URL}/ceo/v3/profit-summary${params.toString() ? '?' + params.toString() : ''}`;
    return apiFetch<CeoV3ProfitSummaryResponse>(url);
  },

  /**
   * 项目余额列表
   */
  async getProjectBalance(period?: string): Promise<CeoV3ProjectBalanceResponse> {
    const params = new URLSearchParams();
    if (period) params.append('period', period);
    const url = `${BASE_URL}/ceo/v3/project-balance${params.toString() ? '?' + params.toString() : ''}`;
    return apiFetch<CeoV3ProjectBalanceResponse>(url);
  },

  /**
   * 项目毛利排行
   */
  async getProjectRanking(period?: string, limit: number = 10): Promise<CeoV3ProjectRankingResponse> {
    const params = new URLSearchParams();
    if (period) params.append('period', period);
    params.append('limit', String(limit));
    const url = `${BASE_URL}/ceo/v3/project-ranking?${params.toString()}`;
    return apiFetch<CeoV3ProjectRankingResponse>(url);
  },

  /**
   * 趋势数据
   */
  async getTrend(period?: string, granularity: string = 'daily'): Promise<CeoV3TrendResponse> {
    const params = new URLSearchParams();
    if (period) params.append('period', period);
    params.append('granularity', granularity);
    const url = `${BASE_URL}/ceo/v3/trend?${params.toString()}`;
    return apiFetch<CeoV3TrendResponse>(url);
  },

  /**
   * 待办事项
   */
  async getActionItems(period?: string): Promise<CeoV3ActionItemsResponse> {
    const params = new URLSearchParams();
    if (period) params.append('period', period);
    const url = `${BASE_URL}/ceo/v3/action-items${params.toString() ? '?' + params.toString() : ''}`;
    return apiFetch<CeoV3ActionItemsResponse>(url);
  },
};

export default dashboardApi;
