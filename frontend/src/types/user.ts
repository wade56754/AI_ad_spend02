/**
 * 用户模型定义
 *
 * SoT 引用:
 * - DATA_SCHEMA.md v5.10 §1.1 (users 表结构)
 * - STATE_MACHINE.md v2.9 §2.1 (业务层角色映射)
 * - AUTH_SPEC.md v2.2 (认证授权规范)
 */

import type { TechRole, BusinessRole } from './roles';
import type { ISODateString } from './common';

// === 用户基础接口 ===

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string | null;

  // 技术层角色 (4 个值之一)
  role: TechRole;

  // 项目负责人标识 (业务属性)
  // SoT: STATE_MACHINE.md v2.9 §2.1 - project_owner 通过布尔字段判断
  is_project_owner: boolean;

  // 关联项目 ID
  project_id: number | null;

  // 账户状态
  is_active: boolean;

  // 时间戳
  created_at: ISODateString;
  updated_at: ISODateString;
  last_login_at: ISODateString | null;
}

// === 用户列表项 ===

export interface UserListItem {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: TechRole;
  is_project_owner: boolean;
  project_id: number | null;
  project_name: string | null;
  is_active: boolean;
  created_at: ISODateString;
  last_login_at: ISODateString | null;
}

// === 用户创建/更新输入 ===

export interface UserCreateInput {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  role: TechRole;
  is_project_owner?: boolean;
  project_id?: number | null;
}

export interface UserUpdateInput {
  email?: string;
  username?: string;
  full_name?: string;
  role?: TechRole;
  is_project_owner?: boolean;
  project_id?: number | null;
  is_active?: boolean;
}

// === 密码更新 ===

export interface PasswordUpdateInput {
  current_password: string;
  new_password: string;
}

// === 用户扩展信息 (带业务角色) ===

export interface UserWithBusinessRole extends User {
  // 计算得出的业务层角色
  business_role: BusinessRole;
}

// === 用户查询参数 ===

export interface UserListParams {
  page?: number;
  page_size?: number;
  role?: TechRole;
  is_active?: boolean;
  is_project_owner?: boolean;
  project_id?: number;
  search?: string;
}

// === 当前用户上下文 ===

export interface CurrentUser {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: TechRole;
  is_project_owner: boolean;
  project_id: number | null;

  // 权限判断结果 (由 usePermission Hook 计算)
  business_role: BusinessRole;
  permissions: string[];
}
