/**
 * Auth Types - 认证类型定义
 *
 * SoT 对齐: AUTH_SPEC.md v2.0, MASTER.md v4.6 §2.4
 *
 * 6 角色白名单 (PRD v5.1):
 *   ceo, project_owner, finance, pitcher, account_manager, admin
 *
 * 技术层别名:
 *   pitcher ← media_buyer
 */

// ========== 用户角色 ==========

export enum UserRole {
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

export const USER_ROLE_CONFIG: Record<
  UserRole,
  {
    label: string;
    description: string;
    level: number;
  }
> = {
  [UserRole.CEO]: {
    label: '老板',
    description: '资金安全、公司盈亏、最终决策',
    level: 100,
  },
  [UserRole.ADMIN]: {
    label: '管理员',
    description: '系统配置（不参与业务）',
    level: 90,
  },
  [UserRole.FINANCE]: {
    label: '财务',
    description: '资金出入准确、数据真实、对账',
    level: 80,
  },
  [UserRole.PROJECT_OWNER]: {
    label: '项目负责人',
    description: '项目盈亏、日报审核、确认有效粉',
    level: 70,
  },
  [UserRole.ACCOUNT_MANAGER]: {
    label: '户管',
    description: '账户分配、账户状态监控',
    level: 40,
  },
  [UserRole.PITCHER]: {
    label: '投手',
    description: 'CPL 达标、日报准确、执行投放',
    level: 20,
  },
  // 兼容旧代码
  [UserRole.MEDIA_BUYER]: {
    label: '投手',
    description: 'CPL 达标、日报准确、执行投放',
    level: 20,
  },
};

// ========== 请求接口 ==========

export interface LoginRequest {
  identifier: string; // 用户名或邮箱 (SoT: AUTH_SPEC.md v2.0)
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
  // Supabase 返回格式兼容
  session?: {
    access_token: string;
    refresh_token?: string;
    expires_in?: number;
  };
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
