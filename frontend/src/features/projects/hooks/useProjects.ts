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
  createProject,
  updateProject,
  deleteProject,
  assignMember,
  removeMember,
} from '../services';
import type {
  Project,
  ProjectMember,
  ProjectStatistics,
  ProjectListParams,
  ProjectCreateInput,
  ProjectUpdateInput,
  ProjectMemberAssignInput,
} from '../types';

// ========== Query Hooks ==========

export function useProjects(
  params: ProjectListParams = {},
  options?: Omit<UseQueryOptions<{ data: Project[]; meta: { pagination: { page: number; page_size: number; total: number; total_pages: number } } }>, 'queryKey' | 'queryFn'>
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

export function useDeleteProject(
  options?: UseMutationOptions<void, Error, number>
) {
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
  options?: UseMutationOptions<{ data: ProjectMember }, Error, { projectId: number; input: ProjectMemberAssignInput }>
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
