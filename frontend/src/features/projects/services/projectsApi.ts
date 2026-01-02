/**
 * Projects API Service
 *
 * SoT: docs/10.module-specs/C1-project-mgmt.md §4 API 接口
 * SoT: DATA_SCHEMA.md v5.2 (projects entity)
 * SoT: STATE_MACHINE.md v2.6 Section 5 (项目状态机)
 *
 * 使用真实后端 API 获取数据
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
  ProjectDashboard,
  ProjectDashboardParams,
  PrepaymentEntry,
  PrepaymentBalance,
  PrepaymentCreateInput,
  PrepaymentReversalInput,
  PrepaymentListParams,
} from '../types';

const BASE_PATH = '/api/v1/projects';

// ========== Query Functions ==========

/**
 * 获取项目列表
 * GET /api/v1/projects
 * SoT: C1-project-mgmt.md §4.1
 */
export async function getProjects(params: ProjectListParams = {}) {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.status) searchParams.set('status', params.status);
  if (params.manager_id) searchParams.set('manager_id', String(params.manager_id));
  if (params.client_name) searchParams.set('client_name', params.client_name);
  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  // apiFetch 自动解包 envelope，返回 data 部分
  const response = await apiFetch<{
    items: Project[];
    meta: { pagination: { page: number; page_size: number; total: number; total_pages: number } };
  }>(url);

  return {
    data: response.items ?? [],
    meta: response.meta,
  };
}

/**
 * 获取项目详情
 * GET /api/v1/projects/{id}
 * SoT: C1-project-mgmt.md §4.1
 */
export async function getProject(id: number): Promise<{ data: Project }> {
  // apiFetch 自动解包 envelope，返回 data 部分
  const response = await apiFetch<Project>(`${BASE_PATH}/${id}`);
  return { data: response };
}

/**
 * 获取项目统计数据
 * GET /api/v1/projects/statistics
 * SoT: C1-project-mgmt.md §4.1
 */
export async function getProjectStatistics(): Promise<{ data: ProjectStatistics }> {
  // apiFetch 自动解包 envelope，返回 data 部分
  const response = await apiFetch<ProjectStatistics>(`${BASE_PATH}/statistics`);
  return { data: response };
}

/**
 * 获取项目成员列表
 * GET /api/v1/projects/{id}/members
 * SoT: C1-project-mgmt.md §4.1
 */
export async function getProjectMembers(projectId: number): Promise<{ data: ProjectMember[] }> {
  // apiFetch 自动解包 envelope，返回 data 部分
  const response = await apiFetch<ProjectMember[]>(`${BASE_PATH}/${projectId}/members`);
  return { data: response ?? [] };
}

/**
 * 获取项目仪表盘数据
 * GET /api/v1/projects/{id}/dashboard
 * TASK-PRJ-004
 */
export async function getProjectDashboard(
  projectId: number,
  params: ProjectDashboardParams = {}
): Promise<{ data: ProjectDashboard }> {
  const searchParams = new URLSearchParams();
  if (params.days) searchParams.set('days', String(params.days));
  const query = searchParams.toString();
  const url = query
    ? `${BASE_PATH}/${projectId}/dashboard?${query}`
    : `${BASE_PATH}/${projectId}/dashboard`;

  const response = await apiFetch<ProjectDashboard>(url);
  return { data: response };
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

// ========== Prepayment Functions (TASK-PRJ-005) ==========

/**
 * 获取项目预付款余额
 * GET /api/v1/projects/{id}/prepayments/balance
 * TASK-PRJ-005: 三本账体系 - 预付款账本
 */
export async function getPrepaymentBalance(
  projectId: number
): Promise<{ data: PrepaymentBalance }> {
  const response = await apiFetch<PrepaymentBalance>(
    `${BASE_PATH}/${projectId}/prepayments/balance`
  );
  return { data: response };
}

/**
 * 获取项目预付款流水列表
 * GET /api/v1/projects/{id}/prepayments
 * TASK-PRJ-005
 */
export async function getPrepaymentEntries(
  projectId: number,
  params: PrepaymentListParams = {}
): Promise<{
  data: PrepaymentEntry[];
  meta: { pagination: { page: number; page_size: number; total: number; total_pages: number } };
}> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.entry_type) searchParams.set('entry_type', params.entry_type);
  const query = searchParams.toString();
  const url = query
    ? `${BASE_PATH}/${projectId}/prepayments?${query}`
    : `${BASE_PATH}/${projectId}/prepayments`;

  const response = await apiFetch<{
    items: PrepaymentEntry[];
    meta: { pagination: { page: number; page_size: number; total: number; total_pages: number } };
  }>(url);

  return {
    data: response.items ?? [],
    meta: response.meta,
  };
}

/**
 * 添加预付款入账
 * POST /api/v1/projects/{id}/prepayments
 * TASK-PRJ-005: 记录客户预付款
 */
export async function createPrepayment(
  projectId: number,
  input: PrepaymentCreateInput
): Promise<{ data: PrepaymentEntry }> {
  const response = await apiFetch<PrepaymentEntry>(`${BASE_PATH}/${projectId}/prepayments`, {
    method: 'POST',
    body: input,
  });
  return { data: response };
}

/**
 * 添加预付款红冲
 * POST /api/v1/projects/{id}/prepayments/reversal
 * TASK-PRJ-005: 红冲错误入账
 */
export async function createPrepaymentReversal(
  projectId: number,
  input: PrepaymentReversalInput
): Promise<{ data: PrepaymentEntry }> {
  const response = await apiFetch<PrepaymentEntry>(
    `${BASE_PATH}/${projectId}/prepayments/reversal`,
    {
      method: 'POST',
      body: input,
    }
  );
  return { data: response };
}
