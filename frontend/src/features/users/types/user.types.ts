/**
 * User Management Types
 *
 * SoT: MASTER.md v4.6 §2.4 (6 角色定义)
 * SoT: AUTH_SPEC.md v2.0
 *
 * 6 角色白名单 (MASTER.md v4.6 / PRD v2.2):
 *   ceo, project_owner, finance, pitcher, account_manager, admin
 *
 * 技术层别名 (兼容性保留):
 *   pitcher ← media_buyer
 *
 * 废弃角色 (禁止使用):
 *   supervisor → project_owner
 *   data_operator → finance
 */

export enum UserRole {
  // 6 角色白名单 (MASTER.md v4.6 §2.4 / PRD v2.2)
  CEO = 'ceo',
  PROJECT_OWNER = 'project_owner',
  FINANCE = 'finance',
  PITCHER = 'pitcher',
  ACCOUNT_MANAGER = 'account_manager',
  ADMIN = 'admin',

  // 技术层别名 (兼容性保留)
  /** @deprecated Use PITCHER instead */
  MEDIA_BUYER = 'media_buyer',
}

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
}

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  role: UserRole;
  status: UserStatus;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
  // 关联字段
  account_manager_id?: string;
  /** 管理者姓名 (JOIN from account_manager_id) - 投手的直属管理人 */
  manager_name?: string;
  /** 团队名称 */
  team_name?: string;
  /** 负责账户数 (COUNT) */
  account_count?: number;
  /** 关联项目数 (COUNT) */
  project_count?: number;
}

export interface CreateUserRequest {
  email: string;
  password: string;
  username: string;
  full_name?: string;
  role: UserRole;
  account_manager_id?: string;
}

export interface UpdateUserRequest {
  username?: string;
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
  account_manager_id?: string;
}

export interface UserListParams {
  role?: UserRole;
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface UserListResponse {
  items: User[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * 6 角色选项 (MASTER.md v4.6 §2.4 / PRD v2.2)
 */
export const USER_ROLE_OPTIONS = [
  { value: UserRole.CEO, label: '老板', color: 'purple' },
  { value: UserRole.PROJECT_OWNER, label: '项目负责人', color: 'cyan' },
  { value: UserRole.FINANCE, label: '财务', color: 'green' },
  { value: UserRole.PITCHER, label: '投手', color: 'orange' },
  { value: UserRole.ACCOUNT_MANAGER, label: '户管', color: 'pink' },
  { value: UserRole.ADMIN, label: '管理员', color: 'red' },
];

export const USER_STATUS_OPTIONS = [
  { value: UserStatus.ACTIVE, label: '正常', color: 'green' },
  { value: UserStatus.INACTIVE, label: '未激活', color: 'gray' },
  { value: UserStatus.SUSPENDED, label: '已停用', color: 'red' },
];
