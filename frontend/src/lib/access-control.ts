/**
 * 访问控制函数
 *
 * SoT 引用:
 * - MASTER.md v4.9 §2.4 (权限矩阵)
 * - FRONTEND_PAGE_DESIGN_v2.1.md §5.2 (导航配置)
 *
 * @module lib/access-control
 */

import type { User } from '@/types/user';
import type { NavAccess } from '@/types/navigation';
import type { TechRole } from '@/types/roles';

// ═══════════════════════════════════════════════════════════════════════════
// CEO 配置
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
// 身份判断函数
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 检查用户是否为 CEO
 *
 * 规则: role = 'admin' 且 user.id 在 CEO_USER_IDS 中
 *
 * @example
 * ```tsx
 * if (isCeo(user)) {
 *   // CEO 专属逻辑
 * }
 * ```
 */
export function isCeo(user: User | null): boolean {
  if (!user) return false;
  return user.role === 'admin' && CEO_USER_IDS.includes(user.id);
}

/**
 * 检查用户是否为项目负责人
 *
 * @example
 * ```tsx
 * if (isProjectOwner(user)) {
 *   // 项目负责人专属逻辑
 * }
 * ```
 */
export function isProjectOwner(user: User | null): boolean {
  return user?.is_project_owner === true;
}

// ═══════════════════════════════════════════════════════════════════════════
// 导航访问控制
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 检查用户是否可访问导航项
 *
 * 规则 (OR 逻辑):
 * - allowAll = true → 允许
 * - requireCeo = true 且用户是 CEO → 允许
 * - requireProjectOwner = true 且用户是项目负责人 → 允许
 * - 用户角色在 techRoles 中 → 允许
 * - 其他 → 拒绝
 *
 * @example
 * ```tsx
 * const navItem = {
 *   label: '财务中心',
 *   href: '/finance',
 *   access: { techRoles: ['admin', 'finance'], requireCeo: true }
 * };
 *
 * if (canAccessNav(user, navItem.access)) {
 *   // 显示导航项
 * }
 * ```
 */
export function canAccessNav(user: User | null, access: NavAccess): boolean {
  // 未登录用户无权限
  if (!user) return false;

  // 全部角色开放
  if (access.allowAll) return true;

  // 检查 CEO 身份
  if (access.requireCeo && isCeo(user)) return true;

  // 检查项目负责人身份
  if (access.requireProjectOwner && isProjectOwner(user)) return true;

  // 检查技术层角色
  if (access.techRoles?.includes(user.role as TechRole)) return true;

  return false;
}

/**
 * 过滤导航项列表，只返回用户有权访问的项
 *
 * @example
 * ```tsx
 * const accessibleNavItems = filterNavItems(user, NAV_ITEMS);
 * ```
 */
export function filterNavItems<T extends { access?: NavAccess }>(
  user: User | null,
  items: T[]
): T[] {
  return items.filter((item) => {
    // 没有 access 配置的项默认开放
    if (!item.access) return true;
    return canAccessNav(user, item.access);
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// 页面级访问控制
// ═══════════════════════════════════════════════════════════════════════════

/** 页面路由的访问配置 */
export const PAGE_ACCESS_CONFIG: Record<string, NavAccess> = {
  // 全部角色可访问
  '/': { allowAll: true },
  '/dashboard': { allowAll: true },
  '/daily-reports': { allowAll: true },
  '/topups': { allowAll: true },

  // 特定角色可访问
  '/projects': {
    techRoles: ['admin'],
    requireProjectOwner: true,
    requireCeo: true,
  },
  '/ad-accounts': {
    techRoles: ['admin', 'account_manager'],
    requireProjectOwner: true,
    requireCeo: true,
  },
  '/channels': {
    techRoles: ['admin', 'account_manager'],
    requireCeo: true,
  },
  '/finance': {
    techRoles: ['admin', 'finance'],
    requireCeo: true,
  },
  '/users': {
    techRoles: ['admin'],
    requireCeo: true,
  },
  '/settings': {
    techRoles: ['admin'],
  },
};

/**
 * 检查用户是否可访问指定页面
 *
 * @example
 * ```tsx
 * if (!canAccessPage(user, '/finance')) {
 *   redirect('/');
 * }
 * ```
 */
export function canAccessPage(user: User | null, pathname: string): boolean {
  // 规范化路径
  const normalizedPath = pathname.split('?')[0].replace(/\/$/, '') || '/';

  // 查找完全匹配的配置
  const accessConfig = PAGE_ACCESS_CONFIG[normalizedPath];

  // 未配置的页面默认需要登录
  if (!accessConfig) {
    return user !== null;
  }

  return canAccessNav(user, accessConfig);
}
