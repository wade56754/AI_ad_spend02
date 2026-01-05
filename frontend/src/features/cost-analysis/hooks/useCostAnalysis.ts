/**
 * Cost Analysis Hooks
 */

import { useQuery } from '@tanstack/react-query';
import {
  getCostAnalysis,
  getCostSummary,
  getCostBreakdown,
  getCostTrends,
  type CostAnalysisParams,
} from '../services';

/**
 * Hook to fetch cost analysis data
 */
export function useCostAnalysis(params: CostAnalysisParams = {}) {
  return useQuery({
    queryKey: ['cost-analysis', params],
    queryFn: () => getCostAnalysis(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch cost summary
 */
export function useCostSummary(params: CostAnalysisParams = {}) {
  return useQuery({
    queryKey: ['cost-analysis', 'summary', params],
    queryFn: () => getCostSummary(params),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook to fetch cost breakdown
 */
export function useCostBreakdown(params: CostAnalysisParams = {}) {
  return useQuery({
    queryKey: ['cost-analysis', 'breakdown', params],
    queryFn: () => getCostBreakdown(params),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook to fetch cost trends
 */
export function useCostTrends(params: CostAnalysisParams = {}) {
  return useQuery({
    queryKey: ['cost-analysis', 'trends', params],
    queryFn: () => getCostTrends(params),
    staleTime: 5 * 60 * 1000,
  });
}
