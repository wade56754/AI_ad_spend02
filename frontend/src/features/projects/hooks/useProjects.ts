/**
 * Projects React Query Hooks
 *
 * TanStack Query v5 hooks for project management
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
