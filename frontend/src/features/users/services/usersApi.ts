/**
 * Users API Service
 *
 * TanStack Query v5 API 服务层
 *
 * SoT: MASTER.md v4.6 §2.4 (6 角色定义)
 * SoT: API_SOT.md v9.0 §5 Users API
 * SoT: ERROR_CODES_SOT.md v2.1
 *
 * 一句话定义: 用户/投手数据获取和管理服务
 *
 * 6 角色白名单 (MASTER.md v4.6 / PRD v2.2):
 *   ceo, project_owner, finance, pitcher, account_manager, admin
 *
 * Author: AI 代码工厂 v2.4
 */

import { apiFetch, apiFetchPaginated } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';
import type { User, UserListParams, CreateUserRequest, UpdateUserRequest } from '../types';

const BASE_PATH = '/api/v1/users';

// === Query Functions ===

/**
 * Get paginated list of users
 * GET /api/v1/users
 * SoT: C2-pitcher-mgmt.md §4.1 接口清单
 * 权限: admin
 */
export async function getUsers(params: UserListParams = {}): Promise<PaginatedResponse<User>> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.role) searchParams.set('role', params.role);
  if (params.is_active !== undefined) searchParams.set('is_active', String(params.is_active));
  if (params.search) searchParams.set('search', params.search);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  return apiFetchPaginated<User>(url);
}

/**
 * Get single user by ID
 * GET /api/v1/users/:id
 * SoT: C2-pitcher-mgmt.md §4.1 接口清单
 * 权限: admin / self
 */
export async function getUser(id: string): Promise<User> {
  return apiFetch<User>(`${BASE_PATH}/${id}`);
}

/**
 * Get user statistics
 * GET /api/v1/users/statistics/summary
 * 权限: admin, finance, project_owner
 */
export async function getUserStatistics(): Promise<{
  total: number;
  active: number;
  inactive: number;
  by_role: Record<string, number>;
}> {
  return apiFetch(`${BASE_PATH}/statistics/summary`);
}

// === Mutation Functions ===

/**
 * Create new user
 * POST /api/v1/users
 * 权限: admin
 */
export async function createUser(input: CreateUserRequest): Promise<User> {
  return apiFetch<User>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
}

/**
 * Update user
 * PUT /api/v1/users/:id
 * 权限: admin
 */
export async function updateUser(id: string, input: UpdateUserRequest): Promise<User> {
  return apiFetch<User>(`${BASE_PATH}/${id}`, {
    method: 'PUT',
    body: input,
  });
}

/**
 * Delete user (soft delete)
 * DELETE /api/v1/users/:id
 * 权限: admin
 */
export async function deleteUser(id: string): Promise<{ user_id: string }> {
  return apiFetch<{ user_id: string }>(`${BASE_PATH}/${id}`, {
    method: 'DELETE',
  });
}

/**
 * Toggle user active status
 * PUT /api/v1/users/:id
 * 权限: admin
 */
export async function toggleUserStatus(id: string, isActive: boolean): Promise<User> {
  return updateUser(id, { is_active: isActive });
}
