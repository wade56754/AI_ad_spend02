/**
 * Auth API Service
 *
 * SoT 对齐: AUTH_SPEC.md v2.0
 */

import { apiFetch } from '@/lib/api';
import type {
  LoginRequest,
  RegisterRequest,
  ChangePasswordRequest,
  AuthResponse,
  User,
} from '../types';

const BASE_PATH = '/api/v1/auth';

/**
 * Login
 * POST /api/v1/auth/login
 */
export async function login(data: LoginRequest): Promise<AuthResponse> {
  // apiFetch already unwraps envelope { success, data } -> data
  return apiFetch<AuthResponse>(`${BASE_PATH}/login`, {
    method: 'POST',
    body: data,
  });
}

/**
 * Register
 * POST /api/v1/auth/register
 */
export async function register(data: RegisterRequest): Promise<AuthResponse> {
  // apiFetch already unwraps envelope { success, data } -> data
  return apiFetch<AuthResponse>(`${BASE_PATH}/register`, {
    method: 'POST',
    body: data,
  });
}

/**
 * Logout
 * POST /api/v1/auth/logout
 */
export async function logout(): Promise<void> {
  await apiFetch(`${BASE_PATH}/logout`, {
    method: 'POST',
  });
}

/**
 * Get current user
 * GET /api/v1/auth/me
 */
export async function getCurrentUser(): Promise<User> {
  // apiFetch already unwraps envelope { success, data } -> data
  return apiFetch<User>(`${BASE_PATH}/me`);
}

/**
 * Change password
 * POST /api/v1/auth/change-password
 */
export async function changePassword(data: ChangePasswordRequest): Promise<void> {
  await apiFetch(`${BASE_PATH}/change-password`, {
    method: 'POST',
    body: data,
  });
}

/**
 * Request password reset
 * POST /api/v1/auth/forgot-password
 */
export async function forgotPassword(email: string): Promise<void> {
  await apiFetch(`${BASE_PATH}/forgot-password`, {
    method: 'POST',
    body: { email },
  });
}

/**
 * Refresh token
 * POST /api/v1/auth/refresh
 */
export async function refreshToken(): Promise<AuthResponse> {
  // apiFetch already unwraps envelope { success, data } -> data
  return apiFetch<AuthResponse>(`${BASE_PATH}/refresh`, {
    method: 'POST',
  });
}

/**
 * Reset password with token
 * POST /api/v1/auth/reset-password
 */
export async function resetPassword(
  token: string,
  newPassword: string,
  refreshToken?: string | null
): Promise<void> {
  await apiFetch(`${BASE_PATH}/reset-password`, {
    method: 'POST',
    body: {
      token,
      new_password: newPassword,
      refresh_token: refreshToken || undefined,
    },
  });
}
