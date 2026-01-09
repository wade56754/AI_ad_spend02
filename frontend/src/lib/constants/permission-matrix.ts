/**
 * 权限矩阵定义
 *
 * SoT 引用:
 * - MASTER.md v4.9 §2.4 (权限矩阵)
 * - AUTH_SPEC.md v2.2 (认证授权规范)
 *
 * @module lib/constants/permission-matrix
 */

import type { BusinessRole } from '@/types/roles';

// ═══════════════════════════════════════════════════════════════════════════
// 操作权限定义
// ═══════════════════════════════════════════════════════════════════════════

export type PermissionAction =
  // ─── 日报操作 ───
  | 'daily_report:create'
  | 'daily_report:view'
  | 'daily_report:view_all'
  | 'daily_report:review'
  | 'daily_report:confirm'
  // ─── 项目操作 ───
  | 'project:create'
  | 'project:view'
  | 'project:view_all'
  | 'project:edit'
  | 'project:manage_members'
  // ─── 账户操作 ───
  | 'ad_account:create'
  | 'ad_account:view'
  | 'ad_account:view_all'
  | 'ad_account:assign'
  | 'ad_account:change_status'
  // ─── 充值操作 ───
  | 'topup:create'
  | 'topup:view'
  | 'topup:view_all'
  | 'topup:approve'
  | 'topup:approve_large' // >50000
  // ─── 财务操作 ───
  | 'finance:view'
  | 'finance:export'
  | 'finance:lock'
  // ─── 用户操作 ───
  | 'user:create'
  | 'user:view'
  | 'user:edit'
  | 'user:delete'
  // ─── 渠道操作 ───
  | 'channel:create'
  | 'channel:view'
  | 'channel:edit'
  // ─── 系统设置 ───
  | 'settings:view'
  | 'settings:edit';

// ═══════════════════════════════════════════════════════════════════════════
// 权限矩阵 - 与 MASTER.md v4.9 §2.4 对齐
// ═══════════════════════════════════════════════════════════════════════════

export const PERMISSION_MATRIX: Record<PermissionAction, BusinessRole[]> = {
  // ─── 日报权限 ───
  'daily_report:create': ['pitcher'],
  'daily_report:view': ['ceo', 'project_owner', 'finance', 'pitcher', 'account_manager', 'admin'],
  'daily_report:view_all': ['ceo', 'admin'],
  'daily_report:review': ['project_owner', 'admin'],
  'daily_report:confirm': ['project_owner', 'admin'],

  // ─── 项目权限 ───
  'project:create': ['ceo', 'admin'],
  'project:view': ['ceo', 'project_owner', 'finance', 'admin'],
  'project:view_all': ['ceo', 'admin'],
  'project:edit': ['ceo', 'project_owner', 'admin'],
  'project:manage_members': ['ceo', 'project_owner', 'admin'],

  // ─── 账户权限 ───
  'ad_account:create': ['account_manager', 'admin'],
  'ad_account:view': ['ceo', 'project_owner', 'account_manager', 'pitcher', 'admin'],
  'ad_account:view_all': ['ceo', 'account_manager', 'admin'],
  'ad_account:assign': ['account_manager', 'admin'],
  'ad_account:change_status': ['account_manager', 'admin'],

  // ─── 充值权限 ───
  'topup:create': ['pitcher', 'account_manager'],
  'topup:view': ['ceo', 'project_owner', 'finance', 'pitcher', 'account_manager', 'admin'],
  'topup:view_all': ['ceo', 'finance', 'admin'],
  'topup:approve': ['finance', 'admin'],
  'topup:approve_large': ['ceo'], // 大额充值 (>50000) 仅 CEO

  // ─── 财务权限 ───
  'finance:view': ['ceo', 'finance', 'admin'],
  'finance:export': ['ceo', 'finance', 'admin'],
  'finance:lock': ['ceo', 'finance'],

  // ─── 用户权限 ───
  'user:create': ['admin'],
  'user:view': ['ceo', 'admin'],
  'user:edit': ['admin'],
  'user:delete': ['admin'],

  // ─── 渠道权限 ───
  'channel:create': ['admin'],
  'channel:view': ['ceo', 'project_owner', 'account_manager', 'admin'],
  'channel:edit': ['admin'],

  // ─── 系统设置 ───
  'settings:view': ['admin'],
  'settings:edit': ['admin'],
};

// ═══════════════════════════════════════════════════════════════════════════
// 权限组定义 (便于批量检查)
// ═══════════════════════════════════════════════════════════════════════════

export const PERMISSION_GROUPS = {
  // 日报模块完整权限
  DAILY_REPORT_FULL: [
    'daily_report:create',
    'daily_report:view',
    'daily_report:review',
    'daily_report:confirm',
  ] as PermissionAction[],

  // 项目管理权限
  PROJECT_MANAGE: [
    'project:create',
    'project:edit',
    'project:manage_members',
  ] as PermissionAction[],

  // 账户管理权限
  ACCOUNT_MANAGE: [
    'ad_account:create',
    'ad_account:assign',
    'ad_account:change_status',
  ] as PermissionAction[],

  // 财务模块权限
  FINANCE_FULL: [
    'finance:view',
    'finance:export',
    'finance:lock',
  ] as PermissionAction[],

  // 用户管理权限
  USER_MANAGE: [
    'user:create',
    'user:edit',
    'user:delete',
  ] as PermissionAction[],
} as const;

// ═══════════════════════════════════════════════════════════════════════════
// 辅助函数
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 获取角色拥有的所有权限
 */
export function getPermissionsForRole(role: BusinessRole): PermissionAction[] {
  return (Object.keys(PERMISSION_MATRIX) as PermissionAction[]).filter(
    (action) => PERMISSION_MATRIX[action].includes(role)
  );
}

/**
 * 检查权限是否存在于矩阵中
 */
export function isValidPermissionAction(action: string): action is PermissionAction {
  return action in PERMISSION_MATRIX;
}
