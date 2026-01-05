/**
 * 角色常量配置
 *
 * SoT 引用:
 * - STATE_MACHINE.md v2.9 §2.1 (业务层角色映射)
 * - MASTER.md v4.9 §2.4 (权限矩阵)
 */

import type { BusinessRole, TechRole } from '@/types/roles';

// === 角色显示配置 ===

export interface RoleConfig {
  label: string;
  description: string;
  color: string;
  bgColor: string;
}

export const ROLE_CONFIG: Record<BusinessRole, RoleConfig> = {
  ceo: {
    label: '老板',
    description: '资金安全、公司盈亏、最终决策',
    color: 'text-purple-700',
    bgColor: 'bg-purple-100',
  },
  project_owner: {
    label: '项目负责人',
    description: '项目盈亏、资金使用效率、日报审核',
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
  },
  finance: {
    label: '财务',
    description: '资金出入准确、数据真实、对账',
    color: 'text-green-700',
    bgColor: 'bg-green-100',
  },
  pitcher: {
    label: '投手',
    description: 'CPL 达标、日报准确、执行投放',
    color: 'text-orange-700',
    bgColor: 'bg-orange-100',
  },
  account_manager: {
    label: '户管',
    description: '账户分配、账户状态监控',
    color: 'text-cyan-700',
    bgColor: 'bg-cyan-100',
  },
  admin: {
    label: '管理员',
    description: '系统配置（不参与业务）',
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
  },
};

// === 技术层角色配置 ===

export const TECH_ROLE_CONFIG: Record<TechRole, { label: string; businessRole: BusinessRole }> = {
  admin: { label: '管理员', businessRole: 'admin' },
  finance: { label: '财务', businessRole: 'finance' },
  account_manager: { label: '户管', businessRole: 'account_manager' },
  media_buyer: { label: '投手', businessRole: 'pitcher' },
};

// === 角色选项列表 (用于下拉选择) ===

export const TECH_ROLE_OPTIONS = [
  { value: 'admin' as TechRole, label: '管理员' },
  { value: 'finance' as TechRole, label: '财务' },
  { value: 'account_manager' as TechRole, label: '户管' },
  { value: 'media_buyer' as TechRole, label: '投手' },
];

export const BUSINESS_ROLE_OPTIONS = [
  { value: 'ceo' as BusinessRole, label: '老板' },
  { value: 'project_owner' as BusinessRole, label: '项目负责人' },
  { value: 'finance' as BusinessRole, label: '财务' },
  { value: 'pitcher' as BusinessRole, label: '投手' },
  { value: 'account_manager' as BusinessRole, label: '户管' },
  { value: 'admin' as BusinessRole, label: '管理员' },
];
