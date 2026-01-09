/**
 * 导航配置
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §5.2 (导航配置)
 * - MASTER.md v4.9 §2.4 (角色权限)
 *
 * @module lib/navigation
 */

import type { NavAccess } from '@/types/navigation';

// ═══════════════════════════════════════════════════════════════════════════
// 导航项接口
// ═══════════════════════════════════════════════════════════════════════════

export interface SidebarNavItem {
  /** 显示标签 */
  label: string;
  /** 路由路径 */
  href: string;
  /** lucide-react 图标名称 */
  icon: string;
  /** 访问控制配置 */
  access: NavAccess;
  /** 徽章内容 (可选) */
  badge?: string | number;
  /** 子菜单 (可选) */
  children?: SidebarNavItem[];
}

// ═══════════════════════════════════════════════════════════════════════════
// 主导航配置
// ═══════════════════════════════════════════════════════════════════════════

export const NAV_ITEMS: SidebarNavItem[] = [
  // ─── 全部角色可访问 ───
  {
    label: '驾驶舱',
    href: '/dashboard',
    icon: 'LayoutDashboard',
    access: { allowAll: true },
  },
  {
    label: '日报管理',
    href: '/daily-reports',
    icon: 'FileText',
    access: { allowAll: true },
  },
  {
    label: '充值管理',
    href: '/topups',
    icon: 'CreditCard',
    access: { allowAll: true },
  },

  // ─── 特定角色可访问 ───
  {
    label: '项目管理',
    href: '/projects',
    icon: 'FolderKanban',
    access: {
      techRoles: ['admin'],
      requireProjectOwner: true,
      requireCeo: true,
    },
  },
  {
    label: '账户管理',
    href: '/ad-accounts',
    icon: 'Users',
    access: {
      techRoles: ['admin', 'account_manager'],
      requireProjectOwner: true,
      requireCeo: true,
    },
  },
  {
    label: '渠道管理',
    href: '/channels',
    icon: 'Radio',
    access: {
      techRoles: ['admin', 'account_manager'],
      requireCeo: true,
    },
  },
  {
    label: '财务中心',
    href: '/finance',
    icon: 'Wallet',
    access: {
      techRoles: ['admin', 'finance'],
      requireCeo: true,
    },
  },
  {
    label: '用户管理',
    href: '/users',
    icon: 'UserCog',
    access: {
      techRoles: ['admin'],
      requireCeo: true,
    },
  },
  {
    label: '系统设置',
    href: '/settings',
    icon: 'Settings',
    access: {
      techRoles: ['admin'],
    },
  },
];

// ═══════════════════════════════════════════════════════════════════════════
// 底部导航配置
// ═══════════════════════════════════════════════════════════════════════════

export const BOTTOM_NAV_ITEMS: SidebarNavItem[] = [
  {
    label: '个人资料',
    href: '/profile',
    icon: 'User',
    access: { allowAll: true },
  },
  {
    label: '帮助中心',
    href: '/help',
    icon: 'HelpCircle',
    access: { allowAll: true },
  },
];

// ═══════════════════════════════════════════════════════════════════════════
// 导航分组配置 (用于侧边栏分组显示)
// ═══════════════════════════════════════════════════════════════════════════

export interface NavGroup {
  title: string;
  items: SidebarNavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    title: '工作台',
    items: [
      NAV_ITEMS[0], // 驾驶舱
      NAV_ITEMS[1], // 日报管理
      NAV_ITEMS[2], // 充值管理
    ],
  },
  {
    title: '业务管理',
    items: [
      NAV_ITEMS[3], // 项目管理
      NAV_ITEMS[4], // 账户管理
      NAV_ITEMS[5], // 渠道管理
    ],
  },
  {
    title: '系统管理',
    items: [
      NAV_ITEMS[6], // 财务中心
      NAV_ITEMS[7], // 用户管理
      NAV_ITEMS[8], // 系统设置
    ],
  },
];
