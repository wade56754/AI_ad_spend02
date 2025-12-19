'use client';

import { AppLayout } from '@/components/dashboard/AppLayout';
import { useRequireAuth } from '@/features/auth/hooks/useAuth';

/**
 * Dashboard 页面布局
 * 包含侧边栏和顶部导航
 *
 * 路由保护: 未登录用户将被重定向到 /login
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isLoading, isAuthenticated } = useRequireAuth();

  // 显示加载状态
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  // 未认证时不渲染内容 (useRequireAuth 会处理重定向)
  if (!isAuthenticated) {
    return null;
  }

  return <AppLayout>{children}</AppLayout>;
}
