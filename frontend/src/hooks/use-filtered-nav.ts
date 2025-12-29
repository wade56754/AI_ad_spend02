/**
 * useFilteredNavItems - 基于角色的导航权限过滤钩子
 *
 * SoT 对齐: MASTER.md v4.6 §2.4 角色白名单
 * 参考设计: next-shadcn-dashboard-starter
 *
 * 安全说明:
 * - 这是仅限 UI 的可见性控制
 * - 实际 API 安全必须在服务端实施
 * - 不要依赖客户端过滤进行真正的授权
 */

'use client';

import { useMemo } from 'react';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { UserRole, USER_ROLE_CONFIG } from '@/features/auth/types';
import type {
  NavItem,
  NavGroup,
  PermissionCheck,
  FilteredNavItem,
  FilteredNavGroup,
} from '@/types/navigation';

// ========== 权限检查函数 ==========

/**
 * 检查用户是否有权限访问导航项
 *
 * @param access - 权限检查配置
 * @param userRole - 用户角色
 * @param userLevel - 用户角色等级
 * @returns 是否有权限
 */
function checkAccess(
  access: PermissionCheck | undefined,
  userRole: UserRole | undefined,
  userLevel: number
): boolean {
  // 无权限配置 = 所有人可访问
  if (!access) return true;

  // 未登录用户无法访问任何有权限配置的项
  if (!userRole) return false;

  // 检查角色列表
  if (access.roles && access.roles.length > 0) {
    if (!access.roles.includes(userRole)) {
      return false;
    }
  }

  // 检查最低等级要求
  if (access.minLevel !== undefined) {
    if (userLevel < access.minLevel) {
      return false;
    }
  }

  // 项目上下文检查 (预留，暂不实现)
  // if (access.requireProject) {
  //   // TODO: 检查用户是否有关联项目
  // }

  return true;
}

/**
 * 获取用户角色等级
 */
function getUserLevel(role: UserRole | undefined): number {
  if (!role) return 0;
  return USER_ROLE_CONFIG[role]?.level ?? 0;
}

// ========== 过滤函数 ==========

/**
 * 递归过滤导航项
 */
function filterNavItems(
  items: NavItem[],
  userRole: UserRole | undefined,
  userLevel: number
): FilteredNavItem[] {
  return (
    items
      .filter((item) => checkAccess(item.access, userRole, userLevel))
      .map((item) => {
        // 移除 access 字段，生成 FilteredNavItem
        const { access, items: children, ...rest } = item;

        const filtered: FilteredNavItem = { ...rest };

        // 递归处理子菜单
        if (children && children.length > 0) {
          const filteredChildren = filterNavItems(children, userRole, userLevel);
          // 只有子菜单有内容时才保留
          if (filteredChildren.length > 0) {
            filtered.items = filteredChildren;
          }
        }

        return filtered;
      })
      // 过滤掉没有 url 且没有子菜单的项
      .filter((item) => item.url || (item.items && item.items.length > 0))
  );
}

/**
 * 过滤导航分组
 */
function filterNavGroups(
  groups: NavGroup[],
  userRole: UserRole | undefined,
  userLevel: number
): FilteredNavGroup[] {
  return (
    groups
      .filter((group) => checkAccess(group.access, userRole, userLevel))
      .map((group) => {
        const { access, items, ...rest } = group;
        return {
          ...rest,
          items: filterNavItems(items, userRole, userLevel),
        };
      })
      // 过滤掉空分组
      .filter((group) => group.items.length > 0)
  );
}

// ========== Hooks ==========

/**
 * 过滤导航项的 Hook
 *
 * @param items - 原始导航项数组
 * @returns 过滤后的导航项数组
 *
 * @example
 * ```tsx
 * const navItems = useFilteredNavItems(rawNavItems);
 * return navItems.map(item => <NavLink {...item} />);
 * ```
 */
export function useFilteredNavItems(items: NavItem[]): FilteredNavItem[] {
  const { user } = useAuth();

  return useMemo(() => {
    const userRole = user?.role;
    const userLevel = getUserLevel(userRole);

    return filterNavItems(items, userRole, userLevel);
  }, [items, user?.role]);
}

/**
 * 过滤导航分组的 Hook
 *
 * @param groups - 原始导航分组数组
 * @returns 过滤后的导航分组数组
 *
 * @example
 * ```tsx
 * const navGroups = useFilteredNavGroups(rawNavGroups);
 * return navGroups.map(group => (
 *   <NavSection title={group.title}>
 *     {group.items.map(item => <NavLink {...item} />)}
 *   </NavSection>
 * ));
 * ```
 */
export function useFilteredNavGroups(groups: NavGroup[]): FilteredNavGroup[] {
  const { user } = useAuth();

  return useMemo(() => {
    const userRole = user?.role;
    const userLevel = getUserLevel(userRole);

    return filterNavGroups(groups, userRole, userLevel);
  }, [groups, user?.role]);
}

/**
 * 检查用户是否有权限访问指定路由
 *
 * @param access - 权限检查配置
 * @returns 是否有权限
 *
 * @example
 * ```tsx
 * const canAccess = useHasAccess({ roles: [UserRole.ADMIN, UserRole.FINANCE] });
 * if (!canAccess) return <AccessDenied />;
 * ```
 */
export function useHasAccess(access: PermissionCheck): boolean {
  const { user } = useAuth();

  return useMemo(() => {
    const userRole = user?.role;
    const userLevel = getUserLevel(userRole);

    return checkAccess(access, userRole, userLevel);
  }, [access, user?.role]);
}

/**
 * 获取当前用户角色信息
 *
 * @returns 角色信息对象
 */
export function useUserRole() {
  const { user } = useAuth();

  return useMemo(() => {
    const role = user?.role;
    const config = role ? USER_ROLE_CONFIG[role] : null;

    return {
      role,
      label: config?.label ?? '未知',
      description: config?.description ?? '',
      level: config?.level ?? 0,
    };
  }, [user?.role]);
}
