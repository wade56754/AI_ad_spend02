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

// 统一使用与 lib/auth.ts 相同的存储键
const AUTH_TOKEN_KEY = 'auth-token';
const AUTH_REFRESH_TOKEN_KEY = 'refresh-token';
const AUTH_USER_KEY = 'auth-user';
// Cookie 名称 - 与 middleware.ts 保持一致
const AUTH_COOKIE_NAME = 'access_token';

/**
 * Get stored auth token
 */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Set auth token (同时设置 localStorage 和 Cookie)
 * Cookie 供 middleware 使用，localStorage 供客户端使用
 */
export function setAuthToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(AUTH_TOKEN_KEY, token);
  // 设置 Cookie 供 middleware 验证
  // HttpOnly: false 允许 JS 访问, Secure: 生产环境启用, SameSite: Lax 防 CSRF
  const isSecure = window.location.protocol === 'https:';
  document.cookie = `${AUTH_COOKIE_NAME}=${token}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Lax${isSecure ? '; Secure' : ''}`;
}

/**
 * Remove auth token (同时清除 localStorage 和 Cookie)
 */
export function removeAuthToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
  // 清除 Cookie
  document.cookie = `${AUTH_COOKIE_NAME}=; path=/; max-age=0`;
}

/**
 * Main auth hook
 *
 * SoT Reference: AUTH_SPEC.md v2.0
 */
export function useAuth() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isInitialized, setIsInitialized] = useState(false);

  // Get stored user from localStorage for initial data
  const getStoredUser = (): User | undefined => {
    try {
      const stored = localStorage.getItem(AUTH_USER_KEY);
      return stored ? JSON.parse(stored) : undefined;
    } catch {
      return undefined;
    }
  };

  // Get current user query
  // SoT Reference: AUTH_SPEC.md v2.0 §7.4 - 401 errors should clear tokens silently
  const {
    data: user,
    isLoading,
    isError,
    refetch: refetchUser,
  } = useQuery({
    queryKey: ['auth', 'user'],
    queryFn: async () => {
      try {
        return await getCurrentUser();
      } catch (error: unknown) {
        // Handle ALL auth errors silently - just clear tokens and return null
        // This prevents expired token errors from showing as toasts
        // api.ts already handles 401 by clearing tokens
        const apiError = error as { status?: number; silent?: boolean };

        // For 401 errors or silent errors, just return null
        if (apiError?.status === 401 || apiError?.silent) {
          removeAuthToken();
          return null;
        }

        // For other errors, still return null to prevent toast display
        // Auth errors should never show toasts - just redirect to login
        console.warn('[useAuth] getCurrentUser failed:', error);
        return null;
      }
    },
    enabled: !!getAuthToken(),
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
    // Use stored user as initial data to avoid flash of unauthenticated state
    initialData: getStoredUser,
    // Keep previous data when query fails (e.g., network error, 401 from expired token)
    placeholderData: (previousData) => previousData,
    // Don't throw errors for auth queries - handle them silently
    throwOnError: false,
    // Skip global error handler toast for auth queries
    meta: { skipErrorToast: true },
    // Don't cache failed results
    gcTime: 0,
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: loginApi,
    onSuccess: (data) => {
      // Token 在 data.session.access_token (后端返回结构)
      const token = data.session?.access_token || data.access_token;
      if (token) {
        setAuthToken(token);
      }
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(data.user));
      queryClient.setQueryData(['auth', 'user'], data.user);
      // Redirect to home page (dashboard is under (dashboard) route group at /)
      router.push('/');
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: registerApi,
    onSuccess: (data) => {
      // Token 在 data.session.access_token (后端返回结构)
      const token = data.session?.access_token || data.access_token;
      if (token) {
        setAuthToken(token);
      }
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(data.user));
      queryClient.setQueryData(['auth', 'user'], data.user);
      // Redirect to home page (dashboard is under (dashboard) route group at /)
      router.push('/');
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

  const logout = useCallback(() => logoutMutation.mutateAsync(), [logoutMutation]);

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
 *
 * 改进: 增加 isRoleVerified 标志，确保角色信息从服务器确认后再进行权限判断
 */
export function useRequireRole(allowedRoles: string[], redirectTo = '/') {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [isRoleVerified, setIsRoleVerified] = useState(false);

  // 当用户数据加载完成后，标记角色已验证
  useEffect(() => {
    if (!isLoading && user) {
      setIsRoleVerified(true);
    } else if (!isLoading && !user) {
      setIsRoleVerified(false);
    }
  }, [isLoading, user]);

  // 权限重定向逻辑 - 只在角色验证完成后执行
  useEffect(() => {
    if (!isLoading && isRoleVerified && isAuthenticated && user) {
      if (!allowedRoles.includes(user.role)) {
        router.push(redirectTo);
      }
    }
  }, [isLoading, isRoleVerified, isAuthenticated, user, allowedRoles, router, redirectTo]);

  // 计算是否有访问权限 - 只在角色验证后才判断
  const hasAccess = isRoleVerified && user ? allowedRoles.includes(user.role) : false;

  // isCheckingRole: 正在验证角色中（加载中或等待角色验证）
  const isCheckingRole = isLoading || (!isRoleVerified && !!user);

  return {
    user,
    isLoading,
    isAuthenticated,
    hasAccess,
    isCheckingRole, // 新增: 用于组件判断是否显示加载状态
    isRoleVerified, // 新增: 角色是否已验证
  };
}

/**
 * Hook to check if user has permission for specific action
 *
 * 用于细粒度权限控制，确保权限检查在角色加载完成后进行
 *
 * @deprecated 推荐使用 @/hooks/usePermission，提供更完整的权限检查功能
 */
export function useRolePermission(requiredRoles: string[]) {
  const { user, isLoading } = useAuth();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      setIsReady(true);
    }
  }, [isLoading]);

  return {
    // 权限是否正在加载中
    isLoading: !isReady,
    // 是否有权限 - 只在加载完成后返回 true
    hasPermission: isReady && user ? requiredRoles.includes(user.role) : false,
    // 用户角色
    userRole: user?.role,
  };
}
