/**
 * Authentication hooks
 * SoT: AUTH_SPEC.md v2.0
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiPost, apiGet, queryKeys } from '@/lib/api';
import { saveTokens, clearTokens } from '@/lib/auth';
import { useRouter } from 'next/navigation';

export interface LoginRequest {
  identifier: string;
  password: string;
  remember_me?: boolean;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  user: User;
}

export function useAuth() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // Get current user
  const { data: user, isLoading } = useQuery({
    queryKey: queryKeys.auth.me(),
    queryFn: async () => {
      const response = await apiGet<User>('/api/v1/auth/me');
      return response.data;
    },
    enabled: typeof window !== 'undefined' && !!localStorage.getItem('auth-token'),
    retry: false,
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      const response = await apiPost<LoginResponse>('/api/v1/auth/login', credentials);
      return response.data;
    },
    onSuccess: (data) => {
      if (data) {
        saveTokens({
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          expiresAt: Date.now() + (data.expires_in || 3600) * 1000,
        });
        queryClient.invalidateQueries({ queryKey: queryKeys.auth.all });
        router.push('/');
      }
    },
  });

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: async () => {
      await apiPost('/api/v1/auth/logout');
    },
    onSettled: () => {
      clearTokens();
      queryClient.clear();
      router.push('/login');
    },
  });

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    login: loginMutation.mutate,
    logout: logoutMutation.mutate,
    isLoggingIn: loginMutation.isPending,
  };
}