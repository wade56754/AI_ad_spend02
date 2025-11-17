'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Mail,
  CheckCircle,
  ArrowRight,
  Shield,
  RefreshCw,
  ExternalLink,
  Clock,
  Zap,
  BarChart3,
  Users,
} from 'lucide-react';
import { toast } from 'sonner';

export default function SignUpSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState('');
  const [resending, setResending] = useState(false);
  const [countdown, setCountdown] = useState(60);

  useEffect(() => {
    const emailParam = searchParams.get('email');
    if (emailParam) {
      setEmail(emailParam);
    } else {
      // 如果没有邮箱参数，重定向到注册页面
      router.push('/auth/sign-up');
    }
  }, [searchParams, router]);

  // 倒计时
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleResendEmail = async () => {
    if (countdown > 0 || !email) return;

    setResending(true);
    try {
      const response = await fetch('/api/v1/auth/resend-verification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const result = await response.json();

      if (result.success) {
        toast.success('验证邮件已重新发送');
        setCountdown(60); // 重新开始倒计时
      } else {
        toast.error(result.message || '发送失败，请稍后重试');
      }
    } catch (error) {
      console.error('重发邮件错误:', error);
      toast.error('发送失败，请检查网络连接');
    } finally {
      setResending(false);
    }
  };

  const handleOpenEmail = () => {
    // 打开默认邮箱客户端
    window.location.href = `mailto:${email}`;
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-6">
        {/* 成功图标和标题 */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            注册成功！
          </h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            我们已向您的邮箱发送了验证邮件
          </p>
        </div>

        {/* 验证邮件卡片 */}
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-lg">验证您的邮箱</CardTitle>
            <CardDescription>
              请点击邮件中的验证链接以激活您的账户
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
                      验证邮件已发送至
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
              {/* 打开邮箱 */}
              <Button
                onClick={handleOpenEmail}
                className="w-full"
                variant="default"
              >
                <ExternalLink className="mr-2 h-4 w-4" />
                打开 {getEmailProviderName()}
              </Button>

              {/* 常用邮箱链接 */}
              {getEmailProviderUrl() !== '#' && (
                <Link
                  href={getEmailProviderUrl()}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button
                    variant="outline"
                    className="w-full"
                  >
                    <ExternalLink className="mr-2 h-4 w-4" />
                    访问 {getEmailProviderName()} 网页版
                  </Button>
                </Link>
              )}

              {/* 重新发送邮件 */}
              <Button
                onClick={handleResendEmail}
                variant="ghost"
                className="w-full"
                disabled={countdown > 0 || resending}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${resending ? 'animate-spin' : ''}`} />
                {resending
                  ? '发送中...'
                  : countdown > 0
                  ? `重新发送 (${countdown}s)`
                  : '重新发送验证邮件'
                }
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
                    <li>• 验证邮件可能需要几分钟才能到达</li>
                    <li>• 请检查垃圾邮件文件夹</li>
                    <li>• 验证链接24小时内有效</li>
                  </ul>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 功能预览 */}
        <div className="space-y-4">
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              验证后即可使用
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              完整的AI广告代投管理功能
            </p>
          </div>

          <div className="grid grid-cols-1 gap-3">
            <div className="flex items-center space-x-3 p-3 bg-white dark:bg-gray-800 rounded-lg border">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Zap className="h-4 w-4 text-blue-600" />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-medium">智能分析</h4>
                <p className="text-xs text-gray-500">AI驱动的账户性能分析</p>
              </div>
              <Badge variant="secondary">AI</Badge>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-white dark:bg-gray-800 rounded-lg border">
              <div className="p-2 bg-green-100 rounded-lg">
                <BarChart3 className="h-4 w-4 text-green-600" />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-medium">数据报表</h4>
                <p className="text-xs text-gray-500">实时监控和趋势分析</p>
              </div>
              <Badge variant="secondary">实时</Badge>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-white dark:bg-gray-800 rounded-lg border">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Users className="h-4 w-4 text-purple-600" />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-medium">团队协作</h4>
                <p className="text-xs text-gray-500">多角色权限管理</p>
              </div>
              <Badge variant="secondary">企业版</Badge>
            </div>
          </div>
        </div>

        {/* 其他操作 */}
        <div className="text-center space-y-3">
          <Link href="/auth/login">
            <Button variant="outline" className="w-full">
              <Shield className="mr-2 h-4 w-4" />
              已验证？立即登录
            </Button>
          </Link>

          <div className="text-sm text-gray-600 dark:text-gray-400">
            <p>
              没有收到邮件？
              <button
                onClick={handleResendEmail}
                className="text-blue-600 hover:text-blue-500 ml-1"
                disabled={countdown > 0 || resending}
              >
                {countdown > 0 ? `请等待 ${countdown} 秒` : '重新发送'}
              </button>
            </p>
            <p className="mt-1">
              邮箱地址错误？
              <Link href="/auth/sign-up" className="text-blue-600 hover:text-blue-500 ml-1">
                重新注册
              </Link>
            </p>
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