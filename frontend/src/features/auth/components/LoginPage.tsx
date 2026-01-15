'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';

export function LoginPage() {
  const { login, isLoggingIn } = useAuth();
  const [formData, setFormData] = useState({
    identifier: '',
    password: '',
    remember_me: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.identifier || !formData.password) {
      toast.error('请输入用户名/邮箱和密码');
      return;
    }

    try {
      await login(formData);
    } catch (error) {
      const message = error instanceof Error ? error.message : '登录失败，请重试';
      toast.error(message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-md">
        <div>
          <h2 className="text-center text-3xl font-bold text-gray-900">AI 广告代投系统</h2>
          <p className="mt-2 text-center text-sm text-gray-600">请登录您的账户</p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="identifier" className="block text-sm font-medium text-gray-700">
                用户名或邮箱
              </label>
              <Input
                id="identifier"
                name="identifier"
                type="text"
                required
                data-testid="email-input"
                className="mt-1 border-gray-300 shadow-sm focus-visible:ring-blue-500 focus-visible:border-blue-500"
                value={formData.identifier}
                onChange={(e) => setFormData({ ...formData, identifier: e.target.value })}
                disabled={isLoggingIn}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                密码
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                required
                data-testid="password-input"
                className="mt-1 border-gray-300 shadow-sm focus-visible:ring-blue-500 focus-visible:border-blue-500"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                disabled={isLoggingIn}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Checkbox
                  id="remember_me"
                  checked={formData.remember_me}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, remember_me: checked === true })
                  }
                  disabled={isLoggingIn}
                />
                <label htmlFor="remember_me" className="ml-2 block text-sm text-gray-900">
                  记住我
                </label>
              </div>
              <Link href="/forgot-password" className="text-sm text-blue-600 hover:text-blue-500">
                忘记密码？
              </Link>
            </div>
          </div>

          <div>
            <Button
              type="submit"
              disabled={isLoggingIn}
              data-testid="login-button"
              variant="primary"
              className="w-full"
            >
              {isLoggingIn ? '登录中...' : '登录'}
            </Button>
          </div>

          <div className="text-center text-sm">
            <span className="text-gray-600">还没有账户？</span>
            <Link href="/register" className="ml-1 font-medium text-blue-600 hover:text-blue-500">
              立即注册
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
