/**
 * User Management Types
 *
 * SoT: docs/10.module-specs/C2-pitcher-mgmt.md §2 数据需求
 * SoT: MASTER.md v4.4 §2.4 (7 角色定义)
 * SoT: AUTH_SPEC.md v2.0
 *
 * 标准角色 (MASTER.md v4.4):
 *   ceo, project_owner, finance, supervisor, pitcher, account_manager, admin
 *
 * 角色映射 (C2-pitcher-mgmt.md §2.4):
 *   pitcher ← media_buyer (历史角色名)
 *   supervisor ← data_operator (历史角色名)
 */

export enum UserRole {
  // 标准角色 (MASTER.md v4.4 §2.4)
  CEO = 'ceo',
  PROJECT_OWNER = 'project_owner',
  FINANCE = 'finance',
  SUPERVISOR = 'supervisor',
  PITCHER = 'pitcher',
  ACCOUNT_MANAGER = 'account_manager',
  ADMIN = 'admin',

  // 历史角色名 (兼容性保留，禁止新代码使用)
  /** @deprecated Use SUPERVISOR instead */
  DATA_OPERATOR = 'data_operator',
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
 * 标准角色选项 (MASTER.md v4.4 §2.4)
 * SoT: C2-pitcher-mgmt.md §2.4
 */
export const USER_ROLE_OPTIONS = [
  { value: UserRole.CEO, label: '老板', color: 'purple' },
  { value: UserRole.PROJECT_OWNER, label: '项目负责人', color: 'cyan' },
  { value: UserRole.FINANCE, label: '财务', color: 'green' },
  { value: UserRole.SUPERVISOR, label: '主管', color: 'blue' },
  { value: UserRole.PITCHER, label: '投手', color: 'orange' },
  { value: UserRole.ACCOUNT_MANAGER, label: '户管', color: 'pink' },
  { value: UserRole.ADMIN, label: '管理员', color: 'red' },
];

export const USER_STATUS_OPTIONS = [
  { value: UserStatus.ACTIVE, label: '正常', color: 'green' },
  { value: UserStatus.INACTIVE, label: '未激活', color: 'gray' },
  { value: UserStatus.SUSPENDED, label: '已停用', color: 'red' },
];
