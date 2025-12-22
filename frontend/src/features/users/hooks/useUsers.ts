/**
 * Users React Query Hooks
 *
 * TanStack Query v5 hooks for user management
 *
 * SoT References:
 * - API_SOT.md v9.0 §5 Users API
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
