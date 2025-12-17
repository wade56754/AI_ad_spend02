'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
  Mail,
  ArrowLeft,
  Send,
  AlertCircle,
  CheckCircle,
  Clock,
  Shield,
  HelpCircle,
  ArrowRight,
} from 'lucide-react';
import { toast } from 'sonner';

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [step, setStep] = useState(1); // 1: 输入邮箱, 2: 邮件已发送
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [countdown, setCountdown] = useState(60);
  const [availableEmail, setAvailableEmail] = useState<boolean | null>(null);

  useEffect(() => {
    // 检查是否已经登录
    const token = localStorage.getItem('token');
    if (token) {
      router.push('/');
    }
  }, [router]);

  // 邮箱检查
  useEffect(() => {
    if (email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      const checkEmailTimer = setTimeout(() => {
        checkEmailExistence();
      }, 500);

      return () => clearTimeout(checkEmailTimer);
    } else {
      setAvailableEmail(null);
    }
  }, [email]);

  // 倒计时
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const checkEmailExistence = async () => {
    try {
      const response = await fetch(`/api/v1/auth/check-email?email=${email}`);
      const result = await response.json();
      // 这里应该检查邮箱是否已注册（与注册页面相反）
      setAvailableEmail(!result.available); // 如果不可用说明已注册
    } catch (error) {
      console.error('检查邮箱失败:', error);
      setAvailableEmail(null);
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!email.trim()) {
      newErrors.email = '请输入邮箱地址';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = '请输入有效的邮箱地址';
    } else if (availableEmail === false) {
      newErrors.email = '该邮箱地址未注册';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const result = await response.json();

      if (result.success) {
        setStep(2);
        setCountdown(60);
        toast.success('重置密码邮件已发送');
      } else {
        setErrors({ submit: result.message || '发送失败，请检查邮箱地址' });
      }
    } catch (error) {
      console.error('发送重置邮件错误:', error);
      setErrors({ submit: '发送失败，请检查网络连接' });
    } finally {
      setLoading(false);
    }
  };

  const handleResendEmail = async () => {
    if (countdown > 0) return;

    setLoading(true);
    try {
      const response = await fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const result = await response.json();

      if (result.success) {
        toast.success('重置邮件已重新发送');
        setCountdown(60);
      } else {
        toast.error(result.message || '发送失败，请稍后重试');
      }
    } catch (error) {
      console.error('重发邮件错误:', error);
      toast.error('发送失败，请检查网络连接');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setEmail(value);

    // 清除错误
    if (errors.email) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.email;
        return newErrors;
      });
    }
  };

  const getEmailDomain = () => {
    if (!email) return '';
    const domain = email.split('@')[1];
    return domain || '';
  };

  const getEmailProviderUrl = () => {
    const domain = getEmailDomain();
    const providerUrls: Record<string, string> = {
      'gmail.com': 'https://mail.google.com',
      'qq.com': 'https://mail.qq.com',
      '163.com': 'https://mail.163.com',
      '126.com': 'https://mail.126.com',
      'sina.com': 'https://mail.sina.com.cn',
      'hotmail.com': 'https://outlook.live.com',
      'outlook.com': 'https://outlook.live.com',
      'yahoo.com': 'https://mail.yahoo.com',
    };

    return providerUrls[domain] || '#';
  };

  const getEmailProviderName = () => {
    const domain = getEmailDomain();
    const providerNames: Record<string, string> = {
      'gmail.com': 'Gmail',
      'qq.com': 'QQ邮箱',
      '163.com': '网易邮箱',
      '126.com': '126邮箱',
      'sina.com': '新浪邮箱',
      'hotmail.com': 'Outlook',
      'outlook.com': 'Outlook',
      'yahoo.com': 'Yahoo Mail',
    };

    return providerNames[domain] || '邮箱';
  };

  if (step === 2) {
    // 邮件已发送页面
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-6">
          {/* 成功图标和标题 */}
          <div className="text-center">
            <div className="mx-auto h-16 w-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <Send className="h-8 w-8 text-blue-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              邮件已发送
            </h1>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              我们已向您的邮箱发送了密码重置链接
            </p>
          </div>

          <Card>
            <CardHeader className="text-center">
              <CardTitle className="text-lg">检查您的邮箱</CardTitle>
              <CardDescription>
                请点击邮件中的链接以重置密码
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 邮箱信息 */}
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Mail className="h-5 w-5 text-blue-600" />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        重置邮件已发送至
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {email}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* 快速操作 */}
              <div className="space-y-3">
                {getEmailProviderUrl() !== '#' && (
                  <Link
                    href={getEmailProviderUrl()}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Button
                      variant="default"
                      className="w-full"
                    >
                      <ArrowRight className="mr-2 h-4 w-4" />
                      打开 {getEmailProviderName()}
                    </Button>
                  </Link>
                )}

                <Button
                  onClick={handleResendEmail}
                  variant="outline"
                  className="w-full"
                  disabled={countdown > 0 || loading}
                >
                  <Send className={`mr-2 h-4 w-4 ${loading ? 'animate-pulse' : ''}`} />
                  {loading
                    ? '发送中...'
                    : countdown > 0
                    ? `重新发送 (${countdown}s)`
                    : '重新发送邮件'
                  }
                </Button>

                <Button
                  onClick={() => setStep(1)}
                  variant="ghost"
                  className="w-full"
                >
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  使用其他邮箱地址
                </Button>
              </div>

              {/* 提示信息 */}
              <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
                <div className="flex items-start space-x-3">
                  <Clock className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                      请注意
                    </p>
                    <ul className="text-sm text-yellow-700 dark:text-yellow-300 mt-1 space-y-1">
                      <li>• 重置链接30分钟内有效</li>
                      <li>• 请检查垃圾邮件文件夹</li>
                      <li>• 如有问题请联系客服</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 其他操作 */}
          <div className="text-center space-y-3">
            <Link href="/auth/login">
              <Button variant="outline" className="w-full">
                <Shield className="mr-2 h-4 w-4" />
                想起密码？立即登录
              </Button>
            </Link>

            <Link href="/auth/sign-up">
              <Button variant="ghost" className="w-full">
                <HelpCircle className="mr-2 h-4 w-4" />
                还没有账户？立即注册
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-6">
        {/* 头部 */}
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            忘记密码
          </h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            输入您的邮箱地址，我们将发送重置链接
          </p>
        </div>

        {/* 返回登录 */}
        <div className="text-center">
          <Link
            href="/auth/login"
            className="inline-flex items-center text-sm text-blue-600 hover:text-blue-500"
          >
            <ArrowLeft className="mr-1 h-4 w-4" />
            返回登录
          </Link>
        </div>

        {/* 重置密码表单 */}
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-xl">重置密码</CardTitle>
            <CardDescription>
              请输入您注册时使用的邮箱地址
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 错误提示 */}
            {errors.submit && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{errors.submit}</AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="email">邮箱地址</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="请输入注册时使用的邮箱地址"
                    value={email}
                    onChange={handleInputChange}
                    className={`pl-10 pr-10 ${
                      availableEmail === false ? 'border-red-300' :
                      availableEmail === true ? 'border-green-300' : ''
                    }`}
                    disabled={loading}
                    aria-invalid={!!errors.email}
                  />
                  {email && (
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                      {availableEmail === false && <AlertCircle className="h-4 w-4 text-red-500" />}
                      {availableEmail === true && <CheckCircle className="h-4 w-4 text-green-500" />}
                    </div>
                  )}
                </div>
                {errors.email && (
                  <p className="text-sm text-red-600 mt-1">{errors.email}</p>
                )}
                {availableEmail === true && (
                  <p className="text-sm text-green-600 mt-1">找到该邮箱账户</p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={loading}
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    发送中...
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <Send className="mr-2 h-4 w-4" />
                    发送重置邮件
                  </div>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* 帮助信息 */}
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-start space-x-3">
              <HelpCircle className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h3 className="font-medium text-sm text-gray-900 dark:text-white">
                  需要帮助？
                </h3>
                <ul className="text-xs text-gray-600 dark:text-gray-400 mt-2 space-y-1">
                  <li>• 确保输入正确的邮箱地址</li>
                  <li>• 检查邮箱是否已注册</li>
                  <li>• 查看垃圾邮件文件夹</li>
                  <li>• 重置链接30分钟内有效</li>
                </ul>
              </div>
            </div>
          </Card>

          {/* 其他选项 */}
          <div className="text-center space-y-2">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              还没有账户？
              <Link
                href="/auth/sign-up"
                className="font-medium text-blue-600 hover:text-blue-500 ml-1"
              >
                立即注册
              </Link>
            </div>
          </div>
        </div>

        {/* 底部信息 */}
        <div className="text-center text-xs text-gray-500 dark:text-gray-400">
          <p>© 2024 AI广告代投系统. All rights reserved.</p>
          <div className="mt-2 flex justify-center gap-4">
            <Link href="/privacy" className="hover:text-gray-700 dark:hover:text-gray-300">
              隐私政策
            </Link>
            <Link href="/terms" className="hover:text-gray-700 dark:hover:text-gray-300">
              服务条款
            </Link>
            <Link href="/help" className="hover:text-gray-700 dark:hover:text-gray-300">
              帮助中心
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}