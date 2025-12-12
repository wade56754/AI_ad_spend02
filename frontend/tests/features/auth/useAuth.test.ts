/**
 * useAuth Hook Tests
 *
 * Tests for frontend/src/features/auth/hooks/useAuth.ts
 * SoT: AUTH_SPEC.md v2.0
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useAuth,
  getAuthToken,
  setAuthToken,
  removeAuthToken,
} from '@/features/auth/hooks/useAuth';
import * as authServices from '@/features/auth/services';

// Mock the auth services
jest.mock('@/features/auth/services', () => ({
  login: jest.fn(),
  logout: jest.fn(),
  getCurrentUser: jest.fn(),
  register: jest.fn(),
  changePassword: jest.fn(),
}));

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
    _getStore: () => store,
    _setStore: (newStore: Record<string, string>) => {
      store = newStore;
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Test wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe('Auth Token Utilities', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock._setStore({});
  });

  describe('getAuthToken', () => {
    it('should return null when no token exists', () => {
      const token = getAuthToken();
      expect(token).toBeNull();
    });

    it('should return the stored token', () => {
      localStorageMock._setStore({ 'auth-token': 'test-token-123' });
      const token = getAuthToken();
      expect(token).toBe('test-token-123');
    });
  });

  describe('setAuthToken', () => {
    it('should store the token in localStorage', () => {
      setAuthToken('new-token-456');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth-token', 'new-token-456');
    });
  });

  describe('removeAuthToken', () => {
    it('should remove auth token and user from localStorage', () => {
      localStorageMock._setStore({
        'auth-token': 'token',
        'auth-user': '{"id":"1"}',
      });

      removeAuthToken();

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth-token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth-user');
    });
  });
});

describe('useAuth Hook', () => {
  const mockUser = {
    id: 'user-123',
    email: 'test@example.com',
    username: 'testuser',
    role: 'admin',
    is_active: true,
    created_at: '2025-01-01T00:00:00Z',
  };

  const mockLoginResponse = {
    user: mockUser,
    access_token: 'new-access-token',
    refresh_token: 'new-refresh-token',
    expires_in: 3600,
    token_type: 'bearer',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock._setStore({});
    mockPush.mockClear();
  });

  it('should return initial unauthenticated state', async () => {
    (authServices.getCurrentUser as jest.Mock).mockRejectedValue(new Error('No token'));

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('should return authenticated state when token and user exist', async () => {
    localStorageMock._setStore({
      'auth-token': 'valid-token',
      'auth-user': JSON.stringify(mockUser),
    });
    (authServices.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  describe('login', () => {
    it('should login successfully and redirect to dashboard', async () => {
      (authServices.login as jest.Mock).mockResolvedValue(mockLoginResponse);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.login({
          identifier: 'test@example.com',
          password: 'password123',
        });
      });

      expect(authServices.login).toHaveBeenCalledWith({
        identifier: 'test@example.com',
        password: 'password123',
      });
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth-token', 'new-access-token');
      expect(mockPush).toHaveBeenCalledWith('/dashboard');
    });

    it('should handle login error', async () => {
      const loginError = new Error('Invalid credentials');
      (authServices.login as jest.Mock).mockRejectedValue(loginError);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await expect(
        act(async () => {
          await result.current.login({
            identifier: 'test@example.com',
            password: 'wrong-password',
          });
        })
      ).rejects.toThrow('Invalid credentials');
    });
  });

  describe('logout', () => {
    it('should logout and redirect to login page', async () => {
      localStorageMock._setStore({
        'auth-token': 'valid-token',
        'auth-user': JSON.stringify(mockUser),
      });
      (authServices.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);
      (authServices.logout as jest.Mock).mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      await act(async () => {
        await result.current.logout();
      });

      expect(authServices.logout).toHaveBeenCalled();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth-token');
      expect(mockPush).toHaveBeenCalledWith('/login');
    });

    it('should clear local state even if server logout fails', async () => {
      localStorageMock._setStore({
        'auth-token': 'valid-token',
        'auth-user': JSON.stringify(mockUser),
      });
      (authServices.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);
      (authServices.logout as jest.Mock).mockRejectedValue(new Error('Server error'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      await act(async () => {
        try {
          await result.current.logout();
        } catch {
          // Expected to handle error internally
        }
      });

      // Should still clear local state and redirect
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth-token');
      expect(mockPush).toHaveBeenCalledWith('/login');
    });
  });

  describe('register', () => {
    it('should register successfully and redirect to dashboard', async () => {
      (authServices.register as jest.Mock).mockResolvedValue(mockLoginResponse);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.register({
          email: 'new@example.com',
          password: 'password123',
          username: 'newuser',
        });
      });

      expect(authServices.register).toHaveBeenCalledWith({
        email: 'new@example.com',
        password: 'password123',
        username: 'newuser',
      });
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth-token', 'new-access-token');
      expect(mockPush).toHaveBeenCalledWith('/dashboard');
    });
  });

  describe('changePassword', () => {
    it('should change password successfully', async () => {
      localStorageMock._setStore({
        'auth-token': 'valid-token',
        'auth-user': JSON.stringify(mockUser),
      });
      (authServices.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);
      (authServices.changePassword as jest.Mock).mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      await act(async () => {
        await result.current.changePassword({
          old_password: 'oldpass',
          new_password: 'newpass',
        });
      });

      expect(authServices.changePassword).toHaveBeenCalledWith({
        old_password: 'oldpass',
        new_password: 'newpass',
      });
    });
  });

  describe('loading states', () => {
    it('should indicate when logging in', async () => {
      let resolveLogin: (value: unknown) => void;
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve;
      });
      (authServices.login as jest.Mock).mockImplementation(() => loginPromise);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Start login but don't await
      act(() => {
        result.current.login({
          identifier: 'test@example.com',
          password: 'password123',
        });
      });

      expect(result.current.isLoggingIn).toBe(true);

      // Resolve the login
      await act(async () => {
        resolveLogin!(mockLoginResponse);
        await loginPromise;
      });

      await waitFor(() => {
        expect(result.current.isLoggingIn).toBe(false);
      });
    });

    it('should indicate when logging out', async () => {
      localStorageMock._setStore({
        'auth-token': 'valid-token',
        'auth-user': JSON.stringify(mockUser),
      });
      (authServices.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

      let resolveLogout: () => void;
      const logoutPromise = new Promise<void>((resolve) => {
        resolveLogout = resolve;
      });
      (authServices.logout as jest.Mock).mockImplementation(() => logoutPromise);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      // Start logout but don't await
      act(() => {
        result.current.logout();
      });

      expect(result.current.isLoggingOut).toBe(true);

      // Resolve the logout
      await act(async () => {
        resolveLogout!();
        await logoutPromise;
      });

      await waitFor(() => {
        expect(result.current.isLoggingOut).toBe(false);
      });
    });
  });

  describe('initialization from localStorage', () => {
    it('should initialize user from localStorage on mount', async () => {
      const storedUser = { ...mockUser, username: 'storeduser' };
      localStorageMock._setStore({
        'auth-token': 'stored-token',
        'auth-user': JSON.stringify(storedUser),
      });
      (authServices.getCurrentUser as jest.Mock).mockResolvedValue(storedUser);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.user?.username).toBe('storeduser');
    });

    it('should clear invalid stored user data', async () => {
      localStorageMock._setStore({
        'auth-token': 'stored-token',
        'auth-user': 'invalid-json{',
      });

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth-token');
    });
  });
});
