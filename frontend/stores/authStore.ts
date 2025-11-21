// stores/authStore.ts
'use client';

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'finance' | 'data_operator' | 'account_manager' | 'media_buyer';
}

interface AuthState {
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setAuth: (user, token) => set({ user, token }),
      clearAuth: () => set({ user: null, token: null }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => {
        // ✅ SSR 安全检查
        if (typeof window === 'undefined') {
          return {
            getItem: () => null,
            setItem: () => {},
            removeItem: () => {},
          };
        }
        return localStorage;
      }),
    }
  )
);

/**
 * 获取客户端 session (非 Hook 版本)
 * ⚠️ 仅在浏览器环境调用
 */
export function getClientSession() {
  if (typeof window === 'undefined') {
    return { user: null, token: null };
  }
  return useAuthStore.getState();
}
