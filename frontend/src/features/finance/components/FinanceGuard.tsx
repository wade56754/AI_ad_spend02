/**
 * FinanceGuard - 财务权限守卫组件
 *
 * TASK-FE-FIN-005: 财务权限守卫
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §6.5.2 (访问控制)
 * - MASTER.md v4.9 §2.4 (ceo, finance, admin 可访问财务模块)
 *
 * 功能:
 * - 封装财务模块权限检查
 * - 无权限显示 AccessDenied 组件
 * - 支持重定向到首页
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ShieldX, Home, ArrowLeft } from 'lucide-react';
import { usePermission } from '@/hooks/usePermission';
import type { BusinessRole } from '@/types/roles';

// === 类型定义 ===

export interface FinanceGuardProps {
  /** 子组件 */
  children: React.ReactNode;
  /** 是否自动重定向（默认 false，显示 AccessDenied） */
  redirect?: boolean;
  /** 重定向目标路径（默认 /dashboard） */
  redirectTo?: string;
  /** 允许访问的角色（默认 ceo, finance, admin） */
  allowedRoles?: BusinessRole[];
  /** 无权限时的回调 */
  onAccessDenied?: () => void;
}

// === 子组件 ===

interface AccessDeniedProps {
  redirectTo?: string;
}

function AccessDenied({ redirectTo = '/dashboard' }: AccessDeniedProps) {
  const router = useRouter();

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
              <ShieldX className="h-8 w-8 text-red-600" />
            </div>
          </div>
          <CardTitle className="text-xl">访问受限</CardTitle>
          <CardDescription>
            您没有权限访问财务模块。如需访问，请联系管理员。
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Button onClick={() => router.push(redirectTo)} className="w-full">
            <Home className="h-4 w-4 mr-2" />
            返回首页
          </Button>
          <Button variant="outline" onClick={() => router.back()} className="w-full">
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回上一页
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

// === 主组件 ===

/**
 * 财务模块权限守卫
 *
 * @example
 * ```tsx
 * // 基本用法 - 显示 AccessDenied
 * <FinanceGuard>
 *   <FinancePage />
 * </FinanceGuard>
 *
 * // 自动重定向
 * <FinanceGuard redirect redirectTo="/dashboard">
 *   <LedgerPage />
 * </FinanceGuard>
 *
 * // 自定义允许角色
 * <FinanceGuard allowedRoles={['ceo', 'finance']}>
 *   <ProfitPage />
 * </FinanceGuard>
 * ```
 */
export function FinanceGuard({
  children,
  redirect = false,
  redirectTo = '/dashboard',
  allowedRoles = ['ceo', 'finance', 'admin'],
  onAccessDenied,
}: FinanceGuardProps) {
  const router = useRouter();
  const { businessRole, isLoading } = usePermission();

  // 权限检查
  const hasAccess = businessRole && allowedRoles.includes(businessRole);

  // 处理重定向
  useEffect(() => {
    if (!isLoading && !hasAccess) {
      onAccessDenied?.();
      if (redirect) {
        router.replace(redirectTo);
      }
    }
  }, [isLoading, hasAccess, redirect, redirectTo, router, onAccessDenied]);

  // 加载中
  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <div className="h-12 w-12 rounded-full bg-gray-200" />
          <div className="h-4 w-32 rounded bg-gray-200" />
        </div>
      </div>
    );
  }

  // 无权限
  if (!hasAccess) {
    if (redirect) {
      return null; // 重定向中
    }
    return <AccessDenied redirectTo={redirectTo} />;
  }

  // 有权限
  return <>{children}</>;
}

// === 辅助 Hook ===

/**
 * 检查是否有财务模块访问权限
 */
export function useFinanceAccess(allowedRoles: BusinessRole[] = ['ceo', 'finance', 'admin']) {
  const { businessRole, isLoading } = usePermission();
  const hasAccess = !isLoading && businessRole && allowedRoles.includes(businessRole);

  return {
    hasAccess,
    isLoading,
    businessRole,
  };
}

export default FinanceGuard;
