/**
 * SettingsGuard - 系统设置权限守卫组件
 *
 * TASK-FE-SET-001: 仅 admin 可访问系统设置
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
 * - MASTER.md v4.9 §2.4 (admin 角色定义)
 *
 * 功能:
 * - 检查用户是否有 admin 角色
 * - 无权限时显示拒绝访问提示或重定向
 */

'use client';

import { ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle, ArrowLeft, Settings, Loader2 } from 'lucide-react';
import { usePermission } from '@/hooks/usePermission';

// === 类型定义 ===

export interface SettingsGuardProps {
  /** 子组件 */
  children: ReactNode;
  /** 无权限时是否重定向 */
  redirect?: boolean;
  /** 重定向目标 */
  redirectTo?: string;
  /** 自定义无权限消息 */
  accessDeniedMessage?: string;
  /** 是否允许 CEO 访问（默认 true） */
  allowCeo?: boolean;
}

// === 无权限提示组件 ===

function AccessDenied({
  message = '您没有权限访问系统设置页面。此页面仅对系统管理员开放。',
  onBack,
}: {
  message?: string;
  onBack: () => void;
}) {
  return (
    <div className="flex items-center justify-center min-h-[60vh] p-6">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 h-16 w-16 rounded-full bg-amber-100 flex items-center justify-center">
            <AlertTriangle className="h-8 w-8 text-amber-600" />
          </div>
          <CardTitle className="text-xl">访问受限</CardTitle>
          <CardDescription className="text-base">{message}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="p-4 bg-muted rounded-lg">
            <div className="flex items-center gap-3">
              <Settings className="h-5 w-5 text-muted-foreground flex-shrink-0" />
              <div className="text-sm">
                <p className="font-medium">系统设置权限说明</p>
                <p className="text-muted-foreground">
                  系统设置包含全局配置项，仅限系统管理员操作。如需更改配置，请联系管理员。
                </p>
              </div>
            </div>
          </div>
          <Button onClick={onBack} variant="outline" className="w-full">
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回上一页
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

// === 加载状态组件 ===

function LoadingState() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <p className="text-muted-foreground">正在验证访问权限...</p>
      </div>
    </div>
  );
}

// === 主组件 ===

export function SettingsGuard({
  children,
  redirect = false,
  redirectTo = '/dashboard',
  accessDeniedMessage,
  allowCeo = true,
}: SettingsGuardProps) {
  const router = useRouter();
  const { businessRole, isCeo, isLoading } = usePermission();

  // 加载中
  if (isLoading) {
    return <LoadingState />;
  }

  // 权限检查 - SoT: MASTER.md v4.9 §2.4
  // admin 始终允许，CEO 根据 allowCeo 参数决定
  const isAdmin = businessRole === 'admin';
  const hasAccess = isAdmin || (allowCeo && isCeo);

  // 无权限处理
  if (!hasAccess) {
    if (redirect) {
      router.replace(redirectTo);
      return <LoadingState />;
    }
    return (
      <AccessDenied
        message={accessDeniedMessage}
        onBack={() => router.back()}
      />
    );
  }

  // 有权限，渲染子组件
  return <>{children}</>;
}

export default SettingsGuard;
