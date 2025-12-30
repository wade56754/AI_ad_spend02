/**
 * Auth Types - 认证类型定义
 *
 * SoT 对齐: MASTER.md v4.6 §2.4（宪法）
 * 变更记录: 2025-12-30 统一为 6 角色，移除 data_operator, media_buyer→pitcher
 */

// ========== 用户角色 ==========

/**
 * 合法角色（6 角色）
 * 来源: MASTER.md v4.6 §2.4
 *
 * 废弃角色（禁止使用）:
 * - supervisor: 已废弃 (PRD v2.2)，合并到 project_owner
 * - data_operator: 不在宪法中
 * - media_buyer: 非标准术语，使用 pitcher
 */
export enum UserRole {
  CEO = 'ceo',
  PROJECT_OWNER = 'project_owner',
  FINANCE = 'finance',
  PITCHER = 'pitcher',
  ACCOUNT_MANAGER = 'account_manager',
  ADMIN = 'admin',
}

/**
 * 角色配置 (来源: MASTER.md v4.6 §2.4)
 */
export const USER_ROLE_CONFIG: Record<UserRole, {
  label: string;
  description: string;
  permissions: string;
  level: number;
}> = {
  [UserRole.CEO]: {
    label: '老板',
    description: '资金安全、公司盈亏、最终决策',
    permissions: '全部可见，批准充值，锁定结算',
    level: 100,
  },
  [UserRole.ADMIN]: {
    label: '管理员',
    description: '系统配置（不参与业务）',
    permissions: '系统设置',
    level: 95,
  },
  [UserRole.FINANCE]: {
    label: '财务',
    description: '资金出入准确、数据真实、对账',
    permissions: '审核充值，更新资金表，锁定结算',
    level: 80,
  },
  [UserRole.PROJECT_OWNER]: {
    label: '项目负责人',
    description: '项目盈亏、资金使用效率、日报审核',
    permissions: '申请充值，审核日报，调配投手',
    level: 70,
  },
  [UserRole.ACCOUNT_MANAGER]: {
    label: '户管',
    description: '账户分配、账户状态监控',
    permissions: '管理账户分配，收集充值需求',
    level: 50,
  },
  [UserRole.PITCHER]: {
    label: '投手',
    description: 'CPL 达标、日报准确、执行投放',
    permissions: '填报日报，查看自己数据',
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
