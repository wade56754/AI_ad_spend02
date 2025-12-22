/**
 * User Management Types
 *
 * SoT 对齐: AUTH_SPEC.md v2.0
 */

export enum UserRole {
  ADMIN = 'admin',
  FINANCE = 'finance',
  DATA_OPERATOR = 'data_operator',
  ACCOUNT_MANAGER = 'account_manager',
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
  account_manager_id?: string;
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

export const USER_ROLE_OPTIONS = [
  { value: UserRole.ADMIN, label: '管理员', color: 'red' },
  { value: UserRole.FINANCE, label: '财务', color: 'green' },
  { value: UserRole.DATA_OPERATOR, label: '数据运营', color: 'blue' },
  { value: UserRole.ACCOUNT_MANAGER, label: '客户经理', color: 'purple' },
  { value: UserRole.MEDIA_BUYER, label: '投手', color: 'orange' },
];

export const USER_STATUS_OPTIONS = [
  { value: UserStatus.ACTIVE, label: '正常', color: 'green' },
  { value: UserStatus.INACTIVE, label: '未激活', color: 'gray' },
  { value: UserStatus.SUSPENDED, label: '已停用', color: 'red' },
];
