/**
 * Projects API Service
 *
 * SoT: docs/10.module-specs/C1-project-mgmt.md §4 API 接口
 * SoT: DATA_SCHEMA.md v5.2 (projects entity)
 * SoT: STATE_MACHINE.md v2.6 Section 5 (项目状态机)
 *
 * 注意: 当前使用 mock 数据回退，后端 API 实现后需要对接
 *
 * @module features/projects/services
 */

import { apiFetch } from '@/lib/api';
import type {
  Project,
  ProjectMember,
  ProjectStatistics,
  ProjectListParams,
  ProjectCreateInput,
  ProjectUpdateInput,
  ProjectMemberAssignInput,
  ProjectStatus,
} from '../types';

const BASE_PATH = '/api/v1/projects';

// ========== Mock 数据生成器 ==========

/**
 * 生成 mock 项目列表数据
 * SoT: C1-project-mgmt.md §4.2 响应示例
 */
function generateMockProjects(): Project[] {
  return [
    {
      id: 1,
      name: '618大促项目',
      client_name: 'XX电商',
      client_company: 'XX电商有限公司',
      description: '618大促广告投放项目',
      status: 'active' as ProjectStatus,
      budget: 1000000,
      currency: 'CNY',
      start_date: '2025-06-01',
      end_date: '2025-06-30',
      owner_id: 1,
      owner_name: '张三',
      target_cpl: 35.00,
      unit_price: 50.00,
      total_spent: 560000,
      total_accounts: 15,
      active_accounts: 12,
      created_by_name: '系统管理员',
      created_at: '2025-05-15T10:00:00Z',
      updated_at: '2025-06-15T15:30:00Z',
      remaining_budget: 440000,
      budget_usage_percent: 56,
    },
    {
      id: 2,
      name: '品牌推广项目',
      client_name: 'YY品牌',
      client_company: 'YY品牌科技公司',
      description: '品牌形象推广',
      status: 'active' as ProjectStatus,
      budget: 800000,
      currency: 'CNY',
      start_date: '2025-03-01',
      end_date: '2025-12-31',
      owner_id: 2,
      owner_name: '李四',
      target_cpl: 40.00,
      unit_price: 55.00,
      total_spent: 720000,
      total_accounts: 10,
      active_accounts: 8,
      created_by_name: '张三',
      created_at: '2025-02-20T09:00:00Z',
      updated_at: '2025-06-10T11:20:00Z',
      remaining_budget: 80000,
      budget_usage_percent: 90,
    },
    {
      id: 3,
      name: '双十一预热',
      client_name: 'ZZ商城',
      client_company: 'ZZ商城集团',
      description: '双十一预热推广',
      status: 'planning' as ProjectStatus,
      budget: 2000000,
      currency: 'CNY',
      start_date: '2025-10-01',
      end_date: '2025-11-11',
      owner_id: 1,
      owner_name: '张三',
      target_cpl: 30.00,
      unit_price: 45.00,
      total_spent: 0,
      total_accounts: 0,
      active_accounts: 0,
      created_by_name: '李四',
      created_at: '2025-06-01T14:00:00Z',
      updated_at: '2025-06-01T14:00:00Z',
      remaining_budget: 2000000,
      budget_usage_percent: 0,
    },
    {
      id: 4,
      name: '年终大促',
      client_name: 'AA零售',
      client_company: 'AA零售连锁',
      description: '年终促销活动',
      status: 'paused' as ProjectStatus,
      budget: 500000,
      currency: 'CNY',
      start_date: '2025-12-01',
      end_date: '2025-12-31',
      owner_id: 3,
      owner_name: '王五',
      target_cpl: 45.00,
      unit_price: 60.00,
      total_spent: 480000,
      total_accounts: 8,
      active_accounts: 0,
      created_by_name: '王五',
      created_at: '2025-11-01T10:00:00Z',
      updated_at: '2025-12-15T16:45:00Z',
      remaining_budget: 20000,
      budget_usage_percent: 96,
    },
  ];
}

/**
 * 生成 mock 项目统计数据
 * SoT: C1-project-mgmt.md §4.1
 */
function generateMockStatistics(): ProjectStatistics {
  const projects = generateMockProjects();
  return {
    total_projects: projects.length,
    active_projects: projects.filter(p => p.status === 'active').length,
    paused_projects: projects.filter(p => p.status === 'paused').length,
    completed_projects: projects.filter(p => p.status === 'completed').length,
    cancelled_projects: projects.filter(p => p.status === 'cancelled').length,
    total_budget: projects.reduce((sum, p) => sum + p.budget, 0),
    total_spent: projects.reduce((sum, p) => sum + p.total_spent, 0),
    total_clients: new Set(projects.map(p => p.client_name)).size,
    avg_project_value: projects.length > 0
      ? projects.reduce((sum, p) => sum + p.budget, 0) / projects.length
      : 0,
    top_performers: [
      { id: 1, name: '618大促项目', roi: 1.85 },
      { id: 3, name: '双十一预热', roi: 1.65 },
      { id: 2, name: '品牌推广项目', roi: 1.42 },
    ],
  };
}

/**
 * 生成 mock 项目成员数据
 */
function generateMockMembers(): ProjectMember[] {
  return [
    {
      id: 1,
      user_id: '1',
      user_name: '张三',
      user_email: 'zhangsan@example.com',
      user_role: 'project_owner',
      project_role: 'account_manager',
      joined_at: '2025-05-15T10:00:00Z',
    },
    {
      id: 2,
      user_id: '2',
      user_name: '投手A',
      user_email: 'pitcher_a@example.com',
      user_role: 'pitcher',
      project_role: 'media_buyer',
      joined_at: '2025-05-16T09:00:00Z',
    },
    {
      id: 3,
      user_id: '3',
      user_name: '投手B',
      user_email: 'pitcher_b@example.com',
      user_role: 'pitcher',
      project_role: 'media_buyer',
      joined_at: '2025-05-17T11:00:00Z',
    },
  ];
}

// ========== Query Functions ==========

/**
 * 获取项目列表
 * GET /api/v1/projects
 * SoT: C1-project-mgmt.md §4.1
 */
export async function getProjects(params: ProjectListParams = {}) {
  // TODO: 后端 API 实现后取消注释
  // const searchParams = new URLSearchParams();
  // if (params.page) searchParams.set('page', String(params.page));
  // if (params.page_size) searchParams.set('page_size', String(params.page_size));
  // if (params.status) searchParams.set('status', params.status);
  // if (params.manager_id) searchParams.set('manager_id', String(params.manager_id));
  // if (params.client_name) searchParams.set('client_name', params.client_name);
  // const query = searchParams.toString();
  // const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;
  // const response = await apiFetch<{
  //   items: Project[];
  //   meta: { pagination: { page: number; page_size: number; total: number; total_pages: number } };
  // }>(url);
  // return {
  //   data: response.items ?? [],
  //   meta: response.meta,
  // };

  // Mock 响应
  let items = generateMockProjects();

  // 筛选
  if (params.status) {
    items = items.filter(p => p.status === params.status);
  }
  if (params.client_name) {
    items = items.filter(p =>
      p.client_name.toLowerCase().includes(params.client_name!.toLowerCase())
    );
  }

  // 分页
  const page = params.page || 1;
  const pageSize = params.page_size || 20;
  const total = items.length;
  const startIndex = (page - 1) * pageSize;
  const paginatedItems = items.slice(startIndex, startIndex + pageSize);

  return {
    data: paginatedItems,
    meta: {
      pagination: {
        page,
        page_size: pageSize,
        total,
        total_pages: Math.ceil(total / pageSize),
      },
    },
  };
}

/**
 * 获取项目详情
 * GET /api/v1/projects/{id}
 * SoT: C1-project-mgmt.md §4.1
 */
export async function getProject(id: number): Promise<{ data: Project }> {
  // TODO: 后端 API 实现后取消注释
  // const response = await apiFetch<Project>(`${BASE_PATH}/${id}`);
  // return { data: response };

  // Mock 响应
  const projects = generateMockProjects();
  const project = projects.find(p => p.id === id);
  if (!project) {
    throw new Error(`Project ${id} not found`);
  }
  return { data: project };
}

/**
 * 获取项目统计数据
 * GET /api/v1/projects/statistics
 * SoT: C1-project-mgmt.md §4.1
 */
export async function getProjectStatistics(): Promise<{ data: ProjectStatistics }> {
  // TODO: 后端 API 实现后取消注释
  // const response = await apiFetch<ProjectStatistics>(`${BASE_PATH}/statistics`);
  // return { data: response };

  // Mock 响应
  return { data: generateMockStatistics() };
}

/**
 * 获取项目成员列表
 * GET /api/v1/projects/{id}/members
 * SoT: C1-project-mgmt.md §4.1
 */
export async function getProjectMembers(projectId: number): Promise<{ data: ProjectMember[] }> {
  // TODO: 后端 API 实现后取消注释
  // const response = await apiFetch<ProjectMember[]>(`${BASE_PATH}/${projectId}/members`);
  // return { data: response ?? [] };

  // Mock 响应
  return { data: generateMockMembers() };
}

// ========== Mutation Functions ==========

/**
 * 创建项目
 * POST /api/v1/projects
 * SoT: C1-project-mgmt.md §4.1
 */
export async function createProject(input: ProjectCreateInput): Promise<{ data: Project }> {
  // TODO: 后端 API 实现后使用真实 API
  const response = await apiFetch<Project>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
  return { data: response };
}

/**
 * 更新项目
 * PUT /api/v1/projects/{id}
 * SoT: C1-project-mgmt.md §4.1
 */
export async function updateProject(
  id: number,
  input: ProjectUpdateInput
): Promise<{ data: Project }> {
  const response = await apiFetch<Project>(`${BASE_PATH}/${id}`, {
    method: 'PUT',
    body: input,
  });
  return { data: response };
}

/**
 * 删除项目
 * DELETE /api/v1/projects/{id}
 * SoT: C1-project-mgmt.md §4.1
 */
export async function deleteProject(id: number): Promise<void> {
  await apiFetch(`${BASE_PATH}/${id}`, { method: 'DELETE' });
}

/**
 * 添加项目成员
 * POST /api/v1/projects/{id}/members
 * SoT: C1-project-mgmt.md §4.1
 */
export async function assignMember(
  projectId: number,
  input: ProjectMemberAssignInput
): Promise<{ data: ProjectMember }> {
  const response = await apiFetch<ProjectMember>(`${BASE_PATH}/${projectId}/members`, {
    method: 'POST',
    body: input,
  });
  return { data: response };
}

/**
 * 移除项目成员
 * DELETE /api/v1/projects/{id}/members/{user_id}
 * SoT: C1-project-mgmt.md §4.1
 */
export async function removeMember(projectId: number, userId: string): Promise<void> {
  await apiFetch(`${BASE_PATH}/${projectId}/members/${userId}`, { method: 'DELETE' });
}
