/**
 * Navigation Types - 导航权限类型定义
 *
 * SoT 对齐: MASTER.md v4.6 §2.4 角色白名单
 * 参考设计: next-shadcn-dashboard-starter
 */

import type { LucideIcon } from 'lucide-react';
import { UserRole } from '@/features/auth/types';

// ========== 权限检查类型 ==========

/**
 * 权限检查配置
 * 用于控制导航项的可见性
 */
export interface PermissionCheck {
  /**
   * 允许访问的角色列表
   * 如果为空或未定义，表示所有角色都可访问
   */
  roles?: UserRole[];

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
