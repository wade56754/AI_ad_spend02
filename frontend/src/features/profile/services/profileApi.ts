/**
 * Profile API Service
 */

import { apiGet, apiPut, apiPost } from '@/lib/api';
import type { UserProfile, ProfileUpdateData, ActivityLog } from '../types';
import type { PaginatedResponse } from '@/types';

const BASE_PATH = '/api/v1/profile';

/**
 * Get current user profile
 */
export async function getProfile(): Promise<UserProfile> {
  return apiGet<UserProfile>(BASE_PATH);
}

/**
 * Update user profile
 */
export async function updateProfile(data: ProfileUpdateData): Promise<UserProfile> {
  return apiPut<UserProfile>(BASE_PATH, data);
}

/**
 * Change password
 */
export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  return apiPost<void>(`${BASE_PATH}/change-password`, {
    current_password: currentPassword,
    new_password: newPassword,
  });
}

/**
 * Get user activity logs
 */
export async function getActivityLogs(params: {
  page?: number;
  page_size?: number;
} = {}): Promise<PaginatedResponse<ActivityLog>> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));

  const query = searchParams.toString();
  return apiGet<PaginatedResponse<ActivityLog>>(`${BASE_PATH}/activity?${query}`);
}

/**
 * Upload avatar
 */
export async function uploadAvatar(file: File): Promise<{ url: string }> {
  const formData = new FormData();
  formData.append('file', file);

  return apiPost<{ url: string }>(`${BASE_PATH}/avatar`, formData);
}
