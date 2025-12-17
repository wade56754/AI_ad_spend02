/**
 * Ad Accounts API Service
 *
 * SoT 对齐: DATA_SCHEMA.md v5.2
 */

import { apiFetch } from '@/lib/api';
import type {
  AdAccount,
  AdAccountListParams,
  AdAccountCreateInput,
  AdAccountStatusUpdateInput,
} from '../types';

const BASE_PATH = '/api/v1/ad-accounts';

// ========== Query Functions ==========

export async function getAdAccounts(params: AdAccountListParams = {}) {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.status) searchParams.set('status', params.status);
  if (params.project_id) searchParams.set('project_id', params.project_id);
  if (params.channel_id) searchParams.set('channel_id', params.channel_id);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  const response = await apiFetch<{
    data: AdAccount[];
    meta: { pagination: { page: number; page_size: number; total: number; total_pages: number } };
  }>(url);

  return response;
}

export async function getAdAccount(id: string): Promise<{ data: AdAccount }> {
  return apiFetch<{ data: AdAccount }>(`${BASE_PATH}/${id}`);
}

// ========== Mutation Functions ==========

export async function createAdAccount(input: AdAccountCreateInput): Promise<{ data: AdAccount }> {
  return apiFetch<{ data: AdAccount }>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
}

export async function updateAdAccountStatus(
  id: string,
  input: AdAccountStatusUpdateInput
): Promise<{ data: AdAccount }> {
  return apiFetch<{ data: AdAccount }>(`${BASE_PATH}/${id}/status`, {
    method: 'PUT',
    body: input,
  });
}

export async function deleteAdAccount(id: string): Promise<void> {
  await apiFetch(`${BASE_PATH}/${id}`, { method: 'DELETE' });
}
