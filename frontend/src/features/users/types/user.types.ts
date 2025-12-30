/**
 * User Management Types
 *
 * SoT 对齐: MASTER.md v4.6 §2.4（宪法）
 * 变更记录: 2025-12-30 统一为 6 角色，移除废弃角色
 *
 * 合法角色（6 角色）:
 *   ceo, project_owner, finance, pitcher, account_manager, admin
 *
 * 废弃角色（禁止使用）:
 *   - supervisor: 已废弃 (PRD v2.2)，合并到 project_owner
 *   - data_operator: 不在宪法中
 *   - media_buyer: 非标准术语，使用 pitcher
 */

export enum UserRole {
  // 合法角色 (MASTER.md v4.6 §2.4)
  CEO = 'ceo',
  PROJECT_OWNER = 'project_owner',
  FINANCE = 'finance',
  PITCHER = 'pitcher',
  ACCOUNT_MANAGER = 'account_manager',
  ADMIN = 'admin',
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
  /** 主管姓名 (JOIN) - SoT: C2-pitcher-mgmt.md §2.2 */
  supervisor_name?: string;
  /** 团队名称 - SoT: C2-pitcher-mgmt.md §2.2 */
  team_name?: string;
  /** 负责账户数 (COUNT) - SoT: C2-pitcher-mgmt.md §2.2 */
  account_count?: number;
  /** 关联项目数 (COUNT) - SoT: C2-pitcher-mgmt.md §2.2 */
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
 * 角色选项 (MASTER.md v4.6 §2.4)
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
