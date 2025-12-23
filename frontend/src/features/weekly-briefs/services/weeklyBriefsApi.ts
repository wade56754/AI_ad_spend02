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

import { apiFetch } from '@/lib/api';
import type {
  WeeklyBrief,
  WeeklyBriefListParams,
  WeeklyBriefListResponse,
  WeeklyBriefStats,
  WeeklyBriefStatus,
  WeeklySummary,
  CreateWeeklyBriefRequest,
  UpdateWeeklyBriefRequest,
  SubmitWeeklyBriefResponse,
} from '../types';

const BASE_PATH = '/api/v1/weekly-briefs';

// ========== Mock 数据生成 ==========
// SoT: B3-weekly-brief.md §2.2 数据模型

/**
 * 生成 Mock 周报数据
 * 覆盖周报 2 状态 (draft, submitted)
 */
function generateMockWeeklyBriefs(): WeeklyBrief[] {
  const now = new Date();
  const weekStart = new Date(now);
  weekStart.setDate(now.getDate() - now.getDay() + 1); // 本周一
  const weekStartStr = weekStart.toISOString().split('T')[0];
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);
  const weekEndStr = weekEnd.toISOString().split('T')[0];

  return [
    {
      id: 1,
      project_id: 101,
      project_name: '618大促项目',
      week_start: weekStartStr,
      week_end: weekEndStr,
      week_label: `${now.getFullYear()}年第${getWeekNumber(weekStart)}周`,
      submitter_id: 'uuid-user-001',
      submitter_name: '张三',
      status: 'submitted' as WeeklyBriefStatus,
      weekly_spend: 156000,
      weekly_conversions: 4200,
      weekly_cpl: 37.14,
      cpl_trend: -3.8,
      achievements: '1. 完成抖音渠道新账户测试，CPL达标\n2. 优化落地页，转化率提升5%',
      issues: '1. 快手渠道审核变严，过审率下降\n2. 周末流量波动较大',
      solutions: '1. 调整素材风格，预计下周过审率恢复\n2. 周末降低预算，避免无效消耗',
      next_week_plan: '1. 测试视频号渠道\n2. 提升日均消耗到25,000\n3. CPL目标控制在35以内',
      submitted_at: new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      created_at: new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: 2,
      project_id: 102,
      project_name: '双11预热项目',
      week_start: weekStartStr,
      week_end: weekEndStr,
      week_label: `${now.getFullYear()}年第${getWeekNumber(weekStart)}周`,
      submitter_id: 'uuid-user-002',
      submitter_name: '李四',
      status: 'draft' as WeeklyBriefStatus,
      weekly_spend: 120000,
      weekly_conversions: 3500,
      weekly_cpl: 34.29,
      cpl_trend: 2.5,
      achievements: null,
      issues: null,
      solutions: null,
      next_week_plan: null,
      submitted_at: null,
      created_at: new Date(now.getTime() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(now.getTime() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: 3,
      project_id: 103,
      project_name: '品牌推广项目',
      week_start: weekStartStr,
      week_end: weekEndStr,
      week_label: `${now.getFullYear()}年第${getWeekNumber(weekStart)}周`,
      submitter_id: 'uuid-user-003',
      submitter_name: '王五',
      status: 'submitted' as WeeklyBriefStatus,
      weekly_spend: 98000,
      weekly_conversions: 2800,
      weekly_cpl: 35.00,
      cpl_trend: -5.2,
      achievements: '1. 新渠道测试成功\n2. 素材库扩充20%',
      issues: '1. 竞品加大投放力度，流量成本上升',
      solutions: '1. 错峰投放，降低竞争压力',
      next_week_plan: '1. 继续优化素材\n2. 拓展新账户',
      submitted_at: new Date(now.getTime() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      created_at: new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(now.getTime() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: 4,
      project_id: 104,
      project_name: '春节营销项目',
      week_start: weekStartStr,
      week_end: weekEndStr,
      week_label: `${now.getFullYear()}年第${getWeekNumber(weekStart)}周`,
      submitter_id: 'uuid-user-004',
      submitter_name: '赵六',
      status: 'draft' as WeeklyBriefStatus,
      weekly_spend: 85000,
      weekly_conversions: 2100,
      weekly_cpl: 40.48,
      cpl_trend: 8.3,
      achievements: null,
      issues: null,
      solutions: null,
      next_week_plan: null,
      submitted_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];
}

/**
 * 获取周次编号
 */
function getWeekNumber(date: Date): number {
  const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
  const pastDaysOfYear = (date.getTime() - firstDayOfYear.getTime()) / 86400000;
  return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
}

/**
 * 生成 Mock 统计数据
 */
function generateMockStats(): WeeklyBriefStats {
  return {
    total_projects: 4,
    submitted_count: 2,
    draft_count: 2,
    submission_rate: 50.0,
    total_weekly_spend: 459000,
  };
}

/**
 * 生成 Mock 周数据汇总
 */
function generateMockWeeklySummary(projectId: number): WeeklySummary {
  const now = new Date();
  const weekStart = new Date(now);
  weekStart.setDate(now.getDate() - now.getDay() + 1);
  const weekStartStr = weekStart.toISOString().split('T')[0];
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);
  const weekEndStr = weekEnd.toISOString().split('T')[0];

  return {
    project_id: projectId,
    project_name: `项目${projectId}`,
    week_start: weekStartStr,
    week_end: weekEndStr,
    weekly_spend: 156000,
    weekly_conversions: 4200,
    weekly_cpl: 37.14,
    target_cpl: 40.00,
    cpl_vs_target: -7.2,
    last_week: {
      spend: 144000,
      conversions: 3750,
      cpl: 38.40,
    },
    trends: {
      spend_change: 8.3,
      conversions_change: 12.0,
      cpl_change: -3.3,
    },
    daily_breakdown: [
      { date: weekStartStr, spend: 22000, conversions: 600 },
      { date: new Date(weekStart.getTime() + 86400000).toISOString().split('T')[0], spend: 23500, conversions: 620 },
    ],
  };
}

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

  try {
    return await apiFetch<WeeklyBriefListResponse>(url);
  } catch (error) {
    console.warn('[WeeklyBriefs] API 不可用，使用 Mock 数据', error);
    const mockItems = generateMockWeeklyBriefs();
    // 应用筛选
    let filteredItems = mockItems;
    if (params.project_id) {
      filteredItems = filteredItems.filter(item => item.project_id === params.project_id);
    }
    if (params.status) {
      filteredItems = filteredItems.filter(item => item.status === params.status);
    }
    return {
      items: filteredItems,
      total: filteredItems.length,
      page: params.page || 1,
      page_size: params.page_size || 20,
      stats: generateMockStats(),
    };
  }
}

/**
 * 获取周报详情
 * GET /api/v1/weekly-briefs/{id}
 * SoT: B3-weekly-brief.md §4.1 接口清单
 */
export async function getWeeklyBriefById(id: number): Promise<WeeklyBrief> {
  try {
    return await apiFetch<WeeklyBrief>(`${BASE_PATH}/${id}`);
  } catch (error) {
    console.warn('[WeeklyBriefs] API 不可用，使用 Mock 数据', error);
    const mockItems = generateMockWeeklyBriefs();
    const found = mockItems.find(item => item.id === id);
    if (found) return found;
    throw new Error(`周报 ${id} 不存在`);
  }
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

  try {
    return await apiFetch<WeeklyBriefStats>(url);
  } catch (error) {
    console.warn('[WeeklyBriefs] Stats API 不可用，使用 Mock 数据', error);
    return generateMockStats();
  }
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

  try {
    return await apiFetch<WeeklySummary>(`/api/v1/projects/${projectId}/weekly-summary?${searchParams.toString()}`);
  } catch (error) {
    console.warn('[WeeklyBriefs] Summary API 不可用，使用 Mock 数据', error);
    return generateMockWeeklySummary(projectId);
  }
}

// ========== Mutation APIs ==========

/**
 * 创建周报
 * POST /api/v1/weekly-briefs
 */
export async function createWeeklyBrief(
  data: CreateWeeklyBriefRequest
): Promise<WeeklyBrief> {
  return apiFetch<WeeklyBrief>(BASE_PATH, {
    method: 'POST',
    body: JSON.stringify(data),
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
    body: JSON.stringify(data),
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

  const response = await fetch(url, {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('导出周报失败');
  }

  return response.blob();
}
