/**
 * 角色类型定义
 *
 * SoT 引用:
 * - STATE_MACHINE.md v2.9 §2 (技术层角色)
 * - STATE_MACHINE.md v2.9 §2.1 (业务层角色映射)
 * - MASTER.md v4.9 §2.4 (权限矩阵)
 * - DATA_SCHEMA.md v5.10 §1.1 (角色映射规则)
 */

// === 技术层角色 (4 个) ===
// 数据库 CHECK 约束使用这些值

export type TechRole = 'admin' | 'finance' | 'account_manager' | 'media_buyer';

export const TECH_ROLES = ['admin', 'finance', 'account_manager', 'media_buyer'] as const;

// === 业务层角色 (6 个) ===
// UI 展示和权限判断使用这些值

export type BusinessRole =
  | 'ceo'              // 老板 - 资金安全、公司盈亏、最终决策
  | 'project_owner'    // 项目负责人 - 项目盈亏、日报审核
  | 'finance'          // 财务 - 资金出入准确、对账
  | 'pitcher'          // 投手 - CPL 达标、日报准确
  | 'account_manager'  // 户管 - 账户分配、状态监控
  | 'admin';           // 管理员 - 系统配置

export const BUSINESS_ROLES = [
  'ceo',
  'project_owner',
  'finance',
  'pitcher',
  'account_manager',
  'admin',
] as const;

// === 业务层到技术层映射 ===
// ceo: admin + isCeo() 判断
// project_owner: users.is_project_owner = true
// pitcher: media_buyer (技术层名称)

export const BUSINESS_TO_TECH_MAP: Record<BusinessRole, TechRole | null> = {
  ceo: 'admin',                // CEO 身份通过 isCeo() 函数判断
  project_owner: null,         // 通过 is_project_owner 布尔字段判断
  finance: 'finance',
  pitcher: 'media_buyer',      // 业务名 → 技术名
  account_manager: 'account_manager',
  admin: 'admin',
};

export const TECH_TO_BUSINESS_MAP: Record<TechRole, BusinessRole> = {
  admin: 'admin',              // 默认映射，CEO 需要额外判断
  finance: 'finance',
  account_manager: 'account_manager',
  media_buyer: 'pitcher',      // 技术名 → 业务名
};

// === 角色中文标签 ===

export const ROLE_LABELS: Record<BusinessRole, string> = {
  ceo: '老板',
  project_owner: '项目负责人',
  finance: '财务',
  pitcher: '投手',
  account_manager: '户管',
  admin: '管理员',
};

// === 废弃角色列表 (禁止使用) ===
// SoT: STATE_MACHINE.md v2.9 §2.1 注意事项

export const DEPRECATED_ROLES = ['supervisor', 'data_operator'] as const;

export type DeprecatedRole = (typeof DEPRECATED_ROLES)[number];
