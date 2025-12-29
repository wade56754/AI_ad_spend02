/**
 * 测试账号配置
 *
 * 基于: AI_TEST_GUIDE_v2.1.md §3.2
 * 覆盖: 7 个合法角色 (MASTER.md v4.4 §2.4)
 */

export const TEST_ACCOUNTS = {
  ceo: {
    email: 'ceo@test.local',
    password: 'test123',
    name: '测试老板',
    role: 'ceo',
  },
  finance: {
    email: 'finance@test.local',
    password: 'test123',
    name: '测试财务',
    role: 'finance',
  },
  supervisor: {
    email: 'supervisor@test.local',
    password: 'test123',
    name: '测试主管',
    role: 'supervisor',
  },
  pitcher: {
    email: 'pitcher@test.local',
    password: 'test123',
    name: '测试投手',
    role: 'pitcher',
  },
  project_owner: {
    email: 'owner@test.local',
    password: 'test123',
    name: '测试项目负责人',
    role: 'project_owner',
  },
  account_manager: {
    email: 'am@test.local',
    password: 'test123',
    name: '测试户管',
    role: 'account_manager',
  },
  admin: {
    email: 'admin@test.local',
    password: 'test123',
    name: '测试管理员',
    role: 'admin',
  },
} as const;

export type TestRole = keyof typeof TEST_ACCOUNTS;

/**
 * 获取所有角色列表
 */
export const ALL_ROLES: TestRole[] = [
  'ceo',
  'finance',
  'supervisor',
  'pitcher',
  'project_owner',
  'account_manager',
  'admin',
];

/**
 * 按模块定义的角色权限
 */
export const MODULE_PERMISSIONS: Record<string, {
  allowed: TestRole[];
  denied: TestRole[];
}> = {
  // A1 驾驶舱 - 所有角色可访问，但数据范围不同
  'A1-dashboard': {
    allowed: ['ceo', 'finance', 'supervisor', 'pitcher', 'project_owner', 'account_manager', 'admin'],
    denied: [],
  },
  // A2 资金总览
  'A2-fund-overview': {
    allowed: ['ceo', 'finance', 'project_owner', 'account_manager'],
    denied: ['supervisor', 'pitcher', 'admin'],
  },
  // A3 项目盈亏
  'A3-project-pnl': {
    allowed: ['ceo', 'finance', 'project_owner'],
    denied: ['supervisor', 'pitcher', 'account_manager', 'admin'],
  },
  // B1 充值审批
  'B1-topup-approval': {
    allowed: ['ceo', 'finance', 'supervisor', 'project_owner'],
    denied: ['pitcher', 'account_manager', 'admin'],
  },
  // B2 日报审核
  'B2-daily-report-review': {
    allowed: ['ceo', 'finance', 'supervisor', 'pitcher', 'project_owner'],
    denied: ['account_manager', 'admin'],
  },
  // B3 周度简报
  'B3-weekly-brief': {
    allowed: ['ceo', 'finance', 'supervisor', 'project_owner'],
    denied: ['pitcher', 'account_manager', 'admin'],
  },
  // C1 项目管理
  'C1-project-mgmt': {
    allowed: ['ceo', 'finance', 'supervisor', 'pitcher', 'project_owner', 'account_manager', 'admin'],
    denied: [],
  },
  // C2 投手管理
  'C2-pitcher-mgmt': {
    allowed: ['ceo', 'supervisor', 'pitcher', 'admin'],
    denied: ['finance', 'project_owner', 'account_manager'],
  },
  // C3 消耗明细
  'C3-spend-detail': {
    allowed: ['ceo', 'finance', 'supervisor', 'pitcher', 'project_owner', 'account_manager', 'admin'],
    denied: [],
  },
  // D1 月度结算
  'D1-monthly-settlement': {
    allowed: ['ceo', 'finance', 'project_owner', 'admin'],
    denied: ['supervisor', 'pitcher', 'account_manager'],
  },
};
