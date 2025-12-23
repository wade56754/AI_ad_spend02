/**
 * Users React Query Hooks
 *
 * TanStack Query v5 hooks for user management
 *
 * SoT: docs/10.module-specs/C2-pitcher-mgmt.md §6.1 前端代码块
 * SoT: MASTER.md v4.4 §2.4 (7 角色定义)
 * SoT: API_SOT.md v9.0 §5 Users API
 *
 * 一句话定义: 管理用户/投手的数据获取和状态变更
 *
 * 标准角色 (MASTER.md v4.4):
 *   ceo, project_owner, finance, supervisor, pitcher, account_manager, admin
 *
 * Author: AI 代码工厂 v2.4
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from '@tanstack/react-query';
import type { PaginatedResponse } from '@/lib/api';
import {
  getUsers,
  getUser,
  getUserStatistics,
  createUser,
  updateUser,
  deleteUser,
  toggleUserStatus,
} from '../services';
import type {
  User,
  UserListParams,
  CreateUserRequest,
  UpdateUserRequest,
} from '../types';

// === Query Keys ===
export const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (params: UserListParams) => [...userKeys.lists(), params] as const,
  details: () => [...userKeys.all, 'detail'] as const,
  detail: (id: string) => [...userKeys.details(), id] as const,
  statistics: () => [...userKeys.all, 'statistics'] as const,
};

// === Query Hooks ===

/**
 * Fetch paginated user list
 */
export function useUsers(
  params: UserListParams = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<User>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: userKeys.list(params),
    queryFn: () => getUsers(params),
    ...options,
  });
}

/**
 * Fetch single user by ID
 */
export function useUser(
  id: string,
  options?: Omit<UseQueryOptions<User>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: userKeys.detail(id),
    queryFn: () => getUser(id),
    enabled: !!id,
    ...options,
  });
}

/**
 * Fetch user statistics
 */
export function useUserStatistics(
  options?: Omit<UseQueryOptions<{
    total: number;
    active: number;
    inactive: number;
    by_role: Record<string, number>;
  }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: userKeys.statistics(),
    queryFn: () => getUserStatistics(),
    ...options,
  });
}

// === Mutation Hooks ===

/**
 * Create user mutation
 */
export function useCreateUser(
  options?: UseMutationOptions<User, Error, CreateUserRequest>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      queryClient.invalidateQueries({ queryKey: userKeys.statistics() });
    },
    ...options,
  });
}

/**
 * Update user mutation
 */
export function useUpdateUser(
  options?: UseMutationOptions<User, Error, { id: string; data: UpdateUserRequest }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => updateUser(id, data),
    onSuccess: (user) => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      queryClient.invalidateQueries({ queryKey: userKeys.detail(user.id) });
      queryClient.invalidateQueries({ queryKey: userKeys.statistics() });
    },
    ...options,
  });
}

/**
 * Delete user mutation
 */
export function useDeleteUser(
  options?: UseMutationOptions<{ user_id: string }, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      queryClient.invalidateQueries({ queryKey: userKeys.statistics() });
    },
    ...options,
  });
}

/**
 * Toggle user status mutation
 */
export function useToggleUserStatus(
  options?: UseMutationOptions<User, Error, { id: string; isActive: boolean }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, isActive }) => toggleUserStatus(id, isActive),
    onSuccess: (user) => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      queryClient.invalidateQueries({ queryKey: userKeys.detail(user.id) });
      queryClient.invalidateQueries({ queryKey: userKeys.statistics() });
    },
    ...options,
  });
}

// ========== Refresh Hook ==========

/**
 * 刷新用户/投手数据
 * SoT: C2-pitcher-mgmt.md 数据刷新策略
 *
 * @example
 * ```tsx
 * const { refreshAll, refreshList, refreshStats } = useRefreshUsers();
 * // 刷新所有用户数据
 * refreshAll();
 * // 仅刷新列表
 * refreshList();
 * // 仅刷新统计
 * refreshStats();
 * ```
 */
export function useRefreshUsers() {
  const queryClient = useQueryClient();

  return {
    /** 刷新所有用户数据 */
    refreshAll: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
    /** 刷新用户列表 */
    refreshList: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
    /** 刷新用户统计 */
    refreshStats: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.statistics() });
    },
    /** 刷新单个用户详情 */
    refreshDetail: (id: string) => {
      queryClient.invalidateQueries({ queryKey: userKeys.detail(id) });
    },
  };
}
