/**
 * Projects React Query Hooks
 *
 * TanStack Query v5 hooks for project management
 *
 * SoT: docs/10.module-specs/C1-project-mgmt.md §4 API 接口
 * SoT: DATA_SCHEMA.md v5.2 (projects entity)
 * SoT: STATE_MACHINE.md v2.6 Section 5 (项目状态机)
 *
 * @module features/projects/hooks
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import {
  getProjects,
  getProject,
  getProjectStatistics,
  getProjectMembers,
  getProjectDashboard,
  createProject,
  updateProject,
  deleteProject,
  assignMember,
  removeMember,
  getPrepaymentBalance,
  getPrepaymentEntries,
  createPrepayment,
  createPrepaymentReversal,
} from '../services';
import type {
  Project,
  ProjectMember,
  ProjectStatistics,
  ProjectDashboardData,
  ProjectListParams,
  ProjectCreateInput,
  ProjectUpdateInput,
  ProjectMemberAssignInput,
  ProjectDashboardParams,
  PrepaymentBalance,
  PrepaymentEntry,
  PrepaymentListParams,
  PrepaymentCreateInput,
  PrepaymentReversalInput,
} from '../types';

// ========== Query Hooks ==========

export function useProjects(
  params: ProjectListParams = {},
  options?: Omit<
    UseQueryOptions<{
      data: Project[];
      meta: { pagination: { page: number; page_size: number; total: number; total_pages: number } };
    }>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery({
    queryKey: queryKeys.projects.list(params),
    queryFn: () => getProjects(params),
    ...options,
  });
}

export function useProject(
  id: number,
  options?: Omit<UseQueryOptions<{ data: Project }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.projects.detail(id),
    queryFn: () => getProject(id),
    enabled: !!id,
    ...options,
  });
}

export function useProjectStatistics(
  options?: Omit<UseQueryOptions<{ data: ProjectStatistics }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...queryKeys.projects.all, 'statistics'],
    queryFn: getProjectStatistics,
    ...options,
  });
}

export function useProjectMembers(
  projectId: number,
  options?: Omit<UseQueryOptions<{ data: ProjectMember[] }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.projects.members(projectId),
    queryFn: () => getProjectMembers(projectId),
    enabled: !!projectId,
    ...options,
  });
}

/**
 * 获取项目仪表盘数据
 * TASK-PRJ-004
 */
export function useProjectDashboard(
  projectId: number,
  params: ProjectDashboardParams = {},
  options?: Omit<UseQueryOptions<{ data: ProjectDashboardData }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...queryKeys.projects.detail(projectId), 'dashboard', params],
    queryFn: () => getProjectDashboard(projectId, params),
    enabled: !!projectId,
    staleTime: 2 * 60 * 1000, // 2 分钟
    ...options,
  });
}

// ========== Mutation Hooks ==========

export function useCreateProject(
  options?: UseMutationOptions<{ data: Project }, Error, ProjectCreateInput>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
    ...options,
  });
}

export function useUpdateProject(
  options?: UseMutationOptions<{ data: Project }, Error, { id: number; input: ProjectUpdateInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => updateProject(id, input),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.detail(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.lists() });
    },
    ...options,
  });
}

export function useDeleteProject(options?: UseMutationOptions<void, Error, number>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
    ...options,
  });
}

export function useAssignMember(
  options?: UseMutationOptions<
    { data: ProjectMember },
    Error,
    { projectId: number; input: ProjectMemberAssignInput }
  >
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, input }) => assignMember(projectId, input),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.members(projectId) });
    },
    ...options,
  });
}

export function useRemoveMember(
  options?: UseMutationOptions<void, Error, { projectId: number; userId: string }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, userId }) => removeMember(projectId, userId),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.members(projectId) });
    },
    ...options,
  });
}

// ========== Prepayment Hooks (TASK-PRJ-005) ==========

/**
 * 获取项目预付款余额
 * TASK-PRJ-005: 三本账体系 - 预付款账本
 */
export function usePrepaymentBalance(
  projectId: number,
  options?: Omit<UseQueryOptions<{ data: PrepaymentBalance }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...queryKeys.projects.detail(projectId), 'prepayments', 'balance'],
    queryFn: () => getPrepaymentBalance(projectId),
    enabled: !!projectId,
    staleTime: 2 * 60 * 1000,
    ...options,
  });
}

/**
 * 获取项目预付款流水列表
 * TASK-PRJ-005
 */
export function usePrepaymentEntries(
  projectId: number,
  params: PrepaymentListParams = {},
  options?: Omit<
    UseQueryOptions<{
      data: PrepaymentEntry[];
      meta: { pagination: { page: number; page_size: number; total: number; total_pages: number } };
    }>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery({
    queryKey: [...queryKeys.projects.detail(projectId), 'prepayments', 'list', params],
    queryFn: () => getPrepaymentEntries(projectId, params),
    enabled: !!projectId,
    staleTime: 2 * 60 * 1000,
    ...options,
  });
}

/**
 * 添加预付款入账
 * TASK-PRJ-005
 */
export function useCreatePrepayment(
  options?: UseMutationOptions<
    { data: PrepaymentEntry },
    Error,
    { projectId: number; input: PrepaymentCreateInput }
  >
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, input }) => createPrepayment(projectId, input),
    onSuccess: (_, { projectId }) => {
      // 刷新余额和流水列表
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.projects.detail(projectId), 'prepayments'],
      });
    },
    ...options,
  });
}

/**
 * 添加预付款红冲
 * TASK-PRJ-005
 */
export function useCreatePrepaymentReversal(
  options?: UseMutationOptions<
    { data: PrepaymentEntry },
    Error,
    { projectId: number; input: PrepaymentReversalInput }
  >
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, input }) => createPrepaymentReversal(projectId, input),
    onSuccess: (_, { projectId }) => {
      // 刷新余额和流水列表
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.projects.detail(projectId), 'prepayments'],
      });
    },
    ...options,
  });
}

// ========== Refresh Hook ==========

/**
 * 刷新项目管理数据
 * SoT: C1-project-mgmt.md §2.4 数据刷新策略
 *
 * @example
 * ```tsx
 * const { refreshAll, refreshList, refreshStatistics } = useRefreshProjects();
 * // 刷新所有项目数据
 * refreshAll();
 * // 仅刷新列表
 * refreshList();
 * ```
 */
export function useRefreshProjects() {
  const queryClient = useQueryClient();

  return {
    /** 刷新所有项目数据 */
    refreshAll: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
    /** 刷新项目列表 */
    refreshList: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.lists() });
    },
    /** 刷新项目统计 */
    refreshStatistics: () => {
      queryClient.invalidateQueries({ queryKey: [...queryKeys.projects.all, 'statistics'] });
    },
    /** 刷新单个项目详情 */
    refreshDetail: (id: number) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.detail(id) });
    },
    /** 刷新项目成员 */
    refreshMembers: (projectId: number) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.members(projectId) });
    },
  };
}
