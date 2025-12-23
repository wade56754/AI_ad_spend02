/**
 * Daily Reports API Service
 *
 * SoT: docs/10.module-specs/B2-daily-report-review.md §5 API 接口
 * SoT: STATE_MACHINE.md v2.6 Section 8 (日报 8 状态机)
 * SoT: API_SOT.md v9.0 Section 5.4 (Daily Reports endpoints)
 *
 * 一句话定义: 管理日报的创建、审核、确认、锁定流程
 *
 * 日报 8 状态机:
 *   raw_submitted → trend_pending → trend_ok/trend_flagged
 *   → trend_resolved → final_pending → final_confirmed → final_locked
 *
 * 注意: 当前使用 mock 数据回退，后端 API 实现后需要对接
 *
 * @module features/daily-reports/services
 */

import { apiFetch, apiFetchPaginated } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';
import type {
  DailyReport,
  DailyReportListParams,
  DailyReportCreateInput,
  DailyReportUpdateInput,
  TrendResolveInput,
  FinalConfirmInput,
  DailyReportStatus,
} from '../types';

const BASE_PATH = '/api/v1/daily-reports';

// ========== Mock 数据生成器 ==========

/**
 * 生成 mock 日报列表数据
 * SoT: B2-daily-report-review.md §5.2 响应示例
 * SoT: STATE_MACHINE.md v2.6 Section 8 (8 状态)
 */
function generateMockDailyReports(): DailyReport[] {
  return [
    {
      id: 1,
      ad_account_id: 101,
      ad_account_name: '巨量-001',
      project_id: 1,
      project_name: '618大促项目',
      report_date: '2025-12-22',
      status: 'trend_flagged' as DailyReportStatus,
      raw_spend: 5000,
      follows_count: 120,
      result_count: 150,
      cost_per_follow: 41.67,
      cost_per_result: 33.33,
      region: 'Turkey',
      platform: 'FB',
      currency: 'USD',
      trend_flag: 'flagged',
      trend_flag_reason: 'CPL 超标 30%',
      submitter_name: '张三',
      team_name: 'A组',
      created_at: '2025-12-22T10:00:00Z',
      updated_at: '2025-12-22T10:00:00Z',
    },
    {
      id: 2,
      ad_account_id: 102,
      ad_account_name: '广点通-002',
      project_id: 1,
      project_name: '618大促项目',
      report_date: '2025-12-22',
      status: 'trend_ok' as DailyReportStatus,
      raw_spend: 3000,
      follows_count: 100,
      result_count: 120,
      cost_per_follow: 30.00,
      cost_per_result: 25.00,
      region: 'India',
      platform: 'Google',
      currency: 'USD',
      trend_flag: 'normal',
      submitter_name: '李四',
      team_name: 'A组',
      created_at: '2025-12-22T09:00:00Z',
      updated_at: '2025-12-22T14:00:00Z',
    },
    {
      id: 3,
      ad_account_id: 103,
      ad_account_name: '巨量-003',
      project_id: 2,
      project_name: '品牌推广项目',
      report_date: '2025-12-21',
      status: 'final_locked' as DailyReportStatus,
      raw_spend: 4500,
      follows_count: 150,
      result_count: 180,
      cost_per_follow: 30.00,
      cost_per_result: 25.00,
      final_spend: 4500,
      final_conversions: 150,
      region: 'Germany',
      platform: 'FB',
      currency: 'USD',
      submitter_name: '张三',
      team_name: 'A组',
      locked_at: '2025-12-22T10:00:00Z',
      created_at: '2025-12-21T10:00:00Z',
      updated_at: '2025-12-22T10:00:00Z',
    },
    {
      id: 4,
      ad_account_id: 101,
      ad_account_name: '巨量-001',
      project_id: 1,
      project_name: '618大促项目',
      report_date: '2025-12-22',
      status: 'trend_pending' as DailyReportStatus,
      raw_spend: 2800,
      follows_count: 85,
      result_count: 100,
      cost_per_follow: 32.94,
      cost_per_result: 28.00,
      region: 'Brazil',
      platform: 'TikTok',
      currency: 'USD',
      submitter_name: '王五',
      team_name: 'B组',
      created_at: '2025-12-22T11:00:00Z',
      updated_at: '2025-12-22T11:00:00Z',
    },
    {
      id: 5,
      ad_account_id: 104,
      ad_account_name: '广点通-004',
      project_id: 2,
      project_name: '品牌推广项目',
      report_date: '2025-12-22',
      status: 'final_pending' as DailyReportStatus,
      raw_spend: 6200,
      follows_count: 200,
      result_count: 240,
      cost_per_follow: 31.00,
      cost_per_result: 25.83,
      region: 'UK',
      platform: 'FB',
      currency: 'USD',
      trend_flag: 'resolved',
      trend_resolution_note: '已调整出价策略',
      submitter_name: '李四',
      team_name: 'A组',
      created_at: '2025-12-22T08:00:00Z',
      updated_at: '2025-12-22T16:00:00Z',
    },
    {
      id: 6,
      ad_account_id: 105,
      ad_account_name: '巨量-005',
      project_id: 1,
      project_name: '618大促项目',
      report_date: '2025-12-22',
      status: 'raw_submitted' as DailyReportStatus,
      raw_spend: 1500,
      follows_count: 50,
      result_count: 60,
      cost_per_follow: 30.00,
      cost_per_result: 25.00,
      region: 'Korea',
      platform: 'Google',
      currency: 'USD',
      submitter_name: '赵六',
      team_name: 'B组',
      created_at: '2025-12-22T12:00:00Z',
      updated_at: '2025-12-22T12:00:00Z',
    },
    {
      id: 7,
      ad_account_id: 102,
      ad_account_name: '广点通-002',
      project_id: 2,
      project_name: '品牌推广项目',
      report_date: '2025-12-22',
      status: 'final_confirmed' as DailyReportStatus,
      raw_spend: 8000,
      follows_count: 280,
      result_count: 320,
      cost_per_follow: 28.57,
      cost_per_result: 25.00,
      final_spend: 8000,
      final_conversions: 280,
      region: 'France',
      platform: 'FB',
      currency: 'USD',
      submitter_name: '张三',
      team_name: 'A组',
      created_at: '2025-12-22T07:00:00Z',
      updated_at: '2025-12-22T17:00:00Z',
    },
    {
      id: 8,
      ad_account_id: 103,
      ad_account_name: '巨量-003',
      project_id: 1,
      project_name: '618大促项目',
      report_date: '2025-12-22',
      status: 'trend_resolved' as DailyReportStatus,
      raw_spend: 3500,
      follows_count: 90,
      result_count: 110,
      cost_per_follow: 38.89,
      cost_per_result: 31.82,
      region: 'Japan',
      platform: 'TikTok',
      currency: 'USD',
      trend_flag: 'resolved',
      trend_flag_reason: 'CPL 超标',
      trend_resolution_note: '已与投手沟通，调整投放策略',
      submitter_name: '王五',
      team_name: 'B组',
      created_at: '2025-12-22T09:30:00Z',
      updated_at: '2025-12-22T15:00:00Z',
    },
  ];
}

/**
 * 生成 mock 日报统计数据
 * SoT: B2-daily-report-review.md §5.1
 */
function generateMockDailyReportStats(): Record<DailyReportStatus, number> {
  const reports = generateMockDailyReports();
  const stats: Record<DailyReportStatus, number> = {
    raw_submitted: 0,
    trend_pending: 0,
    trend_ok: 0,
    trend_flagged: 0,
    trend_resolved: 0,
    final_pending: 0,
    final_confirmed: 0,
    final_locked: 0,
  };

  reports.forEach((r) => {
    stats[r.status]++;
  });

  return stats;
}

// ========== Query Functions ==========

/**
 * 获取日报列表
 * GET /api/v1/daily-reports
 * SoT: B2-daily-report-review.md §5.1
 */
export async function getDailyReports(
  params: DailyReportListParams = {}
): Promise<PaginatedResponse<DailyReport>> {
  // TODO: 后端 API 实现后取消注释
  // const searchParams = new URLSearchParams();
  // if (params.project_id) searchParams.set('project_id', String(params.project_id));
  // if (params.ad_account_id) searchParams.set('ad_account_id', String(params.ad_account_id));
  // if (params.status) {
  //   const statuses = Array.isArray(params.status) ? params.status : [params.status];
  //   statuses.forEach((s) => searchParams.append('status', s));
  // }
  // if (params.start_date) searchParams.set('start_date', params.start_date);
  // if (params.end_date) searchParams.set('end_date', params.end_date);
  // if (params.search) searchParams.set('search', params.search);
  // if (params.page) searchParams.set('page', String(params.page));
  // if (params.page_size) searchParams.set('page_size', String(params.page_size));
  // if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  // if (params.sort_order) searchParams.set('sort_order', params.sort_order);
  // if (params.region) searchParams.set('region', params.region);
  // if (params.platform) searchParams.set('platform', params.platform);
  // if (params.team_id) searchParams.set('team_id', params.team_id);
  // if (params.submitter_name) searchParams.set('submitter_name', params.submitter_name);
  // const query = searchParams.toString();
  // const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;
  // return apiFetchPaginated<DailyReport>(url);

  // Mock 响应
  let items = generateMockDailyReports();

  // 筛选 - 项目
  if (params.project_id) {
    items = items.filter((r) => r.project_id === params.project_id);
  }

  // 筛选 - 账户
  if (params.ad_account_id) {
    items = items.filter((r) => r.ad_account_id === params.ad_account_id);
  }

  // 筛选 - 状态
  if (params.status) {
    const statuses = Array.isArray(params.status) ? params.status : [params.status];
    items = items.filter((r) => statuses.includes(r.status));
  }

  // 筛选 - 日期范围
  if (params.start_date) {
    items = items.filter((r) => r.report_date >= params.start_date!);
  }
  if (params.end_date) {
    items = items.filter((r) => r.report_date <= params.end_date!);
  }

  // 筛选 - 地区
  if (params.region) {
    items = items.filter((r) => r.region === params.region);
  }

  // 筛选 - 平台
  if (params.platform) {
    items = items.filter((r) => r.platform === params.platform);
  }

  // 筛选 - 投手
  if (params.submitter_name) {
    items = items.filter((r) =>
      r.submitter_name?.toLowerCase().includes(params.submitter_name!.toLowerCase())
    );
  }

  // 分页
  const page = params.page || 1;
  const pageSize = params.page_size || 20;
  const total = items.length;
  const startIndex = (page - 1) * pageSize;
  const paginatedItems = items.slice(startIndex, startIndex + pageSize);

  return {
    items: paginatedItems,
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
 * 获取单个日报详情
 * GET /api/v1/daily-reports/:id
 * SoT: B2-daily-report-review.md §5.1
 */
export async function getDailyReport(id: string): Promise<DailyReport> {
  // TODO: 后端 API 实现后取消注释
  // return apiFetch<DailyReport>(`${BASE_PATH}/${id}`);

  // Mock 响应
  const reports = generateMockDailyReports();
  const report = reports.find((r) => r.id === Number(id));
  if (!report) {
    throw new Error(`Daily report ${id} not found`);
  }
  return report;
}

/**
 * 按项目获取日报列表
 * GET /api/v1/projects/:projectId/daily-reports
 * SoT: B2-daily-report-review.md §5.1
 */
export async function getDailyReportsByProject(
  projectId: string | number,
  params: Omit<DailyReportListParams, 'project_id'> = {}
): Promise<PaginatedResponse<DailyReport>> {
  return getDailyReports({ ...params, project_id: Number(projectId) });
}

// ========== Mutation Functions ==========

/**
 * 创建日报
 * POST /api/v1/daily-reports
 * SoT: B2-daily-report-review.md §5.1
 */
export async function createDailyReport(
  input: DailyReportCreateInput
): Promise<DailyReport> {
  return apiFetch<DailyReport>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
}

/**
 * 更新日报 (仅 raw_submitted 状态可更新)
 * PATCH /api/v1/daily-reports/:id
 * SoT: B2-daily-report-review.md §5.1
 */
export async function updateDailyReport(
  id: string,
  input: DailyReportUpdateInput
): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}`, {
    method: 'PATCH',
    body: input,
  });
}

/**
 * 删除日报 (仅 raw_submitted 状态可删除)
 * DELETE /api/v1/daily-reports/:id
 * SoT: B2-daily-report-review.md §5.1
 */
export async function deleteDailyReport(id: string): Promise<void> {
  return apiFetch<void>(`${BASE_PATH}/${id}`, {
    method: 'DELETE',
  });
}

// ========== State Transition Functions ==========
// SoT: STATE_MACHINE.md v2.6 Section 8 (日报 8 状态机)

/**
 * 提交趋势审核
 * POST /api/v1/daily-reports/:id/submit-trend
 * raw_submitted → trend_pending
 */
export async function submitForTrend(id: string): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/submit-trend`, {
    method: 'POST',
  });
}

/**
 * 趋势通过
 * POST /api/v1/daily-reports/:id/approve-trend
 * trend_pending → trend_ok
 */
export async function approveTrend(id: string): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/approve-trend`, {
    method: 'POST',
  });
}

/**
 * 标记异常
 * POST /api/v1/daily-reports/:id/flag-trend
 * trend_pending → trend_flagged
 * SoT: B2-daily-report-review.md §3.5 趋势风控规则 (TF-001/002/003)
 */
export async function flagTrend(
  id: string,
  notes: string
): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/flag-trend`, {
    method: 'POST',
    body: { trend_notes: notes },
  });
}

/**
 * 处理异常
 * POST /api/v1/daily-reports/:id/resolve-flag
 * trend_flagged → trend_resolved
 */
export async function resolveFlag(
  id: string,
  input: TrendResolveInput
): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/resolve-flag`, {
    method: 'POST',
    body: input,
  });
}

/**
 * 提交终审
 * POST /api/v1/daily-reports/:id/submit-final
 * trend_ok | trend_resolved → final_pending
 */
export async function submitForFinal(id: string): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/submit-final`, {
    method: 'POST',
  });
}

/**
 * 终审确认
 * POST /api/v1/daily-reports/:id/confirm-final
 * final_pending → final_confirmed
 */
export async function confirmFinal(
  id: string,
  input: FinalConfirmInput
): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/confirm-final`, {
    method: 'POST',
    body: input,
  });
}

/**
 * 锁定入账
 * POST /api/v1/daily-reports/:id/lock
 * final_confirmed → final_locked
 * SoT: LEDGER_SOT.md v1.1 (账本记录规则)
 */
export async function lockReport(id: string): Promise<DailyReport> {
  return apiFetch<DailyReport>(`${BASE_PATH}/${id}/lock`, {
    method: 'POST',
  });
}

// ========== Bulk Operations ==========

/**
 * 批量提交趋势审核
 * POST /api/v1/daily-reports/bulk/submit-trend
 */
export async function bulkSubmitForTrend(ids: string[]): Promise<{
  success: string[];
  failed: { id: string; error: string }[];
}> {
  return apiFetch(`${BASE_PATH}/bulk/submit-trend`, {
    method: 'POST',
    body: { ids },
  });
}

// ========== Statistics ==========

/**
 * 获取日报状态统计
 * GET /api/v1/daily-reports/stats
 * SoT: B2-daily-report-review.md §5.1
 */
export async function getDailyReportStats(params: {
  project_id?: string;
  start_date?: string;
  end_date?: string;
} = {}): Promise<Record<DailyReportStatus, number>> {
  // TODO: 后端 API 实现后取消注释
  // const searchParams = new URLSearchParams();
  // if (params.project_id) searchParams.set('project_id', params.project_id);
  // if (params.start_date) searchParams.set('start_date', params.start_date);
  // if (params.end_date) searchParams.set('end_date', params.end_date);
  // const query = searchParams.toString();
  // const url = query ? `${BASE_PATH}/stats?${query}` : `${BASE_PATH}/stats`;
  // return apiFetch(url);

  // Mock 响应
  return generateMockDailyReportStats();
}
