/**
 * Transfers API Service
 *
 * SoT 对齐: API_SOT.md v9.0
 */

import { apiFetch, apiFetchPaginated } from '@/lib/api';
import type {
  Transfer,
  TransferCreateInput,
  TransferApproveInput,
  TransferRejectInput,
  TransferListParams,
} from '../types';

const BASE_URL = '/api/transfers';

/** 获取迁移申请列表 */
export async function getTransfers(params?: TransferListParams) {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.page_size) searchParams.set('page_size', String(params.page_size));
  if (params?.status) searchParams.set('status', params.status);

  const query = searchParams.toString();
  return apiFetchPaginated<Transfer>(`${BASE_URL}${query ? `?${query}` : ''}`);
}

/** 获取迁移申请详情 */
export async function getTransfer(id: number) {
  return apiFetch<Transfer>(`${BASE_URL}/${id}`);
}

/** 创建迁移申请 */
export async function createTransfer(input: TransferCreateInput) {
  return apiFetch<Transfer>(BASE_URL, {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

/** 提交迁移申请 (draft → pending_approval) */
export async function submitTransfer(id: number) {
  return apiFetch<Transfer>(`${BASE_URL}/${id}/submit`, {
    method: 'POST',
  });
}

/** 审批迁移申请 (pending_approval → approved) */
export async function approveTransfer(id: number, input: TransferApproveInput) {
  return apiFetch<Transfer>(`${BASE_URL}/${id}/approve`, {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

/** 拒绝迁移申请 (→ rejected) */
export async function rejectTransfer(id: number, input: TransferRejectInput) {
  return apiFetch<Transfer>(`${BASE_URL}/${id}/reject`, {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

/** 完成迁移 (approved → completed) */
export async function completeTransfer(id: number) {
  return apiFetch<Transfer>(`${BASE_URL}/${id}/complete`, {
    method: 'POST',
  });
}
