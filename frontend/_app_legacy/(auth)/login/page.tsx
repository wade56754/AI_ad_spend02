'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import {
  Eye,
  EyeOff,
  LogIn,
  Mail,
  Lock,
  AlertCircle,
  CheckCircle,
  ArrowRight,
  Shield,
  Zap,
} from 'lucide-react';
import { toast } from 'sonner';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    remember: false,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const redirectUrl = searchParams.get('redirect') || '/';

  // 检查是否已经登录
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      router.push(redirectUrl);
    }
  }, [router, redirectUrl]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email.trim()) {
      newErrors.email = '请输入邮箱地址';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = '请输入有效的邮箱地址';
    }

    if (!formData.password.trim()) {
      newErrors.password = '请输入密码';
    } else if (formData.password.length < 6) {
      newErrors.password = '密码长度至少6位';
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
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (result.success) {
        // 保存token和用户信息
        localStorage.setItem('token', result.data.token);
        localStorage.setItem('user', JSON.stringify(result.data.user));

        toast.success('登录成功');
        router.push(redirectUrl);
      } else {
        setErrors({ submit: result.message || '登录失败，请检查用户名和密码' });
      }
    } catch (error) {
      console.error('登录错误:', error);
      setErrors({ submit: '登录失败，请检查网络连接' });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // 清除对应字段的错误
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleSSOLogin = async (provider: string) => {
    setLoading(true);
    try {
      // 模拟SSO登录
      toast.info(`正在跳转到 ${provider} 登录...`);

      // 实际应该跳转到对应的OAuth提供商
      if (provider === 'google') {
        window.location.href = 'https://accounts.google.com/oauth/authorize?...';
      } else if (provider === 'github') {
        window.location.href = 'https://github.com/login/oauth/authorize?...';
      }
    } catch (error) {
      console.error('SSO登录错误:', error);
      toast.error('SSO登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-6">
        {/* 头部Logo和标题 */}
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            AI广告代投系统
          </h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            智能化广告投放管理平台
          </p>
        </div>

        {/* 登录卡片 */}
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-xl">欢迎回来</CardTitle>
            <CardDescription>
              请登录您的账户以继续使用系统
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

            {/* 成功提示 */}
            {searchParams.get('registered') && (
              <Alert className="border-green-200 bg-green-50 text-green-800">
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  注册成功！请登录您的账户。
                </AlertDescription>
              </Alert>
            )}

            {/* 登录表单 */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="email">邮箱地址</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="请输入邮箱地址"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="pl-10"
                    disabled={loading}
                    aria-invalid={!!errors.email}
                  />
                </div>
                {errors.email && (
                  <p className="text-sm text-red-600 mt-1">{errors.email}</p>
                )}
              </div>

              <div>
                <Label htmlFor="password">密码</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="请输入密码"
                    value={formData.password}
                    onChange={handleInputChange}
                    className="pl-10 pr-10"
                    disabled={loading}
                    aria-invalid={!!errors.password}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={loading}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                {errors.password && (
                  <p className="text-sm text-red-600 mt-1">{errors.password}</p>
                )}
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="remember"
                    checked={formData.remember}
                    onCheckedChange={(checked) => setFormData(prev => ({ ...prev, remember: checked }))}
                    disabled={loading}
                  />
                  <Label htmlFor="remember" className="text-sm text-gray-600 dark:text-gray-400">
                    记住我
                  </Label>
                </div>
                <Link
                  href="/auth/forgot-password"
                  className="text-sm text-blue-600 hover:text-blue-500"
                >
                  忘记密码？
                </Link>
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={loading}
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    登录中...
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <LogIn className="mr-2 h-4 w-4" />
                    登录
                  </div>
                )}
              </Button>

              {/* 分隔线 */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300 dark:border-gray-600" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white dark:bg-gray-900 text-gray-500">
                    或
                  </span>
                </div>
              </div>

              {/* 第三方登录 */}
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => handleSSOLogin('google')}
                    disabled={loading}
                    className="w-full"
                  >
                    <div className="flex items-center justify-center">
                      <div className="w-5 h-5 bg-red-500 rounded-full mr-2"></div>
                      Google
                    </div>
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => handleSSOLogin('github')}
                    disabled={loading}
                    className="w-full"
                  >
                    <div className="flex items-center justify-center">
                      <div className="w-5 h-5 bg-gray-800 rounded-full mr-2"></div>
                      GitHub
                    </div>
                  </Button>
                </div>
              </div>
            </form>
          </CardContent>

          <div className="p-6 text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              还没有账户？
              <Link
                href="/auth/sign-up"
                className="ml-1 font-medium text-blue-600 hover:text-blue-500"
              >
                立即注册
              </Link>
            </p>
          </div>
        </Card>

        {/* 功能特性卡片 */}
        <div className="grid grid-cols-1 gap-4">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Zap className="h-5 w-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-sm">智能分析</h3>
                <p className="text-xs text-gray-600">AI驱动的账户性能分析和优化建议</p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-green-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-sm">实时监控</h3>
                <p className="text-xs text-gray-600">24/7账户状态监控和异常预警</p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Shield className="h-5 w-5 text-purple-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-sm">安全可靠</h3>
                <p className="text-xs text-gray-600">企业级安全保障和数据隔离</p>
              </div>
            </div>
          </Card>
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