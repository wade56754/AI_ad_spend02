/**
 * Import Jobs Hooks
 *
 * TanStack Query v5 hooks for import-jobs module
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
import type { ImportJobListParams } from '../types';

/** Query Keys */
export const importJobsKeys = {
  all: ['importJobs'] as const,
  lists: () => [...importJobsKeys.all, 'list'] as const,
  list: (params?: ImportJobListParams) => [...importJobsKeys.lists(), params] as const,
  details: () => [...importJobsKeys.all, 'detail'] as const,
  detail: (id: number) => [...importJobsKeys.details(), id] as const,
  progress: (id: number) => [...importJobsKeys.all, 'progress', id] as const,
  statistics: () => [...importJobsKeys.all, 'statistics'] as const,
};

/** 获取导入任务列表 */
export function useImportJobs(params?: ImportJobListParams) {
  return useQuery({
    queryKey: importJobsKeys.list(params),
    queryFn: () => getImportJobs(params),
  });
}

/** 获取导入任务详情 */
export function useImportJob(id: number) {
  return useQuery({
    queryKey: importJobsKeys.detail(id),
    queryFn: () => getImportJob(id),
    enabled: !!id,
  });
}

/** 获取导入任务进度 */
export function useImportJobProgress(id: number, options?: { enabled?: boolean; refetchInterval?: number }) {
  return useQuery({
    queryKey: importJobsKeys.progress(id),
    queryFn: () => getImportJobProgress(id),
    enabled: options?.enabled !== false && !!id,
    refetchInterval: options?.refetchInterval,
  });
}

/** 获取导入任务统计 */
export function useImportJobStatistics() {
  return useQuery({
    queryKey: importJobsKeys.statistics(),
    queryFn: () => getImportJobStatistics(),
  });
}

/** 上传导入文件 */
export function useUploadImportFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, jobType }: { file: File; jobType: string }) =>
      uploadImportFile(file, jobType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importJobsKeys.lists() });
      queryClient.invalidateQueries({ queryKey: importJobsKeys.statistics() });
    },
  });
}

/** 开始处理导入任务 */
export function useStartImportJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => startImportJob(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: importJobsKeys.lists() });
      queryClient.invalidateQueries({ queryKey: importJobsKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: importJobsKeys.statistics() });
    },
  });
}

/** 取消导入任务 */
export function useCancelImportJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => cancelImportJob(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: importJobsKeys.lists() });
      queryClient.invalidateQueries({ queryKey: importJobsKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: importJobsKeys.statistics() });
    },
  });
}

/** 删除导入任务 */
export function useDeleteImportJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deleteImportJob(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importJobsKeys.lists() });
      queryClient.invalidateQueries({ queryKey: importJobsKeys.statistics() });
    },
  });
}
