/**
 * UserProjectOwnerToggle - 项目负责人切换组件
 *
 * TASK-FE-USER-004: 用户角色分配
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §2 (双层角色架构)
 * - DATA_SCHEMA.md v5.7 (is_project_owner 字段)
 * - MASTER.md v4.9 §2.4 (project_owner 业务角色)
 *
 * 功能:
 * - 项目负责人切换开关
 * - 显示当前状态
 * - 变更需确认
 */

'use client';

import { useState } from 'react';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';
import { Crown, AlertTriangle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

// === 类型定义 ===

export interface UserProjectOwnerToggleProps {
  /** 当前是否为项目负责人 */
  value: boolean;
  /** 切换回调 */
  onChange: (isProjectOwner: boolean) => void;
  /** 用户名（用于确认弹窗） */
  userName?: string;
  /** 是否需要确认 */
  requireConfirm?: boolean;
  /** 是否禁用 */
  disabled?: boolean;
  /** 显示模式 */
  variant?: 'switch' | 'badge' | 'compact';
  /** 自定义类名 */
  className?: string;
}

// === 主组件 ===

export function UserProjectOwnerToggle({
  value,
  onChange,
  userName,
  requireConfirm = true,
  disabled = false,
  variant = 'switch',
  className,
}: UserProjectOwnerToggleProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingValue, setPendingValue] = useState<boolean | null>(null);

  const handleToggle = (newValue: boolean) => {
    if (newValue === value) return;

    if (requireConfirm) {
      setPendingValue(newValue);
      setShowConfirm(true);
    } else {
      onChange(newValue);
    }
  };

  const handleConfirm = () => {
    if (pendingValue !== null) {
      onChange(pendingValue);
    }
    setShowConfirm(false);
    setPendingValue(null);
  };

  const handleCancel = () => {
    setShowConfirm(false);
    setPendingValue(null);
  };

  // Switch 模式
  const renderSwitch = () => (
    <div className={cn('flex items-center gap-3', className)}>
      <Switch
        id="project-owner-toggle"
        checked={value}
        onCheckedChange={handleToggle}
        disabled={disabled}
      />
      <Label
        htmlFor="project-owner-toggle"
        className={cn(
          'flex items-center gap-2 cursor-pointer',
          disabled && 'cursor-not-allowed opacity-60'
        )}
      >
        <Crown className={cn('h-4 w-4', value ? 'text-amber-500' : 'text-gray-400')} />
        <span className={value ? 'font-medium' : ''}>
          {value ? '项目负责人' : '普通用户'}
        </span>
      </Label>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger>
            <Info className="h-4 w-4 text-muted-foreground" />
          </TooltipTrigger>
          <TooltipContent>
            <p className="max-w-xs">
              项目负责人可以管理项目、审核日报、查看项目利润等。
              这是在技术角色之上的附加权限。
            </p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );

  // Badge 模式
  const renderBadge = () => (
    <Badge
      variant={value ? 'default' : 'secondary'}
      className={cn(
        'cursor-pointer transition-colors',
        disabled && 'cursor-not-allowed opacity-60',
        value && 'bg-amber-500 hover:bg-amber-600',
        className
      )}
      onClick={() => !disabled && handleToggle(!value)}
    >
      <Crown className="h-3 w-3 mr-1" />
      {value ? '项目负责人' : '普通用户'}
    </Badge>
  );

  // Compact 模式
  const renderCompact = () => (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-1 rounded-md cursor-pointer transition-colors',
        value ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-600',
        disabled && 'cursor-not-allowed opacity-60',
        className
      )}
      onClick={() => !disabled && handleToggle(!value)}
    >
      <Crown className="h-3.5 w-3.5" />
      <span className="text-sm font-medium">{value ? '负责人' : '普通'}</span>
    </div>
  );

  // 根据 variant 渲染
  const renderToggle = () => {
    switch (variant) {
      case 'badge':
        return renderBadge();
      case 'compact':
        return renderCompact();
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
              确认{pendingValue ? '授予' : '取消'}项目负责人权限
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-4">
                <p>
                  您确定要{pendingValue ? '授予' : '取消'}
                  {userName ? `「${userName}」` : '该用户'}的项目负责人权限吗？
                </p>

                {pendingValue ? (
                  <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                    <div className="flex items-start gap-2">
                      <Crown className="h-5 w-5 text-amber-500 mt-0.5" />
                      <div className="text-sm">
                        <p className="font-medium text-amber-800">授予后将获得以下权限：</p>
                        <ul className="mt-2 space-y-1 text-amber-700">
                          <li>- 管理所属项目</li>
                          <li>- 审核投手日报</li>
                          <li>- 查看项目利润数据</li>
                          <li>- 申请项目充值</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex items-start gap-2">
                      <Info className="h-5 w-5 text-gray-500 mt-0.5" />
                      <div className="text-sm">
                        <p className="font-medium text-gray-800">取消后将失去以下权限：</p>
                        <ul className="mt-2 space-y-1 text-gray-600">
                          <li>- 无法管理项目</li>
                          <li>- 无法审核日报</li>
                          <li>- 无法查看项目利润</li>
                          <li>- 无法申请充值</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancel}>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirm}
              className={pendingValue ? 'bg-amber-500 hover:bg-amber-600' : ''}
            >
              确认{pendingValue ? '授予' : '取消'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

export default UserProjectOwnerToggle;
