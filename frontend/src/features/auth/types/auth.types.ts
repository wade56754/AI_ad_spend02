/**
 * Auth Types - 认证类型定义
 *
 * SoT 对齐: AUTH_SPEC.md v2.0
 */

// ========== 用户角色 ==========

export enum UserRole {
  ADMIN = 'admin',
  FINANCE = 'finance',
  DATA_OPERATOR = 'data_operator',
  ACCOUNT_MANAGER = 'account_manager',
  MEDIA_BUYER = 'media_buyer',
}

export const USER_ROLE_CONFIG: Record<UserRole, {
  label: string;
  description: string;
  level: number;
}> = {
  [UserRole.ADMIN]: {
    label: '管理员',
    description: '系统管理员，拥有全部权限',
    level: 100,
  },
  [UserRole.FINANCE]: {
    label: '财务',
    description: '财务人员，管理充值、结算、对账',
    level: 80,
  },
  [UserRole.DATA_OPERATOR]: {
    label: '数据运营',
    description: '数据运营，管理日报和数据导入',
    level: 60,
  },
  [UserRole.ACCOUNT_MANAGER]: {
    label: '客户经理',
    description: '客户经理，管理项目和账户',
    level: 40,
  },
  [UserRole.MEDIA_BUYER]: {
    label: '投手',
    description: '广告投手，执行投放操作',
    level: 20,
  },
};

// ========== 请求接口 ==========

export interface LoginRequest {
  identifier: string;  // 用户名或邮箱 (SoT: AUTH_SPEC.md v2.0)
  password: string;
  remember_me?: boolean;
}

export interface RegisterRequest {
  email: string;
  password: string;
  username: string;
  full_name?: string;
  role?: UserRole;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
  logout_all?: boolean;
}

export interface ResetPasswordRequest {
  email: string;
}

// ========== 响应接口 ==========

export interface User {
  id: string;
  email: string;
  username?: string;
  full_name?: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token?: string;
  expires_in: number;
  token_type: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// ========== 表单状态 ==========

export interface LoginFormState {
  email: string;
  password: string;
  remember_me: boolean;
  isSubmitting: boolean;
  error: string | null;
}

export interface RegisterFormState {
  email: string;
  password: string;
  confirmPassword: string;
  username: string;
  full_name: string;
  isSubmitting: boolean;
  error: string | null;
}
