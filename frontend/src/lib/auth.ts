/**
 * Authentication utilities
 * SoT: AUTH_SPEC.md v2.2
 */

import { apiPost } from './api';

const TOKEN_KEY = 'auth-token';
const REFRESH_TOKEN_KEY = 'refresh-token';
const TOKEN_EXPIRY_KEY = 'token-expiry';

/**
 * 检查是否在浏览器环境
 */
function isBrowser(): boolean {
  return typeof window !== 'undefined';
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in?: number;
}

export function saveTokens(tokens: AuthTokens): void {
  if (!isBrowser()) return;
  localStorage.setItem(TOKEN_KEY, tokens.accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);
  localStorage.setItem(TOKEN_EXPIRY_KEY, tokens.expiresAt.toString());
}

export function getAccessToken(): string | null {
  if (!isBrowser()) return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (!isBrowser()) return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function clearTokens(): void {
  if (!isBrowser()) return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(TOKEN_EXPIRY_KEY);
}

export function isTokenExpired(): boolean {
  if (!isBrowser()) return true;
  const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
  if (!expiry) return true;
  return Date.now() >= parseInt(expiry, 10);
}

export async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    clearTokens();
    return false;
  }

  try {
    const tokenInfo = await apiPost<RefreshTokenResponse>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });

    saveTokens({
      accessToken: tokenInfo.access_token,
      refreshToken: tokenInfo.refresh_token,
      expiresAt: Date.now() + (tokenInfo.expires_in || 3600) * 1000,
    });
    return true;
  } catch (error) {
    console.error('Token refresh failed:', error);
    clearTokens();
    return false;
  }
}
