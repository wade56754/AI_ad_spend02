/**
 * Fund Overview API Service
 *
 * SoT: docs/10.module-specs/A2-fund-overview.md §5 API 接口
 * SoT: MASTER.md v4.4 §4.5.5 资金口径定义
 * SoT: MASTER.md v4.4 §6.5 页面 2 资金总览字段集
 *
 * 注意: 当前使用 mock 数据，后端 API 实现后需要对接
 *
 * @module features/fund-overview/services
 */

import { apiFetch } from '@/lib/api';
import type {
  FundOverview,
  FundOverviewResponse,
  FundOverviewParams,
  FundByProjectResponse,
  FundByChannelResponse,
  FundDistributionParams,
  ReceivablesResponse,
  PaymentsResponse,
  FundByProjectItem,
  FundByChannelItem,
  ReceivableItem,
  PaymentItem,
} from '../types';

const BASE_PATH = '/api/v1/fund';

// ========== Mock 数据生成器 ==========

/**
 * 生成 mock 资金概览数据
 * SoT: A2-fund-overview.md §5.2 响应示例
 */
function generateMockOverview(): FundOverview {
  return {
    total_topup: 8560000.00,
    total_spend: 7200000.00,
    current_balance: 1360000.00,
    total_receivable: 2800000.00,
    total_received: 2000000.00,
    fund_occupied: 5760000.00,
    topup_change: 15.2,
    spend_change: 12.8,
    balance_change: 18.8,
    occupy_rate: 67.3,
    pending_receivable_count: 3,
  };
}

/**
 * 生成 mock 按项目分布数据
 */
function generateMockByProject(): FundByProjectItem[] {
  return [
    {
      project_id: 1,
      project_name: '618大促项目',
      owner_id: 1,
      owner_name: '张三',
      total_topup: 2000000.00,
      total_spend: 1800000.00,
      balance: 200000.00,
      receivable: 500000.00,
      received: 300000.00,
    },
    {
      project_id: 2,
      project_name: '品牌推广项目',
      owner_id: 2,
      owner_name: '李四',
      total_topup: 1500000.00,
      total_spend: 1400000.00,
      balance: 100000.00,
      receivable: 300000.00,
      received: 200000.00,
    },
    {
      project_id: 3,
      project_name: '双十一预热',
      owner_id: 1,
      owner_name: '张三',
      total_topup: 3000000.00,
      total_spend: 2500000.00,
      balance: 500000.00,
      receivable: 800000.00,
      received: 600000.00,
    },
    {
      project_id: 4,
      project_name: '年终大促',
      owner_id: 3,
      owner_name: '王五',
      total_topup: 2060000.00,
      total_spend: 1500000.00,
      balance: 560000.00,
      receivable: 1200000.00,
      received: 900000.00,
    },
  ];
}

/**
 * 生成 mock 按渠道分布数据
 */
function generateMockByChannel(): FundByChannelItem[] {
  return [
    {
      channel_id: 1,
      channel_name: '巨量引擎',
      total_accounts: 15,
      total_topup: 4000000.00,
      total_spend: 3500000.00,
      balance: 500000.00,
    },
    {
      channel_id: 2,
      channel_name: '腾讯广告',
      total_accounts: 10,
      total_topup: 2500000.00,
      total_spend: 2200000.00,
      balance: 300000.00,
    },
    {
      channel_id: 3,
      channel_name: '百度营销',
      total_accounts: 8,
      total_topup: 2060000.00,
      total_spend: 1500000.00,
      balance: 560000.00,
    },
  ];
}

/**
 * 生成 mock 应收款数据
 */
function generateMockReceivables(): ReceivableItem[] {
  return [
    { id: 1, project_id: 1, project_name: '618大促项目', amount: 500000, days_pending: 30, status: 'pending', created_at: '2025-11-23' },
    { id: 2, project_id: 2, project_name: '品牌推广项目', amount: 800000, days_pending: 15, status: 'pending', created_at: '2025-12-08' },
    { id: 3, project_id: 3, project_name: '双十一预热', amount: 1000000, days_pending: 7, status: 'partial', created_at: '2025-12-16' },
  ];
}

/**
 * 生成 mock 回款记录
 */
function generateMockPayments(): PaymentItem[] {
  return [
    { id: 1, project_id: 2, project_name: '品牌推广项目', amount: 300000, received_at: '2025-12-20', status: 'received' },
    { id: 2, project_id: 1, project_name: '618大促项目', amount: 200000, received_at: '2025-12-18', status: 'received' },
    { id: 3, project_id: 3, project_name: '双十一预热', amount: 500000, received_at: '2025-12-15', status: 'received' },
  ];
}

// ========== Query Functions ==========

/**
 * 获取资金概览
 * GET /api/v1/fund/overview
 * SoT: A2-fund-overview.md §5.2
 *
 * @param params - 查询参数（可选日期范围）
 * @returns 资金概览数据
 */
export async function getFundOverview(
  params: FundOverviewParams = {}
): Promise<FundOverview> {
  // TODO: 后端 API 实现后取消注释
  // const searchParams = new URLSearchParams();
  // if (params.date_from) searchParams.set('date_from', params.date_from);
  // if (params.date_to) searchParams.set('date_to', params.date_to);
  // const query = searchParams.toString();
  // const url = query ? `${BASE_PATH}/overview?${query}` : `${BASE_PATH}/overview`;
  // const response = await apiFetch<FundOverviewResponse>(url);
  // return response.data;

  // Mock 响应
  return generateMockOverview();
}

/**
 * 获取资金分布（按项目）
 * GET /api/v1/fund/distribution/projects
 * SoT: A2-fund-overview.md §5.2
 *
 * @param params - 分页和排序参数
 * @returns 按项目的资金分布列表
 */
export async function getFundByProject(
  params: FundDistributionParams = {}
): Promise<FundByProjectResponse> {
  // TODO: 后端 API 实现后取消注释
  // const searchParams = new URLSearchParams();
  // if (params.page) searchParams.set('page', String(params.page));
  // if (params.page_size) searchParams.set('page_size', String(params.page_size));
  // if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  // if (params.order) searchParams.set('order', params.order);
  // const query = searchParams.toString();
  // const url = query
  //   ? `${BASE_PATH}/distribution/projects?${query}`
  //   : `${BASE_PATH}/distribution/projects`;
  // return apiFetch<FundByProjectResponse>(url);

  // Mock 响应
  const items = generateMockByProject();
  return {
    success: true,
    data: {
      items,
      pagination: {
        page: params.page || 1,
        page_size: params.page_size || 20,
        total: items.length,
      },
    },
  };
}

/**
 * 获取资金分布（按渠道）
 * GET /api/v1/fund/distribution/channels
 * SoT: A2-fund-overview.md §5.2
 *
 * @param params - 分页和排序参数
 * @returns 按渠道的资金分布列表
 */
export async function getFundByChannel(
  params: FundDistributionParams = {}
): Promise<FundByChannelResponse> {
  // TODO: 后端 API 实现后取消注释
  // const searchParams = new URLSearchParams();
  // if (params.page) searchParams.set('page', String(params.page));
  // if (params.page_size) searchParams.set('page_size', String(params.page_size));
  // if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  // if (params.order) searchParams.set('order', params.order);
  // const query = searchParams.toString();
  // const url = query
  //   ? `${BASE_PATH}/distribution/channels?${query}`
  //   : `${BASE_PATH}/distribution/channels`;
  // return apiFetch<FundByChannelResponse>(url);

  // Mock 响应
  const items = generateMockByChannel();
  return {
    success: true,
    data: {
      items,
      pagination: {
        page: params.page || 1,
        page_size: params.page_size || 20,
        total: items.length,
      },
    },
  };
}

/**
 * 获取应收款列表
 * GET /api/v1/fund/receivables
 * SoT: A2-fund-overview.md §5.1
 *
 * @returns 应收款明细列表
 */
export async function getReceivables(): Promise<ReceivablesResponse> {
  // TODO: 后端 API 实现后取消注释
  // return apiFetch<ReceivablesResponse>(`${BASE_PATH}/receivables`);

  // Mock 响应
  const items = generateMockReceivables();
  return {
    success: true,
    data: {
      items,
      total_amount: items.reduce((sum, i) => sum + i.amount, 0),
      pending_count: items.filter(i => i.status === 'pending').length,
    },
  };
}

/**
 * 获取回款记录
 * GET /api/v1/fund/payments
 * SoT: A2-fund-overview.md §5.1
 *
 * @returns 回款记录列表
 */
export async function getPayments(): Promise<PaymentsResponse> {
  // TODO: 后端 API 实现后取消注释
  // return apiFetch<PaymentsResponse>(`${BASE_PATH}/payments`);

  // Mock 响应
  const items = generateMockPayments();
  return {
    success: true,
    data: {
      items,
      total_amount: items.reduce((sum, i) => sum + i.amount, 0),
    },
  };
}
