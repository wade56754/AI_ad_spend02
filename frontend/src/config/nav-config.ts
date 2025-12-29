/**
 * Navigation Configuration - 导航菜单配置
 *
 * SoT 对齐: MASTER.md v4.6 §2.4 角色白名单
 *
 * 角色权限说明:
 * - admin: 系统管理员，拥有全部权限
 * - finance: 财务人员，管理充值、结算、对账
 * - project_owner: 项目负责人，对项目盈亏负责
 * - data_operator: 数据运营，管理日报和数据导入
 * - account_manager: 客户经理，管理项目和账户
 * - media_buyer: 投手，执行投放操作
 */

import {
  LayoutDashboard,
  FolderKanban,
  Users,
  FileText,
  CalendarDays,
  DollarSign,
  UserCog,
  Settings,
  CreditCard,
  BarChart3,
  ClipboardList,
  Building2,
  type LucideIcon,
} from 'lucide-react';

import { UserRole } from '@/features/auth/types';
import type { NavGroup, NavItem } from '@/types/navigation';

// ========== 导航项定义 ==========

/**
 * 主导航配置
 *
 * 权限规则:
 * - 无 access: 所有角色可见
 * - access.roles: 仅指定角色可见
 * - access.minLevel: 角色等级 >= minLevel 可见
 */
export const mainNavGroups: NavGroup[] = [
  {
    title: '业务管理',
    items: [
      {
        id: 'dashboard',
        title: '运营驾驶舱',
        url: '/',
        icon: LayoutDashboard,
        description: '实时数据概览',
        // 所有角色都可以访问仪表盘
      },
      {
        id: 'projects',
        title: '项目管理',
        url: '/projects',
        icon: FolderKanban,
        description: '管理广告项目',
        access: {
          // 投手不能管理项目
          roles: [
            UserRole.ADMIN,
            UserRole.PROJECT_OWNER,
            UserRole.ACCOUNT_MANAGER,
            UserRole.FINANCE,
          ],
        },
      },
      {
        id: 'ad-accounts',
        title: '广告账户',
        url: '/ad-accounts',
        icon: Building2,
        description: '管理广告账户',
        access: {
          // 投手可查看自己的账户，其他角色可管理
          roles: [
            UserRole.ADMIN,
            UserRole.ACCOUNT_MANAGER,
            UserRole.PROJECT_OWNER,
            UserRole.MEDIA_BUYER,
          ],
        },
      },
      {
        id: 'daily-reports',
        title: '日报管理',
        url: '/daily-reports',
        icon: FileText,
        description: '广告投放日报',
        access: {
          // 日报相关角色
          roles: [
            UserRole.ADMIN,
            UserRole.PROJECT_OWNER,
            UserRole.DATA_OPERATOR,
            UserRole.MEDIA_BUYER,
          ],
        },
      },
      {
        id: 'weekly-briefs',
        title: '周度简报',
        url: '/weekly-briefs',
        icon: CalendarDays,
        description: '周度数据汇总',
        access: {
          // 管理层角色
          roles: [UserRole.ADMIN, UserRole.PROJECT_OWNER, UserRole.FINANCE],
        },
      },
    ],
  },
  {
    title: '财务管理',
    access: {
      // 整个分组只对财务相关角色可见
      roles: [UserRole.ADMIN, UserRole.FINANCE, UserRole.PROJECT_OWNER],
    },
    items: [
      {
        id: 'finance',
        title: '财务概览',
        url: '/finance',
        icon: DollarSign,
        description: '财务数据汇总',
      },
      {
        id: 'topups',
        title: '充值管理',
        url: '/topups',
        icon: CreditCard,
        description: '充值申请与审批',
        access: {
          roles: [UserRole.ADMIN, UserRole.FINANCE, UserRole.PROJECT_OWNER],
        },
      },
      {
        id: 'reconciliation',
        title: '对账管理',
        url: '/reconciliation',
        icon: ClipboardList,
        description: '账单核对',
        access: {
          roles: [UserRole.ADMIN, UserRole.FINANCE],
        },
      },
      {
        id: 'profit-reports',
        title: '利润报表',
        url: '/profit-reports',
        icon: BarChart3,
        description: '项目利润分析',
        access: {
          roles: [UserRole.ADMIN, UserRole.FINANCE, UserRole.PROJECT_OWNER],
        },
      },
    ],
  },
  {
    title: '系统管理',
    access: {
      // 仅管理员可见
      roles: [UserRole.ADMIN],
    },
    items: [
      {
        id: 'users',
        title: '用户管理',
        url: '/users',
        icon: UserCog,
        description: '管理系统用户',
      },
      {
        id: 'channels',
        title: '渠道管理',
        url: '/channels',
        icon: Users,
        description: '管理投放渠道',
      },
      {
        id: 'settings',
        title: '系统设置',
        url: '/settings',
        icon: Settings,
        description: '系统配置',
      },
    ],
  },
];

// ========== 底部导航 ==========

/**
 * 底部导航项 (不需要权限过滤)
 */
export const bottomNavItems: NavItem[] = [
  {
    id: 'profile',
    title: '个人设置',
    url: '/profile',
    icon: UserCog,
  },
];

// ========== 角色-菜单映射表 (用于文档) ==========

/**
 * 角色权限矩阵
 *
 * | 菜单项 | admin | finance | project_owner | data_operator | account_manager | media_buyer |
 * |--------|-------|---------|---------------|---------------|-----------------|-------------|
 * | 运营驾驶舱 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
 * | 项目管理 | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
 * | 广告账户 | ✅ | ❌ | ✅ | ❌ | ✅ | ✅(只读) |
 * | 日报管理 | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
 * | 周度简报 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
 * | 财务概览 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
 * | 充值管理 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
 * | 对账管理 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
 * | 利润报表 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
 * | 用户管理 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
 * | 渠道管理 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
 * | 系统设置 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
 */

// ========== 辅助函数 ==========

/**
 * 获取角色可访问的菜单 ID 列表 (用于调试)
 */
export function getAccessibleMenuIds(role: UserRole): string[] {
  const ids: string[] = [];

  for (const group of mainNavGroups) {
    // 检查分组权限
    if (group.access?.roles && !group.access.roles.includes(role)) {
      continue;
    }

    for (const item of group.items) {
      // 检查菜单项权限
      if (!item.access?.roles || item.access.roles.includes(role)) {
        ids.push(item.id);
      }
    }
  }

  return ids;
}
