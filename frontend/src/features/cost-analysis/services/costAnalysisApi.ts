/**
 * Cost Analysis API Service
 */

import { apiGet } from '@/lib/api';
import type { CostAnalysisData, CostSummary, CostBreakdown, CostTrend } from '../types';

const BASE_PATH = '/api/v1/cost-analysis';

export interface CostAnalysisParams {
  start_date?: string;
  end_date?: string;
  project_id?: number;
  account_id?: number;
}

/**
 * Get cost analysis data
 */
export async function getCostAnalysis(params: CostAnalysisParams = {}): Promise<CostAnalysisData> {
  const searchParams = new URLSearchParams();
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.project_id) searchParams.set('project_id', String(params.project_id));
  if (params.account_id) searchParams.set('account_id', String(params.account_id));

  const query = searchParams.toString();
  return apiGet<CostAnalysisData>(`${BASE_PATH}?${query}`);
}

/**
 * Get cost summary
 */
export async function getCostSummary(params: CostAnalysisParams = {}): Promise<CostSummary> {
  const searchParams = new URLSearchParams();
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  return apiGet<CostSummary>(`${BASE_PATH}/summary?${query}`);
}

/**
 * Get cost breakdown by category
 */
export async function getCostBreakdown(params: CostAnalysisParams = {}): Promise<CostBreakdown[]> {
  const searchParams = new URLSearchParams();
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  return apiGet<CostBreakdown[]>(`${BASE_PATH}/breakdown?${query}`);
}

/**
 * Get cost trends over time
 */
export async function getCostTrends(params: CostAnalysisParams = {}): Promise<CostTrend[]> {
  const searchParams = new URLSearchParams();
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const query = searchParams.toString();
  return apiGet<CostTrend[]>(`${BASE_PATH}/trends?${query}`);
}
