/**
 * Navigation Types - 导航权限类型定义
 *
 * SoT 引用:
 * - MASTER.md v4.9 §2.4 (角色白名单)
 * - FRONTEND_PAGE_DESIGN_v2.1.md §5.2 (导航配置)
 */

import type { LucideIcon } from 'lucide-react';
import type { TechRole } from './roles';

// ========== 导航访问控制类型 (新) ==========

/**
 * 导航访问控制配置
 *
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §5.2
 *
 * 规则: allowAll OR (techRoles OR requireProjectOwner OR requireCeo)
 */
export interface NavAccess {
  /** 允许访问的技术层角色 */
  techRoles?: TechRole[];
  /** 是否需要项目负责人身份 */
  requireProjectOwner?: boolean;
  /** 是否需要 CEO 身份 */
  requireCeo?: boolean;
  /** 是否对全部角色开放 */
  allowAll?: boolean;
}

// ========== 权限检查类型 (旧版兼容) ==========

/**
 * 权限检查配置 (旧版)
 * @deprecated 建议使用 NavAccess
 */
export interface PermissionCheck {
  /**
   * 允许访问的角色列表
   * 如果为空或未定义，表示所有角色都可访问
   */
  roles?: string[];

  /**
   * 是否需要项目上下文
   * 某些功能需要用户选择/关联项目后才能访问
   */
  requireProject?: boolean;

  /**
   * 角色层级要求 (可选)
   * 用户角色 level 必须 >= minLevel 才能访问
   * 参考 USER_ROLE_CONFIG 中的 level 定义
   */
  minLevel?: number;
}

// ========== 导航项类型 ==========

/**
 * 基础导航项
 */
export interface NavItem {
  /** 唯一标识符 */
  id: string;

  /** 显示标题 */
  title: string;

  /** 路由路径 */
  url: string;

  /** 图标组件 */
  icon?: LucideIcon;

  /** 是否禁用 */
  disabled?: boolean;

  /** 外部链接 */
  external?: boolean;

  /** 快捷键 */
  shortcut?: string;

  /** 标签/徽章 */
  badge?: string | number;

  /** 描述文字 */
  description?: string;

  /** 权限检查配置 */
  access?: PermissionCheck;

  /** 子菜单项 */
  items?: NavItem[];
}

/**
 * 导航分组
 */
export interface NavGroup {
  /** 分组标题 */
  title: string;

  /** 分组内的导航项 */
  items: NavItem[];

  /** 分组级别的权限检查 (可选) */
  access?: PermissionCheck;
}

// ========== 导航配置类型 ==========

/**
 * 完整导航配置
 */
export interface NavigationConfig {
  /** 主导航分组 */
  mainNav: NavGroup[];

  /** 底部导航项 */
  bottomNav?: NavItem[];
}

// ========== 辅助类型 ==========

/**
 * 过滤后的导航项 (运行时使用)
 */
export type FilteredNavItem = Omit<NavItem, 'access' | 'items'> & {
  items?: FilteredNavItem[];
};

/**
 * 过滤后的导航分组 (运行时使用)
 */
export type FilteredNavGroup = Omit<NavGroup, 'access' | 'items'> & {
  items: FilteredNavItem[];
};
