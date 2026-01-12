/**
 * RoleViewSwitcher - 角色视图切换器
 *
 * TASK-FE-DASH-006: 角色视图切换
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §6.1.1 (角色视图差异)
 * - MASTER.md v4.9 §2.4 (6 角色定义)
 *
 * 功能:
 * - 自动检测用户角色并显示对应视图
 * - CEO/Admin 可切换查看其他角色视图
 * - 普通用户仅能查看自己角色视图
 * - 视图切换时数据自动刷新
 */

'use client';

import * as React from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Eye, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { usePermission } from '@/hooks/usePermission';
import type { BusinessRole } from '@/types/roles';

// === 类型定义 ===

export type DashboardViewRole = BusinessRole | 'all';

export interface RoleViewConfig {
  role: DashboardViewRole;
  label: string;
  description: string;
  icon?: React.ReactNode;
}

export interface RoleViewSwitcherProps {
  /** 当前选中的视图角色 */
  currentView: DashboardViewRole;
  /** 视图切换回调 */
  onViewChange: (view: DashboardViewRole) => void;
  /** 是否显示预览标记 */
  showPreviewBadge?: boolean;
  /** 自定义类名 */
  className?: string;
}

// === 角色视图配置 ===

/**
 * 角色视图配置
 * SoT: MASTER.md v4.9 §2.4
 */
export const ROLE_VIEW_CONFIG: RoleViewConfig[] = [
  {
    role: 'ceo',
    label: '老板视图',
    description: '全公司消耗、利润、资金总览',
  },
  {
    role: 'project_owner',
    label: '项目负责人视图',
    description: '项目消耗、利润、投手绩效',
  },
  {
    role: 'finance',
    label: '财务视图',
    description: '账户余额、待审充值、月度流水',
  },
  {
    role: 'pitcher',
    label: '投手视图',
    description: '我的日报、我的账户、我的CPL',
  },
  {
    role: 'account_manager',
    label: '户管视图',
    description: '账户状态、待分配账户',
  },
  {
    role: 'admin',
    label: '管理员视图',
    description: '用户统计、系统健康',
  },
];

// === Hook: useRoleView ===

export interface UseRoleViewOptions {
  /** 初始视图角色 (默认自动检测) */
  initialView?: DashboardViewRole;
  /** 视图切换时的回调 */
  onViewChange?: (view: DashboardViewRole) => void;
}

export interface UseRoleViewReturn {
  /** 当前视图角色 */
  currentView: DashboardViewRole;
  /** 用户的实际业务角色 */
  actualRole: BusinessRole;
  /** 是否可以切换视图 */
  canSwitchView: boolean;
  /** 是否处于预览模式 (查看其他角色视图) */
  isPreviewMode: boolean;
  /** 可用的视图列表 */
  availableViews: RoleViewConfig[];
  /** 切换视图 */
  setCurrentView: (view: DashboardViewRole) => void;
  /** 重置为实际角色视图 */
  resetToActualRole: () => void;
}

/**
 * 角色视图状态 Hook
 *
 * @example
 * ```tsx
 * const { currentView, canSwitchView, setCurrentView, isPreviewMode } = useRoleView();
 *
 * return (
 *   <div>
 *     {canSwitchView && (
 *       <RoleViewSwitcher
 *         currentView={currentView}
 *         onViewChange={setCurrentView}
 *         showPreviewBadge={isPreviewMode}
 *       />
 *     )}
 *     <DashboardContent role={currentView} />
 *   </div>
 * );
 * ```
 */
export function useRoleView(options: UseRoleViewOptions = {}): UseRoleViewReturn {
  const { initialView, onViewChange } = options;
  const { businessRole, isCeo: userIsCeo } = usePermission();

  // 用户的实际业务角色
  const actualRole = businessRole ?? 'pitcher'; // 默认为投手

  // 是否可以切换视图 (仅 CEO 和 Admin)
  const canSwitchView = userIsCeo || businessRole === 'admin';

  // 可用的视图列表
  const availableViews = React.useMemo(() => {
    if (canSwitchView) {
      return ROLE_VIEW_CONFIG;
    }
    // 普通用户只能看自己的视图
    return ROLE_VIEW_CONFIG.filter(v => v.role === actualRole);
  }, [canSwitchView, actualRole]);

  // 当前视图角色
  const [currentView, setCurrentViewInternal] = React.useState<DashboardViewRole>(
    initialView ?? actualRole
  );

  // 是否处于预览模式
  const isPreviewMode = currentView !== actualRole;

  // 切换视图
  const setCurrentView = React.useCallback((view: DashboardViewRole) => {
    // 普通用户不能切换到其他角色视图
    if (!canSwitchView && view !== actualRole) {
      return;
    }
    setCurrentViewInternal(view);
    onViewChange?.(view);
  }, [canSwitchView, actualRole, onViewChange]);

  // 重置为实际角色视图
  const resetToActualRole = React.useCallback(() => {
    setCurrentView(actualRole);
  }, [actualRole, setCurrentView]);

  // 当用户角色变化时，重置视图
  React.useEffect(() => {
    if (!canSwitchView) {
      setCurrentViewInternal(actualRole);
    }
  }, [actualRole, canSwitchView]);

  return {
    currentView,
    actualRole,
    canSwitchView,
    isPreviewMode,
    availableViews,
    setCurrentView,
    resetToActualRole,
  };
}

// === 主组件 ===

/**
 * 角色视图切换器组件
 */
export function RoleViewSwitcher({
  currentView,
  onViewChange,
  showPreviewBadge = false,
  className,
}: RoleViewSwitcherProps) {
  const { canSwitchView, availableViews } = useRoleView();

  // 如果不能切换视图，不渲染
  if (!canSwitchView) {
    return null;
  }

  const currentConfig = ROLE_VIEW_CONFIG.find(v => v.role === currentView);

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Eye className="h-4 w-4 text-muted-foreground" />
      <Select value={currentView} onValueChange={(v) => onViewChange(v as DashboardViewRole)}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="选择视图">
            {currentConfig?.label}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {availableViews.map((config) => (
            <SelectItem key={config.role} value={config.role}>
              <div className="flex flex-col">
                <span>{config.label}</span>
                <span className="text-xs text-muted-foreground">
                  {config.description}
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {showPreviewBadge && (
        <Badge variant="outline" className="text-xs">
          <User className="h-3 w-3 mr-1" />
          预览模式
        </Badge>
      )}
    </div>
  );
}

// === 导出 ===

export default RoleViewSwitcher;
