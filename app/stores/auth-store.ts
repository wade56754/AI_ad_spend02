/**
 * 认证状态管理
 * 使用Zustand管理用户认证状态
 */
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import { api, tokenManager } from '@/lib/api'

// 用户类型定义
export interface User {
  id: number
  email: string
  username: string
  full_name?: string
  role: 'admin' | 'finance' | 'data_operator' | 'account_manager' | 'media_buyer'
  is_active: boolean
  is_superuser: boolean
  avatar_url?: string
  created_at: string
  updated_at: string
  last_login?: string
}

// 登录数据类型
export interface LoginData {
  email: string
  password: string
  remember?: boolean
}

// 认证状态类型
interface AuthState {
  // 状态
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // 操作
  login: (data: LoginData) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
  updateProfile: (data: Partial<User>) => Promise<void>
  changePassword: (oldPassword: string, newPassword: string) => Promise<void>
  clearError: () => void
}

// 创建认证store
export const useAuthStore = create<AuthState>()(
  persist(
    immer((set, get) => ({
      // 初始状态
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // 登录
      login: async (data: LoginData) => {
        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await api.post<{
            access_token: string
            refresh_token: string
            user: User
          }>('/api/v1/auth/login', data)

          const { access_token, refresh_token, user } = response.data

          // 保存token
          tokenManager.setTokens(access_token, refresh_token)

          // 更新状态
          set((state) => {
            state.user = user
            state.isAuthenticated = true
            state.isLoading = false
            state.error = null
          })

          // 记住登录状态
          if (data.remember) {
            localStorage.setItem('remember_me', 'true')
          }
        } catch (error: any) {
          const message = error.response?.data?.error?.message || '登录失败'
          set((state) => {
            state.isLoading = false
            state.error = message
          })
          throw error
        }
      },

      // 登出
      logout: () => {
        // 清除token
        tokenManager.clearTokens()

        // 清除记住登录状态
        localStorage.removeItem('remember_me')

        // 重置状态
        set((state) => {
          state.user = null
          state.isAuthenticated = false
          state.error = null
        })

        // 调用登出API（可选）
        api.post('/api/v1/auth/logout').catch(() => {
          // 忽略错误
        })
      },

      // 刷新token
      refreshToken: async () => {
        try {
          await tokenManager.refreshAccessToken()
          // Token刷新成功，可以重新获取用户信息
          const response = await api.get<User>('/api/v1/auth/me')
          set((state) => {
            state.user = response.data.data
          })
        } catch (error) {
          // 刷新失败，自动登出
          get().logout()
          throw error
        }
      },

      // 更新个人资料
      updateProfile: async (data: Partial<User>) => {
        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await api.put<User>('/api/v1/auth/profile', data)

          set((state) => {
            state.user = response.data.data
            state.isLoading = false
          })
        } catch (error: any) {
          const message = error.response?.data?.error?.message || '更新失败'
          set((state) => {
            state.isLoading = false
            state.error = message
          })
          throw error
        }
      },

      // 修改密码
      changePassword: async (oldPassword: string, newPassword: string) => {
        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          await api.post('/api/v1/auth/change-password', {
            old_password: oldPassword,
            new_password: newPassword,
          })

          set((state) => {
            state.isLoading = false
          })
        } catch (error: any) {
          const message = error.response?.data?.error?.message || '修改密码失败'
          set((state) => {
            state.isLoading = false
            state.error = message
          })
          throw error
        }
      },

      // 清除错误
      clearError: () => {
        set((state) => {
          state.error = null
        })
      },
    })),
    {
      name: 'auth-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        // 恢复状态后检查token有效性
        if (state?.isAuthenticated && state.user) {
          // 如果设置了记住登录，尝试刷新token
          if (localStorage.getItem('remember_me') === 'true') {
            get().refreshToken().catch(() => {
              // 刷新失败，清除状态
              state?.logout()
            })
          } else {
            // 没有设置记住登录，清除状态
            state?.logout()
          }
        }
      },
    }
  )
)

// 权限检查Hook
export function usePermissions() {
  const user = useAuthStore((state) => state.user)

  const hasRole = (role: string | string[]) => {
    if (!user) return false
    if (Array.isArray(role)) {
      return role.includes(user.role)
    }
    return user.role === role
  }

  const hasPermission = (permission: string) => {
    if (!user) return false

    // 管理员拥有所有权限
    if (user.role === 'admin') return true

    // 根据角色检查权限
    const rolePermissions: Record<string, string[]> = {
      finance: [
        'finance:read',
        'finance:create',
        'finance:update',
        'topup:approve',
        'topup:confirm',
        'reconciliation:manage',
      ],
      data_operator: [
        'project:read',
        'project:update',
        'account:read',
        'account:assign',
        'report:submit',
        'report:review',
      ],
      account_manager: [
        'account:create',
        'account:read',
        'account:update',
        'channel:read',
        'channel:apply',
      ],
      media_buyer: [
        'account:read',
        'account:monitor',
        'report:submit',
        'topup:request',
      ],
    }

    const permissions = rolePermissions[user.role] || []
    return permissions.includes(permission) || permissions.includes('*')
  }

  return {
    user,
    hasRole,
    hasPermission,
    isAdmin: user?.role === 'admin',
    isFinance: user?.role === 'finance',
    isDataOperator: user?.role === 'data_operator',
    isAccountManager: user?.role === 'account_manager',
    isMediaBuyer: user?.role === 'media_buyer',
  }
}