/**
 * Weekly Briefs API Service
 *
 * TanStack Query v5 API 服务层
 *
 * SoT: docs/10.module-specs/B3-weekly-brief.md §4 API 接口
 * SoT: STATE_MACHINE.md v2.6 (周报状态: draft → submitted)
 * SoT: API_SOT.md v9.0 Section 5.7 (Weekly Brief endpoints)
 *
 * 一句话定义: 周报数据获取和提交服务
 *
 * 周报 2 状态机:
 *   draft → submitted (终态)
 *
 * @module features/weekly-briefs/services
 */

import { apiFetch, apiDownload } from '@/lib/api';
import type {
  WeeklyBrief,
  WeeklyBriefListParams,
  WeeklyBriefListResponse,
  WeeklyBriefStats,
  WeeklySummary,
  CreateWeeklyBriefRequest,
  UpdateWeeklyBriefRequest,
  SubmitWeeklyBriefResponse,
} from '../types';

const BASE_PATH = '/api/v1/weekly-briefs';

// ========== Query APIs ==========

/**
 * 获取周报列表
 * GET /api/v1/weekly-briefs
 * SoT: B3-weekly-brief.md §4.1 接口清单
 */
export async function getWeeklyBriefList(
  params: WeeklyBriefListParams = {}
): Promise<WeeklyBriefListResponse> {
  const searchParams = new URLSearchParams();

  if (params.week) searchParams.append('week', params.week);
  if (params.week_start) searchParams.append('week_start', params.week_start);
  if (params.project_id) searchParams.append('project_id', String(params.project_id));
  if (params.status) searchParams.append('status', params.status);
  if (params.page) searchParams.append('page', String(params.page));
  if (params.page_size) searchParams.append('page_size', String(params.page_size));

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  return apiFetch<WeeklyBriefListResponse>(url);
}

/**
 * 获取周报详情
 * GET /api/v1/weekly-briefs/{id}
 * SoT: B3-weekly-brief.md §4.1 接口清单
 */
export async function getWeeklyBriefById(id: number): Promise<WeeklyBrief> {
  return apiFetch<WeeklyBrief>(`${BASE_PATH}/${id}`);
}

/**
 * 获取周报统计
 * GET /api/v1/weekly-briefs/stats
 * SoT: B3-weekly-brief.md §4.1 接口清单
 */
export async function getWeeklyBriefStats(
  params: { week?: string; week_start?: string } = {}
): Promise<WeeklyBriefStats> {
  const searchParams = new URLSearchParams();

  if (params.week) searchParams.append('week', params.week);
  if (params.week_start) searchParams.append('week_start', params.week_start);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/stats?${query}` : `${BASE_PATH}/stats`;

  return apiFetch<WeeklyBriefStats>(url);
}

/**
 * 获取项目周数据汇总
 * GET /api/v1/projects/{id}/weekly-summary
 * SoT: B3-weekly-brief.md §4.2 项目周数据汇总
 */
export async function getProjectWeeklySummary(
  projectId: number,
  weekStart: string
): Promise<WeeklySummary> {
  const searchParams = new URLSearchParams();
  searchParams.append('week_start', weekStart);

  return apiFetch<WeeklySummary>(
    `/api/v1/projects/${projectId}/weekly-summary?${searchParams.toString()}`
  );
}

// ========== Mutation APIs ==========

/**
 * 创建周报
 * POST /api/v1/weekly-briefs
 */
export async function createWeeklyBrief(data: CreateWeeklyBriefRequest): Promise<WeeklyBrief> {
  return apiFetch<WeeklyBrief>(BASE_PATH, {
    method: 'POST',
    body: data,
  });
}

/**
 * 更新周报
 * PUT /api/v1/weekly-briefs/{id}
 */
export async function updateWeeklyBrief(
  id: number,
  data: UpdateWeeklyBriefRequest
): Promise<WeeklyBrief> {
  return apiFetch<WeeklyBrief>(`${BASE_PATH}/${id}`, {
    method: 'PUT',
    body: data,
  });
}

/**
 * 提交周报
 * POST /api/v1/weekly-briefs/{id}/submit
 */
export async function submitWeeklyBrief(id: number): Promise<SubmitWeeklyBriefResponse> {
  return apiFetch<SubmitWeeklyBriefResponse>(`${BASE_PATH}/${id}/submit`, {
    method: 'POST',
  });
}

/**
 * 导出周报
 * GET /api/v1/weekly-briefs/export
 */
export async function exportWeeklyBriefs(
  params: { week?: string; project_id?: number; format?: 'pdf' | 'excel' } = {}
): Promise<Blob> {
  const searchParams = new URLSearchParams();

  if (params.week) searchParams.append('week', params.week);
  if (params.project_id) searchParams.append('project_id', String(params.project_id));
  if (params.format) searchParams.append('format', params.format);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}/export?${query}` : `${BASE_PATH}/export`;

  return apiDownload(url);
}
