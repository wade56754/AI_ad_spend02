/**
 * Channels API Service
 *
 * SoT 对齐:
 * - DATA_SCHEMA.md v5.2 (channels entity)
 * - backend/routers/channels.py
 */

import { apiFetch } from '@/lib/api';
import type {
  Channel,
  ChannelListParams,
  ChannelCreateInput,
  ChannelUpdateInput,
  ChannelListResponse,
} from '../types/channel.types';

const BASE_PATH = '/api/v1/channels';

// ========== Query Functions ==========

/**
 * Get paginated list of channels
 * GET /api/v1/channels
 */
export async function getChannels(
  params: ChannelListParams = {}
): Promise<ChannelListResponse> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.is_active !== undefined) searchParams.set('is_active', String(params.is_active));
  if (params.search) searchParams.set('search', params.search);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  return apiFetch<ChannelListResponse>(url);
}

/**
 * Get single channel by ID
 * GET /api/v1/channels/:id
 */
export async function getChannel(id: string): Promise<{ data: Channel }> {
  return apiFetch<{ data: Channel }>(`${BASE_PATH}/${id}`);
}

// ========== Mutation Functions ==========

/**
 * Create new channel
 * POST /api/v1/channels
 */
export async function createChannel(
  input: ChannelCreateInput
): Promise<{ data: Channel }> {
  return apiFetch<{ data: Channel }>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
}

/**
 * Update channel
 * PUT /api/v1/channels/:id
 */
export async function updateChannel(
  id: string,
  input: ChannelUpdateInput
): Promise<{ data: Channel }> {
  return apiFetch<{ data: Channel }>(`${BASE_PATH}/${id}`, {
    method: 'PUT',
    body: input,
  });
}

// ========== Status Actions ==========

/**
 * Activate channel
 */
export async function activateChannel(id: string): Promise<{ data: Channel }> {
  return updateChannel(id, { is_active: true });
}

/**
 * Deactivate channel
 */
export async function deactivateChannel(id: string): Promise<{ data: Channel }> {
  return updateChannel(id, { is_active: false });
}
