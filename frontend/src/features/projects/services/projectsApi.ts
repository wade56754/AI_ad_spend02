/**
 * Projects API Service
 *
 * SoT 对齐: DATA_SCHEMA.md v5.2
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
} from '../types';

const BASE_PATH = '/api/v1/projects';

// ========== Query Functions ==========

export async function getProjects(params: ProjectListParams = {}) {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.status) searchParams.set('status', params.status);
  if (params.manager_id) searchParams.set('manager_id', String(params.manager_id));
  if (params.client_name) searchParams.set('client_name', params.client_name);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  const response = await apiFetch<{
    data: { items: Project[]; meta: { pagination: { page: number; page_size: number; total: number; total_pages: number } } };
  }>(url);

  return {
    data: response.data.items,
    meta: response.data.meta,
  };
}

export async function getProject(id: number): Promise<{ data: Project }> {
  return apiFetch<{ data: Project }>(`${BASE_PATH}/${id}`);
}

export async function getProjectStatistics(): Promise<{ data: ProjectStatistics }> {
  return apiFetch<{ data: ProjectStatistics }>(`${BASE_PATH}/statistics`);
}

export async function getProjectMembers(projectId: number): Promise<{ data: ProjectMember[] }> {
  return apiFetch<{ data: ProjectMember[] }>(`${BASE_PATH}/${projectId}/members`);
}

// ========== Mutation Functions ==========

export async function createProject(input: ProjectCreateInput): Promise<{ data: Project }> {
  return apiFetch<{ data: Project }>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
}

export async function updateProject(
  id: number,
  input: ProjectUpdateInput
): Promise<{ data: Project }> {
  return apiFetch<{ data: Project }>(`${BASE_PATH}/${id}`, {
    method: 'PUT',
    body: input,
  });
}

export async function deleteProject(id: number): Promise<void> {
  await apiFetch(`${BASE_PATH}/${id}`, { method: 'DELETE' });
}

export async function assignMember(
  projectId: number,
  input: ProjectMemberAssignInput
): Promise<{ data: ProjectMember }> {
  return apiFetch<{ data: ProjectMember }>(`${BASE_PATH}/${projectId}/members`, {
    method: 'POST',
    body: input,
  });
}

export async function removeMember(projectId: number, userId: string): Promise<void> {
  await apiFetch(`${BASE_PATH}/${projectId}/members/${userId}`, { method: 'DELETE' });
}
