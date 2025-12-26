/**
 * Topups API Service
 *
 * SoT: docs/10.module-specs/B1-topup-approval.md §5 API 接口
 * SoT: API_SOT.md v9.0 Section 5.6 (Topup endpoints)
 * SoT: STATE_MACHINE.md v2.6 Section 3 (充值 7 状态机)
 *
 * 一句话定义: 管理充值申请的创建、审批、支付、完成流程
 *
 * 注意: 当前使用 mock 数据回退，后端 API 实现后需要对接
 *
 * @module features/topups/services
 */

import { apiFetch, apiFetchPaginated } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';
import type {
  TopupRequest,
  TopupListParams,
  TopupCreateInput,
  TopupApproveInput,
  TopupRejectInput,
  TopupStatus,
} from '../types';

const BASE_PATH = '/api/v1/topups';

// ========== Mock 数据生成器 ==========

/**
 * Mock 充值申请数据类型 (临时，等待后端 API 实现后移除)
 * 注意: 字段结构与 TopupRequest 接口有差异，使用类型断言
 */
interface MockTopupRequest {
  id: string;
  project_id: string;
  project_name: string;
  ad_account_id: string;
  ad_account_name: string;
  channel: string;
  amount: number;
  currency: string;
  status: TopupStatus;
  requester_id: string;
  requester_name: string;
  reviewer_id: string | null;
  reviewer_name: string | null;
  approver_id: string | null;
  approver_name: string | null;
  reason: string;
  reject_reason: string | null;
  created_at: string;
  updated_at: string;
  reviewed_at: string | null;
  approved_at: string | null;
  paid_at: string | null;
  completed_at: string | null;
}

/**
 * 生成 mock 充值申请列表数据
 * SoT: B1-topup-approval.md §5.2 响应示例
 * SoT: STATE_MACHINE.md v2.6 Section 3 (7 状态)
 *
 * TODO: 后端 API 实现后删除此 mock 数据
 */
function generateMockTopups(): TopupRequest[] {
  const mockData: MockTopupRequest[] = [
    {
      id: '1',
      project_id: '1',
      project_name: '618大促项目',
      ad_account_id: 'acc-001',
      ad_account_name: '巨量-001',
      channel: 'ocean_engine',
      amount: 50000,
      currency: 'CNY',
      status: 'pending_review' as TopupStatus,
      requester_id: '2',
      requester_name: '投手A',
      reviewer_id: null,
      reviewer_name: null,
      approver_id: null,
      approver_name: null,
      reason: '618大促活动需要追加预算',
      reject_reason: null,
      created_at: '2025-06-15T10:00:00Z',
      updated_at: '2025-06-15T10:00:00Z',
      reviewed_at: null,
      approved_at: null,
      paid_at: null,
      completed_at: null,
    },
    {
      id: '2',
      project_id: '1',
      project_name: '618大促项目',
      ad_account_id: 'acc-002',
      ad_account_name: '广点通-002',
      channel: 'guangdiantong',
      amount: 30000,
      currency: 'CNY',
      status: 'finance_approve' as TopupStatus,
      requester_id: '3',
      requester_name: '投手B',
      reviewer_id: '5',
      reviewer_name: '主管张',
      approver_id: null,
      approver_name: null,
      reason: '账户余额不足，需要充值',
      reject_reason: null,
      created_at: '2025-06-14T09:00:00Z',
      updated_at: '2025-06-14T14:00:00Z',
      reviewed_at: '2025-06-14T14:00:00Z',
      approved_at: null,
      paid_at: null,
      completed_at: null,
    },
    {
      id: '3',
      project_id: '2',
      project_name: '品牌推广项目',
      ad_account_id: 'acc-003',
      ad_account_name: '巨量-003',
      channel: 'ocean_engine',
      amount: 80000,
      currency: 'CNY',
      status: 'paid' as TopupStatus,
      requester_id: '2',
      requester_name: '投手A',
      reviewer_id: '5',
      reviewer_name: '主管张',
      approver_id: '6',
      approver_name: '财务李',
      reason: '品牌推广需要大额充值',
      reject_reason: null,
      created_at: '2025-06-13T08:00:00Z',
      updated_at: '2025-06-14T16:00:00Z',
      reviewed_at: '2025-06-13T11:00:00Z',
      approved_at: '2025-06-14T10:00:00Z',
      paid_at: '2025-06-14T16:00:00Z',
      completed_at: null,
    },
    {
      id: '4',
      project_id: '1',
      project_name: '618大促项目',
      ad_account_id: 'acc-001',
      ad_account_name: '巨量-001',
      channel: 'ocean_engine',
      amount: 20000,
      currency: 'CNY',
      status: 'completed' as TopupStatus,
      requester_id: '3',
      requester_name: '投手B',
      reviewer_id: '5',
      reviewer_name: '主管张',
      approver_id: '6',
      approver_name: '财务李',
      reason: '日常充值',
      reject_reason: null,
      created_at: '2025-06-10T08:00:00Z',
      updated_at: '2025-06-11T10:00:00Z',
      reviewed_at: '2025-06-10T14:00:00Z',
      approved_at: '2025-06-10T16:00:00Z',
      paid_at: '2025-06-11T09:00:00Z',
      completed_at: '2025-06-11T10:00:00Z',
    },
    {
      id: '5',
      project_id: '2',
      project_name: '品牌推广项目',
      ad_account_id: 'acc-004',
      ad_account_name: '广点通-004',
      channel: 'guangdiantong',
      amount: 15000,
      currency: 'CNY',
      status: 'rejected' as TopupStatus,
      requester_id: '2',
      requester_name: '投手A',
      reviewer_id: '5',
      reviewer_name: '主管张',
      approver_id: null,
      approver_name: null,
      reason: '测试充值',
      reject_reason: '预算已超限，请等待下月预算',
      created_at: '2025-06-12T08:00:00Z',
      updated_at: '2025-06-12T15:00:00Z',
      reviewed_at: '2025-06-12T15:00:00Z',
      approved_at: null,
      paid_at: null,
      completed_at: null,
    },
    {
      id: '6',
      project_id: '1',
      project_name: '618大促项目',
      ad_account_id: 'acc-002',
      ad_account_name: '广点通-002',
      channel: 'guangdiantong',
      amount: 10000,
      currency: 'CNY',
      status: 'draft' as TopupStatus,
      requester_id: '3',
      requester_name: '投手B',
      reviewer_id: null,
      reviewer_name: null,
      approver_id: null,
      approver_name: null,
      reason: '草稿 - 待提交',
      reject_reason: null,
      created_at: '2025-06-16T08:00:00Z',
      updated_at: '2025-06-16T08:00:00Z',
      reviewed_at: null,
      approved_at: null,
      paid_at: null,
      completed_at: null,
    },
  ];

  // 类型断言: mock 数据结构与正式 TopupRequest 有差异
  // TODO: 后端 API 实现后删除整个 mock 数据生成器
  return mockData as unknown as TopupRequest[];
}

/**
 * 生成 mock 充值统计数据
 * SoT: B1-topup-approval.md §5.1
 */
function generateMockTopupStats(): {
  by_status: Record<TopupStatus, number>;
  total_amount: number;
  pending_count: number;
} {
  const topups = generateMockTopups();
  const byStatus: Record<TopupStatus, number> = {
    draft: 0,
    pending_review: 0,
    finance_approve: 0,
    paid: 0,
    completed: 0,
    rejected: 0,
    cancelled: 0,
  };

  topups.forEach((t) => {
    byStatus[t.status]++;
  });

  return {
    by_status: byStatus,
    // Mock 数据中 amount 实际是 number，但类型断言后变成 Money
    // TODO: 后端 API 实现后修复此计算
    total_amount: topups.reduce((sum, t) => {
      const amt = typeof t.amount === 'number' ? t.amount : (t.amount as { amount: number }).amount;
      return sum + amt;
    }, 0),
    pending_count: byStatus.pending_review + byStatus.finance_approve,
  };
}

// ========== Query Functions ==========

/**
 * 获取充值申请列表
 * GET /api/v1/topups
 * SoT: B1-topup-approval.md §5.1
 */
export async function getTopups(
  params: TopupListParams = {}
): Promise<PaginatedResponse<TopupRequest>> {
  // TODO: 后端 API 实现后取消注释
  // const searchParams = new URLSearchParams();
  // if (params.tenant_id) searchParams.set('tenant_id', params.tenant_id);
  // if (params.project_id) searchParams.set('project_id', params.project_id);
  // if (params.status) {
  //   const statuses = Array.isArray(params.status) ? params.status : [params.status];
  //   statuses.forEach((s) => searchParams.append('status', s));
  // }
  // if (params.start_date) searchParams.set('start_date', params.start_date);
  // if (params.end_date) searchParams.set('end_date', params.end_date);
  // if (params.min_amount) searchParams.set('min_amount', String(params.min_amount));
  // if (params.max_amount) searchParams.set('max_amount', String(params.max_amount));
  // if (params.page) searchParams.set('page', String(params.page));
  // if (params.page_size) searchParams.set('page_size', String(params.page_size));
  // if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  // if (params.sort_order) searchParams.set('sort_order', params.sort_order);
  // const query = searchParams.toString();
  // const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;
  // return apiFetchPaginated<TopupRequest>(url);

  // Mock 响应
  let items = generateMockTopups();

  // 筛选 - 项目
  if (params.project_id) {
    items = items.filter((t) => t.project_id === params.project_id);
  }

  // 筛选 - 状态
  if (params.status) {
    const statuses = Array.isArray(params.status) ? params.status : [params.status];
    items = items.filter((t) => statuses.includes(t.status));
  }

  // 筛选 - 金额范围
  // Mock 数据中 amount 实际是 number，需要兼容处理
  const getAmount = (t: TopupRequest): number => {
    return typeof t.amount === 'number' ? t.amount : (t.amount as { amount: number }).amount;
  };
  if (params.min_amount) {
    items = items.filter((t) => getAmount(t) >= params.min_amount!);
  }
  if (params.max_amount) {
    items = items.filter((t) => getAmount(t) <= params.max_amount!);
  }

  // 分页
  const page = params.page || 1;
  const pageSize = params.page_size || 20;
  const total = items.length;
  const startIndex = (page - 1) * pageSize;
  const paginatedItems = items.slice(startIndex, startIndex + pageSize);
  const totalPages = Math.ceil(total / pageSize);

  return {
    // New format
    items: paginatedItems,
    total,
    page,
    page_size: pageSize,
    total_pages: totalPages,
    // Legacy format
    data: paginatedItems,
    meta: {
      total,
      page,
      page_size: pageSize,
      total_pages: totalPages,
    },
  };
}

/**
 * 获取单个充值申请详情
 * GET /api/v1/topups/:id
 * SoT: B1-topup-approval.md §5.1
 */
export async function getTopup(id: string): Promise<TopupRequest> {
  // TODO: 后端 API 实现后取消注释
  // return apiFetch<TopupRequest>(`${BASE_PATH}/${id}`);

  // Mock 响应
  const topups = generateMockTopups();
  const topup = topups.find((t) => t.id === id);
  if (!topup) {
    throw new Error(`Topup ${id} not found`);
  }
  return topup;
}

/**
 * 按项目获取充值申请列表
 * GET /api/v1/projects/:projectId/topups
 * SoT: B1-topup-approval.md §5.1
 */
export async function getTopupsByProject(
  projectId: string,
  params: Omit<TopupListParams, 'project_id'> = {}
): Promise<PaginatedResponse<TopupRequest>> {
  return getTopups({ ...params, project_id: projectId });
}

// ========== Mutation Functions ==========

/**
 * 创建充值申请
 * POST /api/v1/topups
 * SoT: B1-topup-approval.md §5.1
 */
export async function createTopup(
  input: TopupCreateInput
): Promise<TopupRequest> {
  // 实际 API 调用 - 创建操作需要真实后端
  return apiFetch<TopupRequest>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
}

/**
 * 数据复核通过
 * POST /api/v1/topups/:id/review
 * pending_review → finance_approve
 * SoT: STATE_MACHINE.md v2.6 Section 3 (充值状态机)
 */
export async function reviewTopup(
  id: string,
  input?: TopupApproveInput
): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/review`, {
    method: 'POST',
    body: input ?? {},
  });
}

/**
 * 财务终审通过
 * POST /api/v1/topups/:id/approve
 * finance_approve → paid
 * SoT: STATE_MACHINE.md v2.6 Section 3 (充值状态机)
 */
export async function approveTopup(
  id: string,
  input?: TopupApproveInput
): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/approve`, {
    method: 'POST',
    body: input ?? {},
  });
}

/**
 * 拒绝充值申请
 * POST /api/v1/topups/:id/reject
 * pending_review | finance_approve → rejected
 * SoT: STATE_MACHINE.md v2.6 Section 3 (充值状态机)
 */
export async function rejectTopup(
  id: string,
  input: TopupRejectInput
): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/reject`, {
    method: 'POST',
    body: input,
  });
}

/**
 * 确认到账完成
 * POST /api/v1/topups/:id/complete
 * paid → completed (创建 ledger_entry)
 * SoT: STATE_MACHINE.md v2.6 Section 3 (充值状态机)
 * SoT: LEDGER_SOT.md v1.1 (账本记录规则)
 */
export async function completeTopup(id: string): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/complete`, {
    method: 'POST',
  });
}

/**
 * 取消充值申请
 * POST /api/v1/topups/:id/cancel
 * draft | pending_review | finance_approve → cancelled
 * SoT: STATE_MACHINE.md v2.6 Section 3 (充值状态机)
 */
export async function cancelTopup(id: string): Promise<TopupRequest> {
  return apiFetch<TopupRequest>(`${BASE_PATH}/${id}/cancel`, {
    method: 'POST',
  });
}

// ========== Statistics ==========

/**
 * 获取充值统计数据
 * GET /api/v1/topups/stats
 * SoT: B1-topup-approval.md §5.1
 */
export async function getTopupStats(params: {
  project_id?: string;
  start_date?: string;
  end_date?: string;
} = {}): Promise<{
  by_status: Record<TopupStatus, number>;
  total_amount: number;
  pending_count: number;
}> {
  // TODO: 后端 API 实现后取消注释
  // const searchParams = new URLSearchParams();
  // if (params.project_id) searchParams.set('project_id', params.project_id);
  // if (params.start_date) searchParams.set('start_date', params.start_date);
  // if (params.end_date) searchParams.set('end_date', params.end_date);
  // const query = searchParams.toString();
  // const url = query ? `${BASE_PATH}/stats?${query}` : `${BASE_PATH}/stats`;
  // return apiFetch(url);

  // Mock 响应
  return generateMockTopupStats();
}
