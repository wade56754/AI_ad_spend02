/**
 * Reports React Query Hooks
 *
 * TanStack Query v5 hooks for report analysis
 * SoT 对齐: backend/routers/reports.py v2.0
 */

import {
  useQuery,
  type UseQueryOptions,
} from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import {
  getDashboard,
  getPerformanceReport,
  getProfitReport,
  getReconciliationReport,
  getFinancialSummary,
  getTrendReport,
} from '../services';
import type {
  DashboardSummary,
  PerformanceReportResponse,
  ProfitReportResponse,
  ReconciliationReportResponse,
  FinancialSummaryResponse,
  TrendReportResponse,
  ReportQueryParams,
  TrendReportParams,
} from '../types';

// ========== Dashboard ==========

/**
 * Fetch dashboard summary
 */
export function useDashboard(
  options?: Omit<UseQueryOptions<DashboardSummary>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.reports.dashboard(),
    queryFn: getDashboard,
    staleTime: 1000 * 60 * 2, // 2 minutes
    refetchInterval: 1000 * 60 * 5, // Refresh every 5 minutes
    ...options,
  });
}

// ========== Performance Report ==========

/**
 * Fetch performance report
 */
export function usePerformanceReport(
  params: ReportQueryParams = {},
  options?: Omit<UseQueryOptions<PerformanceReportResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.reports.performance(params),
    queryFn: () => getPerformanceReport(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}

// ========== Profit Report ==========

/**
 * Fetch profit report
 */
export function useProfitReport(
  params: ReportQueryParams = {},
  options?: Omit<UseQueryOptions<ProfitReportResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.reports.profit(params),
    queryFn: () => getProfitReport(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}

// ========== Reconciliation Report ==========

/**
 * Fetch reconciliation report
 */
export function useReconciliationReport(
  params: Pick<ReportQueryParams, 'start_date' | 'end_date'> = {},
  options?: Omit<UseQueryOptions<ReconciliationReportResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.reports.reconciliation(params),
    queryFn: () => getReconciliationReport(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}

// ========== Financial Summary ==========

/**
 * Fetch financial summary
 */
export function useFinancialSummary(
  params: ReportQueryParams = {},
  options?: Omit<UseQueryOptions<FinancialSummaryResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.reports.financial(params),
    queryFn: () => getFinancialSummary(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}

// ========== Trend Report ==========

/**
 * Fetch trend report
 */
export function useTrendReport(
  params: TrendReportParams,
  options?: Omit<UseQueryOptions<TrendReportResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.reports.trends(params),
    queryFn: () => getTrendReport(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}
