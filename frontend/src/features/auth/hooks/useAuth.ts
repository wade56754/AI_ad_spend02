/**
 * Auth Hooks
 *
 * SoT 对齐: AUTH_SPEC.md v2.0
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  login as loginApi,
  logout as logoutApi,
  getCurrentUser,
  register as registerApi,
  changePassword as changePasswordApi,
} from '../services';
import type {
  LoginRequest,
  RegisterRequest,
  ChangePasswordRequest,
  User,
  AuthState,
} from '../types';

const AUTH_TOKEN_KEY = 'auth_token';
const AUTH_USER_KEY = 'auth_user';

/**
 * Get stored auth token
 */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Set auth token
 */
export function setAuthToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

/**
 * Remove auth token
 */
export function removeAuthToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
}

/**
 * Main auth hook
 */
export function useAuth() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isInitialized, setIsInitialized] = useState(false);

  // TEMPORARY: Mock user for development (remove this in production)
  const MOCK_DEV_MODE = process.env.NODE_ENV === 'development' && !getAuthToken();

  // Get current user query
  const {
    data: user,
    isLoading,
    isError,
    refetch: refetchUser,
  } = useQuery({
    queryKey: ['auth', 'user'],
    queryFn: MOCK_DEV_MODE
      ? async () => ({
          id: 'mock-user-1',
          username: '演示用户',
          full_name: '演示用户',
          email: 'demo@example.com',
          role: 'admin',
          is_active: true,
          created_at: new Date().toISOString(),
        } as User)
      : getCurrentUser,
    enabled: MOCK_DEV_MODE || !!getAuthToken(),
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: loginApi,
    onSuccess: (data) => {
      setAuthToken(data.access_token);
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(data.user));
      queryClient.setQueryData(['auth', 'user'], data.user);
      router.push('/dashboard');
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: registerApi,
    onSuccess: (data) => {
      setAuthToken(data.access_token);
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(data.user));
      queryClient.setQueryData(['auth', 'user'], data.user);
      router.push('/dashboard');
    },
  });

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: logoutApi,
    onSuccess: () => {
      removeAuthToken();
      queryClient.clear();
      router.push('/login');
    },
    onError: () => {
      // Even if logout fails on server, clear local state
      removeAuthToken();
      queryClient.clear();
      router.push('/login');
    },
  });

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: changePasswordApi,
  });

  // Initialize auth state from localStorage
  useEffect(() => {
    const token = getAuthToken();
    const storedUser = localStorage.getItem(AUTH_USER_KEY);

    if (token && storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        queryClient.setQueryData(['auth', 'user'], parsedUser);
      } catch {
        removeAuthToken();
      }
    }
    setIsInitialized(true);
  }, [queryClient]);

  const login = useCallback(
    (data: LoginRequest) => loginMutation.mutateAsync(data),
    [loginMutation]
  );

  const register = useCallback(
    (data: RegisterRequest) => registerMutation.mutateAsync(data),
    [registerMutation]
  );

  const logout = useCallback(
    () => logoutMutation.mutateAsync(),
    [logoutMutation]
  );

  const changePassword = useCallback(
    (data: ChangePasswordRequest) => changePasswordMutation.mutateAsync(data),
    [changePasswordMutation]
  );

  return {
    user: user || null,
    isAuthenticated: !!user && !!getAuthToken(),
    isLoading: !isInitialized || isLoading,
    isError,
    login,
    register,
    logout,
    changePassword,
    refetchUser,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
    isLoggingOut: logoutMutation.isPending,
  };
}

/**
 * Hook to require authentication
 */
export function useRequireAuth(redirectTo = '/login') {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(redirectTo);
    }
  }, [isLoading, isAuthenticated, router, redirectTo]);

  return { user, isLoading, isAuthenticated };
}

/**
 * Hook to require specific role
 */
export function useRequireRole(allowedRoles: string[], redirectTo = '/dashboard') {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      if (!allowedRoles.includes(user.role)) {
        router.push(redirectTo);
      }
    }
  }, [isLoading, isAuthenticated, user, allowedRoles, router, redirectTo]);

  return { user, isLoading, isAuthenticated, hasAccess: user ? allowedRoles.includes(user.role) : false };
}
