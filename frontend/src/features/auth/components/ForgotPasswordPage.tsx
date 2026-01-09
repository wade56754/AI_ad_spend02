'use client';

import { useState } from 'react';
import Link from 'next/link';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { forgotPassword } from '../services/authApi';

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email) {
      toast.error('请输入邮箱地址');
      return;
    }

    setIsSubmitting(true);
    try {
      await forgotPassword(email);
      setIsSubmitted(true);
      toast.success('重置密码邮件已发送');
    } catch (error) {
      const message = error instanceof Error ? error.message : '发送失败，请重试';
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-md">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
              <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="mt-6 text-2xl font-bold text-gray-900">
              邮件已发送
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              请检查您的邮箱 <span className="font-medium">{email}</span>，点击邮件中的链接重置密码。
            </p>
            <p className="mt-4 text-sm text-gray-500">
              没有收到邮件？请检查垃圾邮件文件夹，或
              <Button
                variant="link"
                onClick={() => setIsSubmitted(false)}
                className="text-blue-600 hover:text-blue-500 ml-1 p-0 h-auto"
              >
                重新发送
              </Button>
            </p>
            <div className="mt-6">
              <Link
                href="/login"
                className="text-blue-600 hover:text-blue-500 font-medium"
              >
                返回登录
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
          <h2 className="text-center text-3xl font-bold text-gray-900">
            忘记密码
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            输入您的邮箱地址，我们将发送重置密码链接
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div>
            <Label htmlFor="email" className="block text-sm font-medium text-gray-700">
              邮箱地址
            </Label>
            <Input
              id="email"
              name="email"
              type="email"
              required
              className="mt-1"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isSubmitting}
              placeholder="your@email.com"
            />
          </div>

          <div>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-full"
            >
              {isSubmitting ? '发送中...' : '发送重置链接'}
            </Button>
          </div>

          <div className="text-center text-sm">
            <Link
              href="/login"
              className="text-blue-600 hover:text-blue-500"
            >
              返回登录
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}







