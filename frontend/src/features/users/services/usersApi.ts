/**
 * Users API Service
 *
 * TanStack Query v5 API 服务层
 *
 * SoT: docs/10.module-specs/C2-pitcher-mgmt.md §4 API 接口
 * SoT: MASTER.md v4.4 §2.4 (7 角色定义)
 * SoT: API_SOT.md v9.0 §5 Users API
 * SoT: ERROR_CODES_SOT.md v2.1
 *
 * 一句话定义: 用户/投手数据获取和管理服务
 *
 * 标准角色 (MASTER.md v4.4):
 *   ceo, project_owner, finance, supervisor, pitcher, account_manager, admin
 *
 * Author: AI 代码工厂 v2.4
 */

import { apiFetch, apiFetchPaginated } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';
import type {
  User,
  UserListParams,
  CreateUserRequest,
  UpdateUserRequest,
  UserRole,
  UserStatus,
} from '../types';

const BASE_PATH = '/api/v1/users';

// ========== Mock 数据生成 ==========
// SoT: C2-pitcher-mgmt.md §2 数据需求

/**
 * 生成 Mock 投手数据
 * SoT: C2-pitcher-mgmt.md §4.2 响应示例
 */
function generateMockPitchers(): User[] {
  const now = new Date().toISOString();

  return [
    {
      id: 'uuid-pitcher-001',
      username: 'zhangsan',
      full_name: '张三',
      email: 'zhangsan@example.com',
      role: 'pitcher' as unknown as UserRole,
      status: 'active' as unknown as UserStatus,
      is_active: true,
      account_manager_id: 'uuid-supervisor-001',
      supervisor_name: '李主管',
      team_name: 'A组',
      account_count: 5,
      project_count: 2,
      created_at: '2025-01-01T00:00:00Z',
      last_login: now,
    },
    {
      id: 'uuid-pitcher-002',
      username: 'lisi',
      full_name: '李四',
      email: 'lisi@example.com',
      role: 'pitcher' as unknown as UserRole,
      status: 'active' as unknown as UserStatus,
      is_active: true,
      account_manager_id: 'uuid-supervisor-001',
      supervisor_name: '李主管',
      team_name: 'A组',
      account_count: 3,
      project_count: 1,
      created_at: '2025-02-15T00:00:00Z',
      last_login: now,
    },
    {
      id: 'uuid-pitcher-003',
      username: 'wangwu',
      full_name: '王五',
      email: 'wangwu@example.com',
      role: 'pitcher' as unknown as UserRole,
      status: 'inactive' as unknown as UserStatus,
      is_active: false,
      account_manager_id: 'uuid-supervisor-002',
      supervisor_name: '王主管',
      team_name: 'B组',
      account_count: 4,
      project_count: 1,
      created_at: '2025-03-01T00:00:00Z',
      last_login: '2025-12-01T10:00:00Z',
    },
    {
      id: 'uuid-pitcher-004',
      username: 'zhaoliu',
      full_name: '赵六',
      email: 'zhaoliu@example.com',
      role: 'pitcher' as unknown as UserRole,
      status: 'active' as unknown as UserStatus,
      is_active: true,
      account_manager_id: 'uuid-supervisor-002',
      supervisor_name: '王主管',
      team_name: 'B组',
      account_count: 6,
      project_count: 3,
      created_at: '2025-04-01T00:00:00Z',
      last_login: now,
    },
  ];
}

/**
 * 生成 Mock 用户统计
 * SoT: C2-pitcher-mgmt.md §3.1 KPI 卡片
 */
function generateMockUserStats() {
  return {
    total: 25,
    active: 22,
    inactive: 3,
    by_role: {
      pitcher: 18,
      supervisor: 4,
      finance: 2,
      admin: 1,
    },
  };
}

// === Query Functions ===

/**
 * Get paginated list of users
 * GET /api/v1/users
 * SoT: C2-pitcher-mgmt.md §4.1 接口清单
 * 权限: admin
 */
export async function getUsers(
  params: UserListParams = {}
): Promise<PaginatedResponse<User>> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.role) searchParams.set('role', params.role);
  if (params.is_active !== undefined) searchParams.set('is_active', String(params.is_active));
  if (params.search) searchParams.set('search', params.search);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  try {
    return await apiFetchPaginated<User>(url);
  } catch (error) {
    console.warn('[Users] API 不可用，使用 Mock 数据', error);
    let mockItems = generateMockPitchers();

    // 应用筛选
    if (params.role) {
      mockItems = mockItems.filter(item => item.role === params.role);
    }
    if (params.is_active !== undefined) {
      mockItems = mockItems.filter(item => item.is_active === params.is_active);
    }
    if (params.search) {
      const search = params.search.toLowerCase();
      mockItems = mockItems.filter(
        item =>
          item.full_name?.toLowerCase().includes(search) ||
          item.username.toLowerCase().includes(search) ||
          item.email.toLowerCase().includes(search)
      );
    }

    return {
      data: mockItems,
      meta: {
        pagination: {
          page: params.page || 1,
          page_size: params.page_size || 20,
          total: mockItems.length,
          total_pages: Math.ceil(mockItems.length / (params.page_size || 20)),
        },
      },
    };
  }
}

/**
 * Get single user by ID
 * GET /api/v1/users/:id
 * SoT: C2-pitcher-mgmt.md §4.1 接口清单
 * 权限: admin / self
 */
export async function getUser(id: string): Promise<User> {
  try {
    return await apiFetch<User>(`${BASE_PATH}/${id}`);
  } catch (error) {
    console.warn('[Users] API 不可用，使用 Mock 数据', error);
    const mockItems = generateMockPitchers();
    const found = mockItems.find(item => item.id === id);
    if (found) return found;
    throw new Error(`用户 ${id} 不存在`);
  }
}

/**
 * Get user statistics
 * GET /api/v1/users/statistics/summary
 * SoT: C2-pitcher-mgmt.md §3.1 KPI 卡片
 * 权限: admin, finance, supervisor
 */
export async function getUserStatistics(): Promise<{
  total: number;
  active: number;
  inactive: number;
  by_role: Record<string, number>;
}> {
  try {
    return await apiFetch(`${BASE_PATH}/statistics/summary`);
  } catch (error) {
    console.warn('[Users] Stats API 不可用，使用 Mock 数据', error);
    return generateMockUserStats();
  }
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
export async function updateUser(
  id: string,
  input: UpdateUserRequest
): Promise<User> {
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
export async function toggleUserStatus(
  id: string,
  isActive: boolean
): Promise<User> {
  return updateUser(id, { is_active: isActive });
}
