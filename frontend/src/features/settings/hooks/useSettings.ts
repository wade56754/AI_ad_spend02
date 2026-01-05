/**
 * Settings Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  getSystemSettings,
  updateSystemSettings,
  getUserPreferences,
  updateUserPreferences,
  resetUserPreferences,
} from '../services';
import type { SystemSettings, UserPreferences } from '../types';

/**
 * Hook to fetch system settings (admin only)
 */
export function useSystemSettings() {
  return useQuery({
    queryKey: ['settings', 'system'],
    queryFn: getSystemSettings,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to update system settings (admin only)
 */
export function useUpdateSystemSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (settings: Partial<SystemSettings>) => updateSystemSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'system'] });
      toast.success('系统设置已更新');
    },
    onError: (error: Error) => {
      toast.error(error.message || '更新失败');
    },
  });
}

/**
 * Hook to fetch user preferences
 */
export function useUserPreferences() {
  return useQuery({
    queryKey: ['settings', 'preferences'],
    queryFn: getUserPreferences,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to update user preferences
 */
export function useUpdateUserPreferences() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (preferences: Partial<UserPreferences>) => updateUserPreferences(preferences),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'preferences'] });
      toast.success('偏好设置已保存');
    },
    onError: (error: Error) => {
      toast.error(error.message || '保存失败');
    },
  });
}

/**
 * Hook to reset user preferences
 */
export function useResetUserPreferences() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: resetUserPreferences,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'preferences'] });
      toast.success('偏好设置已重置');
    },
    onError: (error: Error) => {
      toast.error(error.message || '重置失败');
    },
  });
}
