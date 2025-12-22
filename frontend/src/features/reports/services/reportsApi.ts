/**
 * Reports API Service
 *
 * SoT 对齐:
 * - backend/routers/reports.py v2.0
 * - backend/services/reports_service.py
 */

import { apiFetch } from '@/lib/api';
import type {
  DashboardSummary,
  PerformanceReportResponse,
  ProfitReportResponse,
  ReconciliationReportResponse,
  FinancialSummaryResponse,
  TrendReportResponse,
  ReportQueryParams,
  TrendReportParams,
  TrendMetric,
} from '../types';

const BASE_PATH = '/api/v1/reports';

// ========== Dashboard ==========

/**
 * Get dashboard summary
 * GET /api/v1/reports/dashboard
 */
export async function getDashboard(): Promise<DashboardSummary> {
  // apiFetch already extracts .data from the envelope
  return apiFetch<DashboardSummary>(`${BASE_PATH}/dashboard`);
}

// ========== Performance Report ==========

/**
 * Get performance report
 * GET /api/v1/reports/performance
 */
export async function getPerformanceReport(
  params: ReportQueryParams = {}
): Promise<PerformanceReportResponse> {
  const searchParams = new URLSearchParams();

  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.project_ids) searchParams.set('project_ids', params.project_ids);
  if (params.channel_ids) searchParams.set('channel_ids', params.channel_ids);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/performance?${query}` : `${BASE_PATH}/performance`;

  // apiFetch already extracts .data from the envelope
  return apiFetch<PerformanceReportResponse>(url);
}

// ========== Profit Report ==========

/**
 * Get profit report
 * GET /api/v1/reports/profit
 */
export async function getProfitReport(
  params: ReportQueryParams = {}
): Promise<ProfitReportResponse> {
  const searchParams = new URLSearchParams();

  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.project_ids) searchParams.set('project_ids', params.project_ids);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/profit?${query}` : `${BASE_PATH}/profit`;

  // apiFetch already extracts .data from the envelope
  return apiFetch<ProfitReportResponse>(url);
}

// ========== Reconciliation Report ==========

/**
 * Get reconciliation report
 * GET /api/v1/reports/reconciliation
 */
export async function getReconciliationReport(
  params: Pick<ReportQueryParams, 'start_date' | 'end_date'> = {}
): Promise<ReconciliationReportResponse> {
  const searchParams = new URLSearchParams();

  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/reconciliation?${query}` : `${BASE_PATH}/reconciliation`;

  // apiFetch already extracts .data from the envelope
  return apiFetch<ReconciliationReportResponse>(url);
}

// ========== Financial Summary ==========

/**
 * Get financial summary
 * GET /api/v1/reports/financial
 */
export async function getFinancialSummary(
  params: ReportQueryParams = {}
): Promise<FinancialSummaryResponse> {
  const searchParams = new URLSearchParams();

  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.project_ids) searchParams.set('project_ids', params.project_ids);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/financial?${query}` : `${BASE_PATH}/financial`;

  // apiFetch already extracts .data from the envelope
  return apiFetch<FinancialSummaryResponse>(url);
}

// ========== Trend Report ==========

/**
 * Get trend report
 * GET /api/v1/reports/trends/{metric}
 */
export async function getTrendReport(
  params: TrendReportParams
): Promise<TrendReportResponse> {
  const { metric, ...queryParams } = params;
  const searchParams = new URLSearchParams();

  if (queryParams.period) searchParams.set('period', queryParams.period);
  if (queryParams.start_date) searchParams.set('start_date', queryParams.start_date);
  if (queryParams.end_date) searchParams.set('end_date', queryParams.end_date);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/trends/${metric}?${query}` : `${BASE_PATH}/trends/${metric}`;

  // apiFetch already extracts .data from the envelope
  return apiFetch<TrendReportResponse>(url);
}
