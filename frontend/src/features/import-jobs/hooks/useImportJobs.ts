/**
 * Import Jobs React Query Hooks
 *
 * TanStack Query v5 hooks for import-jobs module
 * SoT 对齐: DATA_SCHEMA.md v5.2
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
  getImportJobs,
  getImportJob,
  getImportJobProgress,
  getImportJobStatistics,
  startImportJob,
  cancelImportJob,
  deleteImportJob,
  uploadImportFile,
} from '../services';
import type {
  ImportJob,
  ImportJobListParams,
  ImportJobProgress,
  ImportJobStatistics,
} from '../types';

// ========== Query Hooks ==========

/**
 * 获取导入任务列表
 */
export function useImportJobs(
  params: ImportJobListParams = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<ImportJob>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.importJobs.list(params as Record<string, any>),
    queryFn: () => getImportJobs(params),
    ...options,
  });
}

/**
 * 获取导入任务详情
 */
export function useImportJob(
  id: number,
  options?: Omit<UseQueryOptions<ImportJob>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.importJobs.detail(String(id)),
    queryFn: () => getImportJob(id),
    enabled: !!id,
    ...options,
  });
}

/**
 * 获取导入任务进度
 * 支持轮询模式用于实时更新
 */
export function useImportJobProgress(
  id: number,
  options?: {
    enabled?: boolean;
    refetchInterval?: number;
  } & Omit<UseQueryOptions<ImportJobProgress>, 'queryKey' | 'queryFn' | 'enabled' | 'refetchInterval'>
) {
  const { enabled, refetchInterval, ...restOptions } = options || {};

  return useQuery({
    queryKey: queryKeys.importJobs.progress(String(id)),
    queryFn: () => getImportJobProgress(id),
    enabled: enabled !== false && !!id,
    refetchInterval,
    ...restOptions,
  });
}

/**
 * 获取导入任务统计
 */
export function useImportJobStatistics(
  options?: Omit<UseQueryOptions<ImportJobStatistics>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.importJobs.statistics(),
    queryFn: getImportJobStatistics,
    ...options,
  });
}

// ========== Mutation Hooks ==========

/**
 * 上传导入文件
 */
export function useUploadImportFile(
  options?: UseMutationOptions<ImportJob, Error, { file: File; jobType: string }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, jobType }) => uploadImportFile(file, jobType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.importJobs.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.importJobs.statistics() });
    },
    ...options,
  });
}

/**
 * 开始处理导入任务
 */
export function useStartImportJob(
  options?: UseMutationOptions<ImportJob, Error, number>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: startImportJob,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.importJobs.detail(String(id)), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.importJobs.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.importJobs.statistics() });
    },
    ...options,
  });
}

/**
 * 取消导入任务
 */
export function useCancelImportJob(
  options?: UseMutationOptions<ImportJob, Error, number>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelImportJob,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.importJobs.detail(String(id)), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.importJobs.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.importJobs.progress(String(id)) });
      queryClient.invalidateQueries({ queryKey: queryKeys.importJobs.statistics() });
    },
    ...options,
  });
}

/**
 * 删除导入任务
 */
export function useDeleteImportJob(
  options?: UseMutationOptions<void, Error, number>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteImportJob,
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: queryKeys.importJobs.detail(String(id)) });
      queryClient.removeQueries({ queryKey: queryKeys.importJobs.progress(String(id)) });
      queryClient.invalidateQueries({ queryKey: queryKeys.importJobs.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.importJobs.statistics() });
    },
    ...options,
  });
}
