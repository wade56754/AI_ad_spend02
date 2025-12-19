/**
 * Auth Mock Helpers
 *
 * 提供认证相关的 mock 工具函数
 */

import { UserRole } from '@/features/auth/types/auth.types'

/**
 * Mock 用户数据
 */
export const mockUser = {
  id: 'user-test-id-001',
  email: 'test@example.com',
  username: 'testuser',
  role: 'admin' as UserRole,
  is_active: true,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
}

/**
 * Mock JWT Token
 */
export const mockToken = 'mock-jwt-token-for-testing'

/**
 * Mock 登录响应
 */
export function mockLoginResponse() {
  return {
    access_token: mockToken,
    token_type: 'bearer',
    user: mockUser,
  }
}

/**
 * Mock localStorage for auth
 */
export function mockAuthStorage(token?: string, user?: any) {
  const storage: Record<string, string> = {}

  if (token) {
    storage['auth-token'] = token
  }

  if (user) {
    storage['auth-user'] = JSON.stringify(user)
  }

  const mockGetItem = jest.fn((key: string) => storage[key] || null)
  const mockSetItem = jest.fn((key: string, value: string) => {
    storage[key] = value
  })
  const mockRemoveItem = jest.fn((key: string) => {
    delete storage[key]
  })
  const mockClear = jest.fn(() => {
    Object.keys(storage).forEach((key) => delete storage[key])
  })

  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: mockGetItem,
      setItem: mockSetItem,
      removeItem: mockRemoveItem,
      clear: mockClear,
      length: Object.keys(storage).length,
      key: jest.fn((index: number) => Object.keys(storage)[index] || null),
    },
    writable: true,
  })

  return {
    getItem: mockGetItem,
    setItem: mockSetItem,
    removeItem: mockRemoveItem,
    clear: mockClear,
  }
}

/**
 * Mock 认证状态为已登录
 */
export function mockAuthenticatedState() {
  return mockAuthStorage(mockToken, mockUser)
}

/**
 * Mock 认证状态为未登录
 */
export function mockUnauthenticatedState() {
  return mockAuthStorage()
}

/**
 * 不同角色的 mock 用户
 */
export const mockUsers = {
  admin: {
    ...mockUser,
    role: 'admin' as UserRole,
  },
  finance: {
    ...mockUser,
    id: 'user-finance-id-001',
    email: 'finance@example.com',
    username: 'financeuser',
    role: 'finance' as UserRole,
  },
  data_operator: {
    ...mockUser,
    id: 'user-operator-id-001',
    email: 'operator@example.com',
    username: 'operatoruser',
    role: 'data_operator' as UserRole,
  },
  account_manager: {
    ...mockUser,
    id: 'user-am-id-001',
    email: 'am@example.com',
    username: 'amuser',
    role: 'account_manager' as UserRole,
  },
  media_buyer: {
    ...mockUser,
    id: 'user-buyer-id-001',
    email: 'buyer@example.com',
    username: 'buyeruser',
    role: 'media_buyer' as UserRole,
  },
}

/**
 * Mock 特定角色的认证状态
 */
export function mockAuthenticatedStateWithRole(role: UserRole) {
  const user = mockUsers[role] || mockUsers.admin
  return mockAuthStorage(mockToken, user)
}
