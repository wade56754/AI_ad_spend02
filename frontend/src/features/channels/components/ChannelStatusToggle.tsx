/**
 * ChannelStatusToggle - 渠道状态切换组件
 *
 * TASK-FE-CHAN-004: 渠道状态切换
 *
 * SoT 引用:
 * - MASTER.md v4.9 §2.4 (权限: account_manager, admin)
 * - FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
 *
 * 功能:
 * - 支持启用/禁用状态切换
 * - 仅 account_manager 和 admin 可操作
 * - 状态变更需确认弹窗
 */

'use client';

import { useState } from 'react';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
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
import { Badge } from '@/components/ui/badge';
import { Power, PowerOff, Loader2, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import { usePermission } from '@/hooks/usePermission';
import { useActivateChannel, useDeactivateChannel } from '../hooks';
import type { Channel } from '../types';

// === Types ===

export interface ChannelStatusToggleProps {
  /** 渠道数据 */
  channel: Channel;
  /** 切换成功回调 */
  onSuccess?: () => void;
  /** 显示模式: switch | button | badge */
  variant?: 'switch' | 'button' | 'badge';
  /** 是否显示标签 */
  showLabel?: boolean;
  /** 自定义类名 */
  className?: string;
}

// === Main Component ===

export function ChannelStatusToggle({
  channel,
  onSuccess,
  variant = 'switch',
  showLabel = true,
  className,
}: ChannelStatusToggleProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingStatus, setPendingStatus] = useState<boolean | null>(null);

  // 权限检查 - SoT: MASTER.md v4.9 §2.4
  const { businessRole } = usePermission();
  const canToggle = businessRole === 'account_manager' || businessRole === 'admin';

  // Mutations
  const activateMutation = useActivateChannel({
    onSuccess: () => {
      toast.success(`渠道「${channel.name}」已启用`);
      onSuccess?.();
      setShowConfirm(false);
      setPendingStatus(null);
    },
    onError: (error) => {
      toast.error(`启用失败: ${error.message}`);
      setPendingStatus(null);
    },
  });

  const deactivateMutation = useDeactivateChannel({
    onSuccess: () => {
      toast.success(`渠道「${channel.name}」已停用`);
      onSuccess?.();
      setShowConfirm(false);
      setPendingStatus(null);
    },
    onError: (error) => {
      toast.error(`停用失败: ${error.message}`);
      setPendingStatus(null);
    },
  });

  const isPending = activateMutation.isPending || deactivateMutation.isPending;

  // 处理状态切换请求
  const handleToggleRequest = (newStatus: boolean) => {
    if (!canToggle) {
      toast.error('您没有权限修改渠道状态');
      return;
    }

    setPendingStatus(newStatus);
    setShowConfirm(true);
  };

  // 确认切换
  const handleConfirm = () => {
    if (pendingStatus === null) return;

    if (pendingStatus) {
      activateMutation.mutate(channel.id);
    } else {
      deactivateMutation.mutate(channel.id);
    }
  };

  // 取消切换
  const handleCancel = () => {
    setShowConfirm(false);
    setPendingStatus(null);
  };

  // 渲染 Switch 模式
  const renderSwitch = () => (
    <div className={`flex items-center gap-2 ${className || ''}`}>
      <Switch
        checked={channel.is_active}
        onCheckedChange={handleToggleRequest}
        disabled={!canToggle || isPending}
      />
      {showLabel && (
        <span className="text-sm text-muted-foreground">
          {channel.is_active ? '已启用' : '已停用'}
        </span>
      )}
    </div>
  );

  // 渲染 Button 模式
  const renderButton = () => (
    <Button
      variant={channel.is_active ? 'outline' : 'default'}
      size="sm"
      onClick={() => handleToggleRequest(!channel.is_active)}
      disabled={!canToggle || isPending}
      className={className}
    >
      {isPending ? (
        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
      ) : channel.is_active ? (
        <PowerOff className="h-4 w-4 mr-2" />
      ) : (
        <Power className="h-4 w-4 mr-2" />
      )}
      {channel.is_active ? '停用' : '启用'}
    </Button>
  );

  // 渲染 Badge 模式 (只显示状态，点击触发切换)
  const renderBadge = () => (
    <Badge
      variant={channel.is_active ? 'default' : 'secondary'}
      className={`cursor-pointer ${!canToggle ? 'cursor-not-allowed opacity-60' : ''} ${className || ''}`}
      onClick={() => canToggle && handleToggleRequest(!channel.is_active)}
    >
      {isPending ? (
        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
      ) : channel.is_active ? (
        <Power className="h-3 w-3 mr-1" />
      ) : (
        <PowerOff className="h-3 w-3 mr-1" />
      )}
      {channel.is_active ? '启用' : '停用'}
    </Badge>
  );

  // 根据 variant 渲染对应组件
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

      {/* 确认弹窗 */}
      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              确认{pendingStatus ? '启用' : '停用'}渠道
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-2">
                <p>
                  您确定要{pendingStatus ? '启用' : '停用'}渠道「{channel.name}」吗？
                </p>
                {!pendingStatus && (
                  <p className="text-amber-600">
                    停用后，该渠道下的广告账户将无法继续使用此渠道进行投放。
                  </p>
                )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>

          <div className="py-4">
            <div className="rounded-lg border bg-muted/50 p-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">渠道名称</span>
                <span className="font-medium">{channel.name}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">服务费类型</span>
                <span className="font-medium">
                  {channel.service_fee_type === 'percent' ? '百分比' : '固定金额'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">服务费</span>
                <span className="font-medium">
                  {channel.service_fee_type === 'percent'
                    ? `${channel.service_fee_value}%`
                    : `¥${channel.service_fee_value}`}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">当前状态</span>
                <Badge variant={channel.is_active ? 'default' : 'secondary'}>
                  {channel.is_active ? '启用' : '停用'}
                </Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">目标状态</span>
                <Badge variant={pendingStatus ? 'default' : 'secondary'}>
                  {pendingStatus ? '启用' : '停用'}
                </Badge>
              </div>
            </div>
          </div>

          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancel} disabled={isPending}>
              取消
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirm}
              disabled={isPending}
              className={pendingStatus ? '' : 'bg-amber-600 hover:bg-amber-700'}
            >
              {isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : pendingStatus ? (
                <Power className="h-4 w-4 mr-2" />
              ) : (
                <PowerOff className="h-4 w-4 mr-2" />
              )}
              确认{pendingStatus ? '启用' : '停用'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

export default ChannelStatusToggle;
