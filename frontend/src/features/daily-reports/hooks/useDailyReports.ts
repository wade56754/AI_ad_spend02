/**
 * Daily Reports React Query Hooks
 *
 * TanStack Query v5 hooks for daily reports data fetching and mutations
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';
import {
  getDailyReports,
  getDailyReport,
  getDailyReportsByProject,
  createDailyReport,
  updateDailyReport,
  deleteDailyReport,
  submitForTrend,
  approveTrend,
  flagTrend,
  resolveFlag,
  submitForFinal,
  confirmFinal,
  lockReport,
  bulkSubmitForTrend,
  getDailyReportStats,
} from '../services';
import type {
  DailyReport,
  DailyReportListParams,
  DailyReportCreateInput,
  DailyReportUpdateInput,
  TrendResolveInput,
  FinalConfirmInput,
  DailyReportStatus,
} from '../types';

// === Query Hooks ===

/**
 * Fetch paginated daily reports list
 */
export function useDailyReports(
  params: DailyReportListParams = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<DailyReport>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.dailyReports.list(params as Record<string, unknown>),
    queryFn: () => getDailyReports(params),
    ...options,
  });
}

/**
 * Fetch single daily report by ID
 */
export function useDailyReport(
  id: string,
  options?: Omit<UseQueryOptions<DailyReport>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.dailyReports.detail(id),
    queryFn: () => getDailyReport(id),
    enabled: !!id,
    ...options,
  });
}

/**
 * Fetch daily reports by project
 */
export function useDailyReportsByProject(
  projectId: string,
  params: Omit<DailyReportListParams, 'project_id'> = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<DailyReport>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.dailyReports.byProject(projectId, params),
    queryFn: () => getDailyReportsByProject(projectId, params),
    enabled: !!projectId,
    ...options,
  });
}

/**
 * Fetch daily report statistics
 */
export function useDailyReportStats(
  params: { project_id?: string; start_date?: string; end_date?: string } = {},
  options?: Omit<UseQueryOptions<Record<DailyReportStatus, number>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...queryKeys.dailyReports.all, 'stats', params],
    queryFn: () => getDailyReportStats(params),
    ...options,
  });
}

// === Mutation Hooks ===

/**
 * Create daily report mutation
 */
export function useCreateDailyReport(
  options?: UseMutationOptions<DailyReport, Error, DailyReportCreateInput>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createDailyReport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.dailyReports.all });
    },
    ...options,
  });
}

/**
 * Update daily report mutation
 */
export function useUpdateDailyReport(
  options?: UseMutationOptions<DailyReport, Error, { id: string; input: DailyReportUpdateInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => updateDailyReport(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.dailyReports.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.dailyReports.lists() });
    },
    ...options,
  });
}

/**
 * Delete daily report mutation
 */
export function useDeleteDailyReport(
  options?: UseMutationOptions<void, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDailyReport,
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: queryKeys.dailyReports.detail(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.dailyReports.lists() });
    },
    ...options,
  });
}

// === State Transition Hooks ===

/**
 * Submit for trend analysis
 * raw_submitted → trend_pending
 */
export function useSubmitForTrend(
  options?: UseMutationOptions<DailyReport, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: submitForTrend,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.dailyReports.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.dailyReports.lists() });
    },
    ...options,
  });
}

/**
 * Approve trend
 * trend_pending → trend_ok
 */
export function useApproveTrend(
  options?: UseMutationOptions<DailyReport, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: approveTrend,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.dailyReports.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.dailyReports.lists() });
    },
    ...options,
  });
}

/**
 * Flag trend anomaly
 * trend_pending → trend_flagged
 */
export function useFlagTrend(
  options?: UseMutationOptions<DailyReport, Error, { id: string; notes: string }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, notes }) => flagTrend(id, notes),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.dailyReports.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.dailyReports.lists() });
    },
    ...options,
  });
}

/**
 * Resolve trend flag
 * trend_flagged → trend_resolved
 */
export function useResolveFlag(
  options?: UseMutationOptions<DailyReport, Error, { id: string; input: TrendResolveInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => resolveFlag(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.dailyReports.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.dailyReports.lists() });
    },
    ...options,
  });
}

/**
 * Submit for final confirmation
 * trend_ok | trend_resolved → final_pending
 */
export function useSubmitForFinal(
  options?: UseMutationOptions<DailyReport, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: submitForFinal,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.dailyReports.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.dailyReports.lists() });
    },
    ...options,
  });
}

/**
 * Confirm final data
 * final_pending → final_confirmed
 */
export function useConfirmFinal(
  options?: UseMutationOptions<DailyReport, Error, { id: string; input: FinalConfirmInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => confirmFinal(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.dailyReports.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.dailyReports.lists() });
    },
    ...options,
  });
}

/**
 * Lock report
 * final_confirmed → final_locked
 */
export function useLockReport(
  options?: UseMutationOptions<DailyReport, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: lockReport,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.dailyReports.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.dailyReports.lists() });
    },
    ...options,
  });
}

/**
 * Bulk submit for trend
 */
export function useBulkSubmitForTrend(
  options?: UseMutationOptions<
    { success: string[]; failed: { id: string; error: string }[] },
    Error,
    string[]
  >
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: bulkSubmitForTrend,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.dailyReports.all });
    },
    ...options,
  });
}
