/**
 * Profile Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  getProfile,
  updateProfile,
  changePassword,
  getActivityLogs,
  uploadAvatar,
} from '../services';
import type { ProfileUpdateData } from '../types';

/**
 * Hook to fetch user profile
 */
export function useProfile() {
  return useQuery({
    queryKey: ['profile'],
    queryFn: getProfile,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to update user profile
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ProfileUpdateData) => updateProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      toast.success('个人信息已更新');
    },
    onError: (error: Error) => {
      toast.error(error.message || '更新失败');
    },
  });
}

/**
 * Hook to change password
 */
export function useChangePassword() {
  return useMutation({
    mutationFn: ({ currentPassword, newPassword }: { currentPassword: string; newPassword: string }) =>
      changePassword(currentPassword, newPassword),
    onSuccess: () => {
      toast.success('密码已更新');
    },
    onError: (error: Error) => {
      toast.error(error.message || '密码更新失败');
    },
  });
}

/**
 * Hook to fetch activity logs
 */
export function useActivityLogs(params: { page?: number; page_size?: number } = {}) {
  return useQuery({
    queryKey: ['profile', 'activity', params],
    queryFn: () => getActivityLogs(params),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook to upload avatar
 */
export function useUploadAvatar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => uploadAvatar(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      toast.success('头像已更新');
    },
    onError: (error: Error) => {
      toast.error(error.message || '头像上传失败');
    },
  });
}
