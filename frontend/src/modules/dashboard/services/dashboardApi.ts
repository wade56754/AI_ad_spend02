/**
 * Dashboard API Service Layer
 *
 * 负责与后端 Dashboard API 通信
 * 所有 API 请求必须通过此文件，禁止在组件/Hook 中直接调用 apiFetch
 *
 * @see API_SOT.md v9.0 - API Response Envelope Format
 * @see FRONTEND_DEVELOPMENT_FLOW_v1.0.md §3.3 - API Service Layer 规范
 */

import { apiFetch } from '@/lib/api/apiFetch';
import type {
  DashboardFiltersState,
  KpiMetric,
  TrendChartData,
  RiskAlert,
  TodoTask,
  FundsOverview,
} from '../types';

/**
 * Convert filters to query parameters
 */
function buildQueryParams(filters: DashboardFiltersState): Record<string, string | number | undefined> {
  const params: Record<string, string | number | undefined> = {};

  // Date range handling
  if (filters.dateRange === 'custom' && filters.startDate && filters.endDate) {
    params.start_date = filters.startDate;
    params.end_date = filters.endDate;
  } else {
    params.date_range = filters.dateRange;
  }

  // Project filter
  if (filters.projectId) {
    params.project_id = filters.projectId;
  }

  return params;
}

/**
 * Get KPI metrics
 *
 * 后端路径: GET /api/v1/dashboard/kpi
 * 响应格式: Envelope<KpiMetric[]>
 *
 * @param filters - Dashboard filter state
 * @returns Promise<KpiMetric[]>
 */
export async function getKpiMetrics(filters: DashboardFiltersState): Promise<KpiMetric[]> {
  const params = buildQueryParams(filters);

  const data = await apiFetch<KpiMetric[]>('/dashboard/kpi', { params });

  return data;
}

/**
 * Get trend chart data
 *
 * 后端路径: GET /api/v1/dashboard/trend
 * 响应格式: Envelope<TrendChartData[]>
 *
 * @param filters - Dashboard filter state
 * @returns Promise<TrendChartData[]>
 */
export async function getChartData(filters: DashboardFiltersState): Promise<TrendChartData[]> {
  const params = buildQueryParams(filters);

  const data = await apiFetch<TrendChartData[]>('/dashboard/trend', { params });

  return data;
}

/**
 * Get risk alerts
 *
 * 后端路径: GET /api/v1/dashboard/alerts
 * 响应格式: Envelope<RiskAlert[]>
 *
 * @param filters - Dashboard filter state
 * @returns Promise<RiskAlert[]>
 */
export async function getRiskAlerts(filters: DashboardFiltersState): Promise<RiskAlert[]> {
  const params = buildQueryParams(filters);

  const data = await apiFetch<RiskAlert[]>('/dashboard/alerts', { params });

  return data;
}

/**
 * Get todo tasks
 *
 * 后端路径: GET /api/v1/dashboard/tasks
 * 响应格式: Envelope<TodoTask[]>
 *
 * 注意: UI status ('pending'|'in_progress'|'completed') 是聚合状态
 * 后端根据 STATE_MACHINE.md v2.6 映射各模块状态到 UI status
 *
 * @param filters - Dashboard filter state
 * @returns Promise<TodoTask[]>
 */
export async function getTodoTasks(filters: DashboardFiltersState): Promise<TodoTask[]> {
  const params = buildQueryParams(filters);

  const data = await apiFetch<TodoTask[]>('/dashboard/tasks', { params });

  return data;
}

/**
 * Get funds overview
 *
 * 后端路径: GET /api/v1/dashboard/funds
 * 响应格式: Envelope<FundsOverview>
 *
 * @param filters - Dashboard filter state (资金概览可能不需要 filters)
 * @returns Promise<FundsOverview>
 */
export async function getFundsOverview(filters: DashboardFiltersState): Promise<FundsOverview> {
  // 资金概览不需要 filters，但为了保持接口一致性，仍然接受 filters 参数
  const data = await apiFetch<FundsOverview>('/dashboard/funds');

  return data;
}

/**
 * Dashboard API 统一导出
 */
export const dashboardApi = {
  getKpiMetrics,
  getChartData,
  getRiskAlerts,
  getTodoTasks,
  getFundsOverview,
};

export default dashboardApi;
