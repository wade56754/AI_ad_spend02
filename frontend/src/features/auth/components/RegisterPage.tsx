'use client';

import { useState } from 'react';
import Link from 'next/link';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '../hooks';
import type { RegisterRequest } from '../types';

interface RegisterFormData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  full_name: string;
}

export function RegisterPage() {
  const { register, isRegistering } = useAuth();
  const [formData, setFormData] = useState<RegisterFormData>({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.username || !formData.email || !formData.password) {
      toast.error('请填写所有必填字段');
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

    try {
      const registerData: RegisterRequest = {
        email: formData.email,
        password: formData.password,
        username: formData.username,
        full_name: formData.full_name || undefined,
      };

      await register(registerData);
      toast.success('注册成功');
      // useAuth hook 会自动跳转到 dashboard
    } catch (error) {
      const message = error instanceof Error ? error.message : '注册失败，请重试';
      toast.error(message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-md">
        <div>
          <h2 className="text-center text-3xl font-bold text-gray-900">AI 广告代投系统</h2>
          <p className="mt-2 text-center text-sm text-gray-600">创建新账户</p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                用户名
              </label>
              <Input
                id="username"
                name="username"
                type="text"
                required
                className="mt-1 border-gray-300 shadow-sm focus-visible:ring-blue-500 focus-visible:border-blue-500"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                disabled={isRegistering}
              />
            </div>

            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
                全名 <span className="text-gray-400">(可选)</span>
              </label>
              <Input
                id="full_name"
                name="full_name"
                type="text"
                className="mt-1 border-gray-300 shadow-sm focus-visible:ring-blue-500 focus-visible:border-blue-500"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                disabled={isRegistering}
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                邮箱
              </label>
              <Input
                id="email"
                name="email"
                type="email"
                required
                className="mt-1 border-gray-300 shadow-sm focus-visible:ring-blue-500 focus-visible:border-blue-500"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                disabled={isRegistering}
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
                className="mt-1 border-gray-300 shadow-sm focus-visible:ring-blue-500 focus-visible:border-blue-500"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                disabled={isRegistering}
                minLength={8}
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                确认密码
              </label>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                className="mt-1 border-gray-300 shadow-sm focus-visible:ring-blue-500 focus-visible:border-blue-500"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                disabled={isRegistering}
                minLength={8}
              />
            </div>
          </div>

          <div>
            <Button type="submit" disabled={isRegistering} variant="primary" className="w-full">
              {isRegistering ? '注册中...' : '注册'}
            </Button>
          </div>

          <div className="text-center text-sm">
            <span className="text-gray-600">已有账户？</span>{' '}
            <Link href="/login" className="text-blue-600 hover:text-blue-500">
              立即登录
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
