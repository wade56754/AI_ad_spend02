'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { resetPassword } from '../services/authApi';

export function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [tokenType, setTokenType] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 首先检查 query parameter (用于后端生成的链接)
    const tokenParam = searchParams.get('token');
    if (tokenParam) {
      setToken(tokenParam);
      setIsLoading(false);
      return;
    }

    // 检查 URL hash fragment (Supabase 格式)
    // Supabase 链接格式: #access_token=xxx&type=recovery&...
    if (typeof window !== 'undefined') {
      const hash = window.location.hash.substring(1); // 移除 #
      if (hash) {
        const params = new URLSearchParams(hash);
        const accessToken = params.get('access_token');
        const type = params.get('type');

        if (accessToken && type === 'recovery') {
          setToken(accessToken);
          setRefreshToken(params.get('refresh_token'));
          setTokenType('recovery');
        }
      }
    }
    setIsLoading(false);
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!token) {
      toast.error('无效的重置链接');
      return;
    }

    if (!formData.password || !formData.confirmPassword) {
      toast.error('请填写所有字段');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      toast.error('两次输入的密码不一致');
      return;
    }

    if (formData.password.length < 8) {
      toast.error('密码长度至少为8位');
      return;
    }

    setIsSubmitting(true);
    try {
      await resetPassword(token, formData.password, refreshToken);
      setIsSuccess(true);
      toast.success('密码重置成功');
    } catch (error) {
      const message = error instanceof Error ? error.message : '重置失败，请重试';
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // 加载中状态
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">正在验证链接...</p>
        </div>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-md">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <svg
                className="h-6 w-6 text-red-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h2 className="mt-6 text-2xl font-bold text-gray-900">无效的链接</h2>
            <p className="mt-2 text-sm text-gray-600">重置密码链接无效或已过期，请重新申请。</p>
            <div className="mt-6">
              <Link
                href="/forgot-password"
                className="text-blue-600 hover:text-blue-500 font-medium"
              >
                重新申请重置密码
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-md">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
              <svg
                className="h-6 w-6 text-green-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h2 className="mt-6 text-2xl font-bold text-gray-900">密码重置成功</h2>
            <p className="mt-2 text-sm text-gray-600">您的密码已成功重置，请使用新密码登录。</p>
            <div className="mt-6">
              <Link
                href="/login"
                className="inline-flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                前往登录
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-md">
        <div>
          <h2 className="text-center text-3xl font-bold text-gray-900">重置密码</h2>
          <p className="mt-2 text-center text-sm text-gray-600">请输入您的新密码</p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                新密码
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                required
                className="mt-1 border-gray-300 shadow-sm focus-visible:ring-blue-500 focus-visible:border-blue-500"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                disabled={isSubmitting}
                minLength={8}
                placeholder="至少8位"
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                确认新密码
              </label>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                className="mt-1 border-gray-300 shadow-sm focus-visible:ring-blue-500 focus-visible:border-blue-500"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                disabled={isSubmitting}
                minLength={8}
              />
            </div>
          </div>

          <div>
            <Button type="submit" disabled={isSubmitting} variant="primary" className="w-full">
              {isSubmitting ? '重置中...' : '重置密码'}
            </Button>
          </div>

          <div className="text-center text-sm">
            <Link href="/login" className="text-blue-600 hover:text-blue-500">
              返回登录
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
