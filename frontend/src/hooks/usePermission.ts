'use client';

/**
 * 权限检查 Hook
 *
 * SoT 引用:
 * - MASTER.md v4.9 §2.4 (权限矩阵)
 * - AUTH_SPEC.md v2.2 (认证授权规范)
 * - STATE_MACHINE.md v2.9 §2.1 (业务层角色映射)
 *
 * @module hooks/usePermission
 */

import { useMemo } from 'react';
import { useAuth } from '@/features/auth/hooks/useAuth';
import type { BusinessRole, TechRole } from '@/types/roles';
import { TECH_TO_BUSINESS_ROLE } from '@/types/roles';
import { PERMISSION_MATRIX, type PermissionAction } from '@/lib/constants/permission-matrix';

// ═══════════════════════════════════════════════════════════════════════════
// CEO 用户配置
// ═══════════════════════════════════════════════════════════════════════════

/**
 * CEO 用户 ID 列表（从环境变量获取）
 *
 * 配置方式: 在 .env.local 中设置
 * NEXT_PUBLIC_CEO_USER_IDS=1,2,3
 */
const CEO_USER_IDS: number[] = (process.env.NEXT_PUBLIC_CEO_USER_IDS || '')
  .split(',')
  .filter(Boolean)
  .map(Number)
  .filter((id) => !isNaN(id));

// ═══════════════════════════════════════════════════════════════════════════
// 类型定义
// ═══════════════════════════════════════════════════════════════════════════

export interface UsePermissionReturn {
  /** 用户信息是否加载中 */
  isLoading: boolean;
  /** 当前用户的业务层角色 */
  businessRole: BusinessRole | null;
  /** 判断当前用户是否为 CEO */
  isCeo: () => boolean;
  /** 判断当前用户是否为项目负责人 */
  isProjectOwner: () => boolean;
  /** 检查是否拥有指定权限 */
  can: (action: PermissionAction) => boolean;
  /** 检查是否拥有任意一个权限 */
  canAny: (actions: PermissionAction[]) => boolean;
  /** 检查是否拥有所有权限 */
  canAll: (actions: PermissionAction[]) => boolean;
  /** 获取当前用户拥有的所有权限 */
  getAllPermissions: () => PermissionAction[];
}

// ═══════════════════════════════════════════════════════════════════════════
// Hook 实现
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 权限检查 Hook
 *
 * 提供基于业务层角色的权限检查功能。
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { can, isCeo, businessRole } = usePermission();
 *
 *   if (!can('daily_report:review')) {
 *     return <AccessDenied />;
 *   }
 *
 *   return (
 *     <div>
 *       {isCeo() && <AdminPanel />}
 *       <Content />
 *     </div>
 *   );
 * }
 * ```
 */
export function usePermission(): UsePermissionReturn {
  const { user, isLoading } = useAuth();

  // useMemo 依赖说明:
  // - user: 用户信息变化时需要重新计算权限
  // - isLoading: 加载状态变化时需要更新返回值
  // - CEO_USER_IDS 是模块级常量，不需要作为依赖
  // - PERMISSION_MATRIX/TECH_TO_BUSINESS_ROLE 是静态映射，不需要作为依赖
  return useMemo(() => {
    // ─── 用户未登录或加载中 ───
    if (!user) {
      return {
        isLoading,
        businessRole: null,
        isCeo: () => false,
        isProjectOwner: () => false,
        can: () => false,
        canAny: () => false,
        canAll: () => false,
        getAllPermissions: () => [],
      };
    }

    // ─── CEO 判断 ───
    // 规则: role = 'admin' 且 user.id 在 CEO_USER_IDS 中
    const checkIsCeo = (): boolean => {
      return user.role === 'admin' && CEO_USER_IDS.includes(user.id);
    };

    // ─── 项目负责人判断 ───
    const checkIsProjectOwner = (): boolean => {
      return user.is_project_owner === true;
    };

    // ─── 获取业务层角色 ───
    // 优先级: CEO > 项目负责人 > 技术角色映射
    const getBusinessRole = (): BusinessRole => {
      if (checkIsCeo()) return 'ceo';
      if (checkIsProjectOwner()) return 'project_owner';
      // 技术角色映射到业务角色
      const techRole = user.role as TechRole;
      return TECH_TO_BUSINESS_ROLE[techRole] || 'pitcher';
    };

    const businessRole = getBusinessRole();

    // ─── 权限检查 ───
    const can = (action: PermissionAction): boolean => {
      const allowedRoles = PERMISSION_MATRIX[action];
      if (!allowedRoles) {
        console.warn(`[usePermission] Unknown permission action: ${action}`);
        return false;
      }
      return allowedRoles.includes(businessRole);
    };

    const canAny = (actions: PermissionAction[]): boolean => {
      return actions.some((action) => can(action));
    };

    const canAll = (actions: PermissionAction[]): boolean => {
      return actions.every((action) => can(action));
    };

    // ─── 获取所有权限 ───
    const getAllPermissions = (): PermissionAction[] => {
      return (Object.keys(PERMISSION_MATRIX) as PermissionAction[]).filter(
        (action) => PERMISSION_MATRIX[action].includes(businessRole)
      );
    };

    return {
      isLoading: false,
      businessRole,
      isCeo: checkIsCeo,
      isProjectOwner: checkIsProjectOwner,
      can,
      canAny,
      canAll,
      getAllPermissions,
    };
  }, [user, isLoading]);
}

// ═══════════════════════════════════════════════════════════════════════════
// 辅助 Hooks
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 权限守卫 Hook
 *
 * 用于页面级别的权限检查，返回是否有权限访问。
 *
 * @example
 * ```tsx
 * function FinancePage() {
 *   const { hasAccess, isLoading } = usePermissionGuard('finance:view');
 *
 *   if (isLoading) return <Loading />;
 *   if (!hasAccess) return <AccessDenied />;
 *
 *   return <FinanceContent />;
 * }
 * ```
 */
export function usePermissionGuard(
  requiredAction: PermissionAction | PermissionAction[]
): {
  hasAccess: boolean;
  isLoading: boolean;
  businessRole: BusinessRole | null;
} {
  const { can, canAny, isLoading, businessRole } = usePermission();

  const hasAccess = useMemo(() => {
    if (isLoading) return false;
    if (Array.isArray(requiredAction)) {
      return canAny(requiredAction);
    }
    return can(requiredAction);
  }, [can, canAny, isLoading, requiredAction]);

  return { hasAccess, isLoading, businessRole };
}

/**
 * 检查是否为特定角色
 *
 * @example
 * ```tsx
 * const { isRole } = useRoleCheck();
 * if (isRole('finance')) {
 *   // 财务专属逻辑
 * }
 * ```
 */
export function useRoleCheck(): {
  isRole: (role: BusinessRole) => boolean;
  isAnyRole: (roles: BusinessRole[]) => boolean;
  businessRole: BusinessRole | null;
  isLoading: boolean;
} {
  const { businessRole, isLoading } = usePermission();

  const isRole = (role: BusinessRole): boolean => {
    return businessRole === role;
  };

  const isAnyRole = (roles: BusinessRole[]): boolean => {
    return businessRole !== null && roles.includes(businessRole);
  };

  return { isRole, isAnyRole, businessRole, isLoading };
}

export default usePermission;
