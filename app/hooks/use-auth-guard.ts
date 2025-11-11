/**
 * 认证守卫Hook
 * 保护需要认证的路由
 */
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores'

interface AuthGuardOptions {
  redirectTo?: string
  requireAuth?: boolean
  roles?: string[]
}

export function useAuthGuard(options: AuthGuardOptions = {}) {
  const {
    redirectTo = '/auth/login',
    requireAuth = true,
    roles = [],
  } = options

  const router = useRouter()
  const { isAuthenticated, user } = useAuthStore()

  useEffect(() => {
    // 如果需要认证但用户未登录
    if (requireAuth && !isAuthenticated) {
      // 保存当前路径，登录后跳转回来
      const currentPath = window.location.pathname
      if (currentPath !== redirectTo) {
        sessionStorage.setItem('redirect_after_login', currentPath)
      }
      router.push(redirectTo)
      return
    }

    // 如果需要特定角色但用户角色不匹配
    if (requireAuth && isAuthenticated && roles.length > 0 && !roles.includes(user?.role || '')) {
      router.push('/403')
      return
    }

    // 如果已登录但访问认证页面，跳转到首页
    if (!requireAuth && isAuthenticated && redirectTo === '/auth/login') {
      const redirectPath = sessionStorage.getItem('redirect_after_login')
      sessionStorage.removeItem('redirect_after_login')
      router.push(redirectPath || '/')
    }
  }, [isAuthenticated, user, router, redirectTo, requireAuth, roles])

  return {
    isAuthenticated,
    user,
    canAccess: isAuthenticated && (roles.length === 0 || roles.includes(user?.role || '')),
  }
}