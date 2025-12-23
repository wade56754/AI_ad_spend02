/**
 * Dashboard Data Hooks
 *
 * SoT: docs/10.module-specs/A1-dashboard.md §2.4 数据刷新策略
 * 技术栈: TanStack Query v5
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { dashboardApi } from '../services/dashboardApi';
import type {
  DashboardOverviewParams,
  DashboardTrendParams,
  DashboardOverviewResponse,
  DashboardTrendResponse,
  DashboardTopProjectsResponse,
  DashboardPendingCountsResponse,
} from '../types/dashboard.types';

// ============ Query Keys ============

/**
 * Dashboard Query Keys
 * 用于缓存管理和查询失效
 */
export const dashboardKeys = {
  all: ['dashboard'] as const,
  overview: () => [...dashboardKeys.all, 'overview'] as const,
  overviewWithParams: (params: DashboardOverviewParams) =>
    [...dashboardKeys.overview(), params] as const,
  trend: () => [...dashboardKeys.all, 'trend'] as const,
  trendWithParams: (params: DashboardTrendParams) =>
    [...dashboardKeys.trend(), params] as const,
  topProjects: () => [...dashboardKeys.all, 'top-projects'] as const,
  pendingCounts: () => [...dashboardKeys.all, 'pending-counts'] as const,
};

// ============ Hooks ============

/**
 * 获取驾驶舱概览数据
 * SoT: A1-dashboard.md §2.4 刷新策略 - 页面加载 + 手动刷新
 */
export function useDashboardOverview(params: DashboardOverviewParams) {
  return useQuery({
    queryKey: dashboardKeys.overviewWithParams(params),
    queryFn: () => dashboardApi.getOverview(params),
    select: (response: DashboardOverviewResponse) => response.data,
    staleTime: 1000 * 60 * 5, // 5 分钟内认为数据是新鲜的
  });
}

/**
 * 获取趋势数据
 * SoT: A1-dashboard.md §2.4 刷新策略 - 时间范围变化时
 */
export function useDashboardTrend(params: DashboardTrendParams) {
  return useQuery({
    queryKey: dashboardKeys.trendWithParams(params),
    queryFn: () => dashboardApi.getTrend(params),
    select: (response: DashboardTrendResponse) => response.data,
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * 获取 Top 项目列表
 * SoT: A1-dashboard.md §2.4 刷新策略 - 页面加载
 */
export function useDashboardTopProjects() {
  return useQuery({
    queryKey: dashboardKeys.topProjects(),
    queryFn: () => dashboardApi.getTopProjects(),
    select: (response: DashboardTopProjectsResponse) => response.data,
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * 获取待处理数量
 * SoT: A1-dashboard.md §2.4 刷新策略 - 实时 (5 分钟轮询)
 */
export function useDashboardPendingCounts() {
  return useQuery({
    queryKey: dashboardKeys.pendingCounts(),
    queryFn: () => dashboardApi.getPendingCounts(),
    select: (response: DashboardPendingCountsResponse) => response.data,
    staleTime: 1000 * 60 * 5,
    refetchInterval: 1000 * 60 * 5, // 5 分钟轮询
  });
}

// ============ 组合 Hook ============

/**
 * 获取完整的驾驶舱数据
 * 组合多个查询，提供统一的加载和错误状态
 */
export function useDashboardData(dateRange: { from: string; to: string }) {
  const params: DashboardOverviewParams = {
    date_from: dateRange.from,
    date_to: dateRange.to,
  };

  const overview = useDashboardOverview(params);
  const trend = useDashboardTrend(params);
  const topProjects = useDashboardTopProjects();
  const pendingCounts = useDashboardPendingCounts();

  const isLoading =
    overview.isLoading ||
    trend.isLoading ||
    topProjects.isLoading ||
    pendingCounts.isLoading;

  const isError =
    overview.isError ||
    trend.isError ||
    topProjects.isError ||
    pendingCounts.isError;

  const error =
    overview.error || trend.error || topProjects.error || pendingCounts.error;

  return {
    overview: overview.data,
    trend: trend.data,
    topProjects: topProjects.data,
    pendingCounts: pendingCounts.data,
    isLoading,
    isError,
    error,
    // 单独暴露各查询的状态，供细粒度控制
    queries: {
      overview,
      trend,
      topProjects,
      pendingCounts,
    },
  };
}

// ============ 刷新函数 ============

/**
 * 使用 queryClient 刷新所有驾驶舱数据
 */
export function useRefreshDashboard() {
  const queryClient = useQueryClient();

  return {
    refreshAll: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.all });
    },
    refreshOverview: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.overview() });
    },
    refreshTrend: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.trend() });
    },
    refreshTopProjects: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.topProjects() });
    },
    refreshPendingCounts: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.pendingCounts() });
    },
  };
}
