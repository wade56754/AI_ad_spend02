/**
 * Dashboard Data Hooks
 *
 * SoT: docs/10.module-specs/A1-dashboard.md §2.4 数据刷新策略
 * 技术栈: TanStack Query v5
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import dashboardApi, { ceoV3Api } from '../services/dashboardApi';
import type {
  CeoV3OverviewResponse,
  CeoV3ProfitSummaryResponse,
  CeoV3ProjectBalanceResponse,
  CeoV3ProjectRankingResponse,
  CeoV3TrendResponse,
  CeoV3ActionItemsResponse,
} from '../services/dashboardApi';
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
      // 清除 API 缓存
      dashboardApi.clearCache();
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

// ============ CEO Dashboard V3 Hooks ============
// 核心公式: 毛利 = 收款 - 消耗 (不含手续费)

/**
 * CEO V3 Query Keys
 */
export const ceoV3Keys = {
  all: ['ceo-v3'] as const,
  overview: (period?: string) => [...ceoV3Keys.all, 'overview', period] as const,
  profitSummary: (period?: string) => [...ceoV3Keys.all, 'profit-summary', period] as const,
  projectBalance: (period?: string) => [...ceoV3Keys.all, 'project-balance', period] as const,
  projectRanking: (period?: string, limit?: number) => [...ceoV3Keys.all, 'project-ranking', period, limit] as const,
  trend: (period?: string, granularity?: string) => [...ceoV3Keys.all, 'trend', period, granularity] as const,
  actionItems: (period?: string) => [...ceoV3Keys.all, 'action-items', period] as const,
};

/**
 * CEO V3 Overview Hook
 */
export function useCeoV3Overview(period?: string) {
  return useQuery({
    queryKey: ceoV3Keys.overview(period),
    queryFn: () => ceoV3Api.getOverview(period),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * CEO V3 Profit Summary Hook
 * 核心公式: 毛利 = 收款 - 消耗
 */
export function useCeoV3ProfitSummary(period?: string) {
  return useQuery({
    queryKey: ceoV3Keys.profitSummary(period),
    queryFn: () => ceoV3Api.getProfitSummary(period),
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * CEO V3 Project Balance Hook
 */
export function useCeoV3ProjectBalance(period?: string) {
  return useQuery({
    queryKey: ceoV3Keys.projectBalance(period),
    queryFn: () => ceoV3Api.getProjectBalance(period),
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * CEO V3 Project Ranking Hook
 */
export function useCeoV3ProjectRanking(period?: string, limit: number = 10) {
  return useQuery({
    queryKey: ceoV3Keys.projectRanking(period, limit),
    queryFn: () => ceoV3Api.getProjectRanking(period, limit),
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * CEO V3 Trend Hook
 */
export function useCeoV3Trend(period?: string, granularity: string = 'daily') {
  return useQuery({
    queryKey: ceoV3Keys.trend(period, granularity),
    queryFn: () => ceoV3Api.getTrend(period, granularity),
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * CEO V3 Action Items Hook
 */
export function useCeoV3ActionItems(period?: string) {
  return useQuery({
    queryKey: ceoV3Keys.actionItems(period),
    queryFn: () => ceoV3Api.getActionItems(period),
    staleTime: 1000 * 60 * 2, // 2 minutes for action items
  });
}

/**
 * Combined CEO V3 Dashboard Data Hook
 */
export function useCeoV3DashboardData(period?: string) {
  const overview = useCeoV3Overview(period);
  const projectRanking = useCeoV3ProjectRanking(period, 10);
  const trend = useCeoV3Trend(period);

  const isLoading = overview.isLoading || projectRanking.isLoading || trend.isLoading;
  const isError = overview.isError || projectRanking.isError || trend.isError;
  const error = overview.error || projectRanking.error || trend.error;

  return {
    overview: overview.data,
    projectRanking: projectRanking.data,
    trend: trend.data,
    isLoading,
    isError,
    error,
    queries: {
      overview,
      projectRanking,
      trend,
    },
  };
}

/**
 * Refresh CEO V3 Dashboard Data
 */
export function useRefreshCeoV3Dashboard() {
  const queryClient = useQueryClient();

  return {
    refreshAll: () => {
      queryClient.invalidateQueries({ queryKey: ceoV3Keys.all });
    },
    refreshOverview: (period?: string) => {
      queryClient.invalidateQueries({ queryKey: ceoV3Keys.overview(period) });
    },
    refreshProjectRanking: (period?: string) => {
      queryClient.invalidateQueries({ queryKey: ceoV3Keys.projectRanking(period) });
    },
    refreshTrend: (period?: string) => {
      queryClient.invalidateQueries({ queryKey: ceoV3Keys.trend(period) });
    },
  };
}
