/**
 * 认证 Hook
 * 管理用户认证状态和操作
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  supabase,
  getUserProfile,
  signIn as supabaseSignIn,
  signUp as supabaseSignUp,
  signOut as supabaseSignOut,
  resetPassword as supabaseResetPassword,
  updatePassword as supabaseUpdatePassword,
  type UserProfile,
  type AuthUser
} from '@/lib/supabase'
import type { User, Session } from '@supabase/supabase-js'

interface AuthState {
  user: User | null
  profile: UserProfile | null
  session: Session | null
  loading: boolean
  error: string | null
}

export function useAuth() {
  const router = useRouter()
  const [state, setState] = useState<AuthState>({
    user: null,
    profile: null,
    session: null,
    loading: true,
    error: null,
  })

  // 初始化认证状态
  useEffect(() => {
    // 获取初始会话
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (session?.user) {
        const profile = await getUserProfile(session.user.id)
        setState({
          user: session.user,
          profile,
          session,
          loading: false,
          error: null,
        })
      } else {
        setState({
          user: null,
          profile: null,
          session: null,
          loading: false,
          error: null,
        })
      }
    })

    // 监听认证状态变化
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log('Auth state changed:', event)

      if (session?.user) {
        const profile = await getUserProfile(session.user.id)
        setState({
          user: session.user,
          profile,
          session,
          loading: false,
          error: null,
        })

        // 登录成功后跳转
        if (event === 'SIGNED_IN') {
          router.push('/')
        }
      } else {
        setState({
          user: null,
          profile: null,
          session: null,
          loading: false,
          error: null,
        })

        // 登出后跳转到登录页
        if (event === 'SIGNED_OUT') {
          router.push('/auth/login')
        }
      }
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [router])

  // 登录
  const signIn = async (email: string, password: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const { data, error } = await supabaseSignIn(email, password)

      if (error) {
        setState(prev => ({
          ...prev,
          loading: false,
          error,
        }))
        return { success: false, error }
      }

      // 状态会通过 onAuthStateChange 自动更新
      return { success: true, error: null }
    } catch (error: any) {
      const errorMessage = error.message || '登录失败'
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }))
      return { success: false, error: errorMessage }
    }
  }

  // 注册
  const signUp = async (
    email: string,
    password: string,
    metadata?: {
      username?: string
      full_name?: string
      role?: string
    }
  ) => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const { data, error } = await supabaseSignUp(email, password, metadata)

      if (error) {
        setState(prev => ({
          ...prev,
          loading: false,
          error,
        }))
        return { success: false, error }
      }

      setState(prev => ({ ...prev, loading: false }))
      return { success: true, error: null }
    } catch (error: any) {
      const errorMessage = error.message || '注册失败'
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }))
      return { success: false, error: errorMessage }
    }
  }

  // 登出
  const signOut = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const { error } = await supabaseSignOut()

      if (error) {
        setState(prev => ({
          ...prev,
          loading: false,
          error,
        }))
        return { success: false, error }
      }

      // 状态会通过 onAuthStateChange 自动更新
      return { success: true, error: null }
    } catch (error: any) {
      const errorMessage = error.message || '登出失败'
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }))
      return { success: false, error: errorMessage }
    }
  }

  // 重置密码
  const resetPassword = async (email: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const { error } = await supabaseResetPassword(email)

      if (error) {
        setState(prev => ({
          ...prev,
          loading: false,
          error,
        }))
        return { success: false, error }
      }

      setState(prev => ({ ...prev, loading: false }))
      return { success: true, error: null }
    } catch (error: any) {
      const errorMessage = error.message || '重置密码失败'
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }))
      return { success: false, error: errorMessage }
    }
  }

  // 更新密码
  const updatePassword = async (newPassword: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const { error } = await supabaseUpdatePassword(newPassword)

      if (error) {
        setState(prev => ({
          ...prev,
          loading: false,
          error,
        }))
        return { success: false, error }
      }

      setState(prev => ({ ...prev, loading: false }))
      return { success: true, error: null }
    } catch (error: any) {
      const errorMessage = error.message || '更新密码失败'
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }))
      return { success: false, error: errorMessage }
    }
  }

  return {
    user: state.user,
    profile: state.profile,
    session: state.session,
    loading: state.loading,
    error: state.error,
    isAuthenticated: !!state.user,
    signIn,
    signUp,
    signOut,
    resetPassword,
    updatePassword,
  }
}
