/**
 * UserRoleSelect - 用户角色选择器
 *
 * TASK-FE-USER-004: 用户角色分配
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §2 (双层角色架构)
 * - DATA_SCHEMA.md v5.7 (技术层 4 角色)
 * - MASTER.md v4.9 §2.4 (6 业务角色)
 *
 * 功能:
 * - 技术层角色下拉选择（4 个选项）
 * - 角色变更需确认
 * - 显示角色描述
 */

'use client';

import { useState } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
import { Shield, AlertTriangle, Crown, Wallet, Users, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

// === 类型定义 ===

/**
 * 技术层角色（数据库存储）
 * SoT: DATA_SCHEMA.md v5.7
 */
export type TechRole = 'admin' | 'finance' | 'account_manager' | 'media_buyer';

export interface UserRoleSelectProps {
  /** 当前选中的角色 */
  value: TechRole;
  /** 角色变更回调 */
  onChange: (role: TechRole) => void;
  /** 是否需要确认 */
  requireConfirm?: boolean;
  /** 是否禁用 */
  disabled?: boolean;
  /** 自定义类名 */
  className?: string;
}

// === 配置 ===

/**
 * 技术层角色配置
 * SoT: DATA_SCHEMA.md v5.7 + MASTER.md v4.9 §2.4
 */
const TECH_ROLE_CONFIG: Record<TechRole, {
  label: string;
  description: string;
  icon: typeof Shield;
  color: string;
  bgColor: string;
}> = {
  admin: {
    label: '管理员',
    description: '系统配置、用户管理',
    icon: Settings,
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
  },
  finance: {
    label: '财务',
    description: '资金审批、对账结算',
    icon: Wallet,
    color: 'text-green-600',
    bgColor: 'bg-green-100',
  },
  account_manager: {
    label: '户管',
    description: '账户分配、状态监控',
    icon: Users,
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  media_buyer: {
    label: '投手',
    description: '日报填写、广告投放',
    icon: Crown,
    color: 'text-orange-600',
    bgColor: 'bg-orange-100',
  },
};

// === 主组件 ===

export function UserRoleSelect({
  value,
  onChange,
  requireConfirm = true,
  disabled = false,
  className,
}: UserRoleSelectProps) {
  const [pendingRole, setPendingRole] = useState<TechRole | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);

  const currentConfig = TECH_ROLE_CONFIG[value];
  const CurrentIcon = currentConfig.icon;

  const handleValueChange = (newRole: TechRole) => {
    if (newRole === value) return;

    if (requireConfirm) {
      setPendingRole(newRole);
      setShowConfirm(true);
    } else {
      onChange(newRole);
    }
  };

  const handleConfirm = () => {
    if (pendingRole) {
      onChange(pendingRole);
    }
    setShowConfirm(false);
    setPendingRole(null);
  };

  const handleCancel = () => {
    setShowConfirm(false);
    setPendingRole(null);
  };

  return (
    <>
      <Select value={value} onValueChange={handleValueChange} disabled={disabled}>
        <SelectTrigger className={cn('w-full', className)}>
          <SelectValue>
            <div className="flex items-center gap-2">
              <CurrentIcon className={cn('h-4 w-4', currentConfig.color)} />
              <span>{currentConfig.label}</span>
            </div>
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {(Object.entries(TECH_ROLE_CONFIG) as [TechRole, typeof currentConfig][]).map(
            ([role, config]) => {
              const Icon = config.icon;
              return (
                <SelectItem key={role} value={role}>
                  <div className="flex items-center gap-3">
                    <div className={cn('flex h-8 w-8 items-center justify-center rounded-lg', config.bgColor)}>
                      <Icon className={cn('h-4 w-4', config.color)} />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-medium">{config.label}</span>
                      <span className="text-xs text-muted-foreground">{config.description}</span>
                    </div>
                  </div>
                </SelectItem>
              );
            }
          )}
        </SelectContent>
      </Select>

      {/* 确认弹窗 */}
      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              确认变更角色
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-4">
                <p>您确定要变更用户角色吗？角色变更将影响用户的系统权限。</p>

                <div className="flex items-center justify-center gap-4 py-4">
                  {/* 当前角色 */}
                  <div className="flex flex-col items-center gap-2">
                    <div className={cn('flex h-12 w-12 items-center justify-center rounded-lg', currentConfig.bgColor)}>
                      <CurrentIcon className={cn('h-6 w-6', currentConfig.color)} />
                    </div>
                    <Badge variant="outline">{currentConfig.label}</Badge>
                    <span className="text-xs text-muted-foreground">当前角色</span>
                  </div>

                  {/* 箭头 */}
                  <div className="text-2xl text-muted-foreground">→</div>

                  {/* 新角色 */}
                  {pendingRole && (
                    <div className="flex flex-col items-center gap-2">
                      <div className={cn(
                        'flex h-12 w-12 items-center justify-center rounded-lg',
                        TECH_ROLE_CONFIG[pendingRole].bgColor
                      )}>
                        {(() => {
                          const PendingIcon = TECH_ROLE_CONFIG[pendingRole].icon;
                          return <PendingIcon className={cn('h-6 w-6', TECH_ROLE_CONFIG[pendingRole].color)} />;
                        })()}
                      </div>
                      <Badge variant="default">{TECH_ROLE_CONFIG[pendingRole].label}</Badge>
                      <span className="text-xs text-muted-foreground">新角色</span>
                    </div>
                  )}
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancel}>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirm}>确认变更</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

export default UserRoleSelect;
