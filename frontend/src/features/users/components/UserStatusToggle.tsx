/**
 * UserStatusToggle - 用户状态切换组件
 *
 * TASK-FE-USER-005: 用户停用/启用操作
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
 * - MASTER.md v4.9 §2.4 (ceo, admin 可操作)
 *
 * 功能:
 * - 仅 ceo 和 admin 可操作
 * - 停用用户需确认弹窗
 * - 停用后用户无法登录
 */

'use client';

import { useState } from 'react';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Power, PowerOff, AlertTriangle, Loader2, ShieldAlert } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { usePermission } from '@/hooks/usePermission';

// === 类型定义 ===

export interface UserStatusToggleProps {
  /** 用户 ID */
  userId: string;
  /** 用户名（用于确认弹窗） */
  userName: string;
  /** 当前是否激活 */
  isActive: boolean;
  /** 状态变更回调 */
  onToggle: (userId: string, isActive: boolean) => Promise<void>;
  /** 显示模式 */
  variant?: 'switch' | 'button' | 'badge';
  /** 是否显示标签 */
  showLabel?: boolean;
  /** 自定义类名 */
  className?: string;
}

// === 主组件 ===

export function UserStatusToggle({
  userId,
  userName,
  isActive,
  onToggle,
  variant = 'switch',
  showLabel = true,
  className,
}: UserStatusToggleProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingStatus, setPendingStatus] = useState<boolean | null>(null);
  const [isPending, setIsPending] = useState(false);

  // 权限检查 - SoT: MASTER.md v4.9 §2.4
  const { businessRole, isCeo } = usePermission();
  const canToggle = isCeo || businessRole === 'admin';

  // 处理切换请求
  const handleToggleRequest = (newStatus: boolean) => {
    if (!canToggle) {
      toast.error('您没有权限修改用户状态');
      return;
    }

    // 启用不需要确认，停用需要确认
    if (newStatus) {
      handleToggle(newStatus);
    } else {
      setPendingStatus(newStatus);
      setShowConfirm(true);
    }
  };

  // 执行切换
  const handleToggle = async (newStatus: boolean) => {
    setIsPending(true);
    try {
      await onToggle(userId, newStatus);
      toast.success(newStatus ? `用户「${userName}」已启用` : `用户「${userName}」已停用`);
    } catch (error) {
      toast.error(`操作失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setIsPending(false);
      setShowConfirm(false);
      setPendingStatus(null);
    }
  };

  // 确认停用
  const handleConfirm = () => {
    if (pendingStatus !== null) {
      handleToggle(pendingStatus);
    }
  };

  // 取消操作
  const handleCancel = () => {
    setShowConfirm(false);
    setPendingStatus(null);
  };

  // Switch 模式
  const renderSwitch = () => (
    <div className={cn('flex items-center gap-2', className)}>
      <Switch
        checked={isActive}
        onCheckedChange={handleToggleRequest}
        disabled={!canToggle || isPending}
      />
      {showLabel && (
        <span className={cn('text-sm', isActive ? 'text-green-600' : 'text-gray-500')}>
          {isActive ? '已启用' : '已停用'}
        </span>
      )}
    </div>
  );

  // Button 模式
  const renderButton = () => (
    <Button
      variant={isActive ? 'outline' : 'default'}
      size="sm"
      onClick={() => handleToggleRequest(!isActive)}
      disabled={!canToggle || isPending}
      className={className}
    >
      {isPending ? (
        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
      ) : isActive ? (
        <PowerOff className="h-4 w-4 mr-2" />
      ) : (
        <Power className="h-4 w-4 mr-2" />
      )}
      {isActive ? '停用' : '启用'}
    </Button>
  );

  // Badge 模式
  const renderBadge = () => (
    <Badge
      variant={isActive ? 'default' : 'secondary'}
      className={cn(
        'cursor-pointer transition-colors',
        !canToggle && 'cursor-not-allowed opacity-60',
        isActive && 'bg-green-500 hover:bg-green-600',
        !isActive && 'bg-gray-400 hover:bg-gray-500',
        className
      )}
      onClick={() => canToggle && handleToggleRequest(!isActive)}
    >
      {isPending ? (
        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
      ) : isActive ? (
        <Power className="h-3 w-3 mr-1" />
      ) : (
        <PowerOff className="h-3 w-3 mr-1" />
      )}
      {isActive ? '已启用' : '已停用'}
    </Badge>
  );

  // 根据 variant 渲染
  const renderToggle = () => {
    switch (variant) {
      case 'button':
        return renderButton();
      case 'badge':
        return renderBadge();
      default:
        return renderSwitch();
    }
  };

  return (
    <>
      {renderToggle()}

      {/* 停用确认弹窗 */}
      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              确认停用用户
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-4">
                <p>
                  您确定要停用用户「<strong>{userName}</strong>」吗？
                </p>

                <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
                  <div className="flex items-start gap-3">
                    <ShieldAlert className="h-5 w-5 text-amber-500 mt-0.5 flex-shrink-0" />
                    <div className="text-sm space-y-2">
                      <p className="font-medium text-amber-800">停用后：</p>
                      <ul className="space-y-1 text-amber-700">
                        <li>- 该用户将无法登录系统</li>
                        <li>- 该用户的所有会话将立即失效</li>
                        <li>- 该用户负责的账户/项目不会受影响</li>
                        <li>- 可以随时重新启用该用户</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancel} disabled={isPending}>
              取消
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirm}
              disabled={isPending}
              className="bg-amber-600 hover:bg-amber-700"
            >
              {isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <PowerOff className="h-4 w-4 mr-2" />
              )}
              确认停用
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

export default UserStatusToggle;
