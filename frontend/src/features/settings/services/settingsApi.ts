/**
 * Settings API Service
 */

import { apiGet, apiPut } from '@/lib/api';
import type { SystemSettings, UserPreferences } from '../types';

const BASE_PATH = '/api/v1/settings';

/**
 * Get system settings (admin only)
 */
export async function getSystemSettings(): Promise<SystemSettings> {
  return apiGet<SystemSettings>(`${BASE_PATH}/system`);
}

/**
 * Update system settings (admin only)
 */
export async function updateSystemSettings(settings: Partial<SystemSettings>): Promise<SystemSettings> {
  return apiPut<SystemSettings>(`${BASE_PATH}/system`, settings);
}

/**
 * Get user preferences
 */
export async function getUserPreferences(): Promise<UserPreferences> {
  return apiGet<UserPreferences>(`${BASE_PATH}/preferences`);
}

/**
 * Update user preferences
 */
export async function updateUserPreferences(preferences: Partial<UserPreferences>): Promise<UserPreferences> {
  return apiPut<UserPreferences>(`${BASE_PATH}/preferences`, preferences);
}

/**
 * Reset user preferences to defaults
 */
export async function resetUserPreferences(): Promise<UserPreferences> {
  return apiPut<UserPreferences>(`${BASE_PATH}/preferences/reset`, {});
}
