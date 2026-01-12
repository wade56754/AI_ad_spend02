/**
 * role-views - 角色视图配置
 *
 * TASK-FE-DASH-006: 角色视图切换
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §6.1.1 (角色视图差异)
 * - MASTER.md v4.9 §2.4 (6 角色权限矩阵)
 *
 * 定义每个角色视图显示的 KPI、组件和功能
 */

import type { BusinessRole } from '@/types/roles';
import type { LucideIcon } from 'lucide-react';
import {
  DollarSign,
  Users,
  BarChart3,
  Target,
  Wallet,
  CreditCard,
  FileText,
  Activity,
  Settings,
  TrendingUp,
  PieChart,
  UserCheck,
  FolderOpen,
  AlertTriangle,
} from 'lucide-react';

// === 类型定义 ===

export interface KPIConfig {
  /** KPI 唯一标识 */
  id: string;
  /** KPI 名称 */
  label: string;
  /** KPI 图标 */
  icon: LucideIcon;
  /** 颜色主题 */
  color: 'blue' | 'green' | 'purple' | 'orange' | 'red' | 'gray';
  /** 数据字段路径 */
  dataKey: string;
  /** 格式化类型 */
  format: 'currency' | 'number' | 'percent' | 'decimal';
  /** 是否支持点击联动趋势图 */
  clickable?: boolean;
  /** 目标字段路径 (可选) */
  targetKey?: string;
  /** 变化率字段路径 (可选) */
  changeKey?: string;
}

export interface QuickActionConfig {
  /** 操作唯一标识 */
  id: string;
  /** 操作名称 */
  label: string;
  /** 图标 */
  icon: LucideIcon;
  /** 跳转路径 */
  href: string;
  /** 是否主操作 */
  primary?: boolean;
}

export interface PendingTaskConfig {
  /** 任务类型 */
  type: string;
  /** 显示名称 */
  label: string;
  /** 图标 */
  icon: LucideIcon;
  /** 跳转路径 */
  href: string;
  /** 优先级 */
  priority: 'high' | 'medium' | 'low';
}

export interface RoleViewDefinition {
  /** 角色 ID */
  role: BusinessRole;
  /** 显示名称 */
  label: string;
  /** 描述 */
  description: string;
  /** KPI 卡片配置 */
  kpis: KPIConfig[];
  /** 快捷操作配置 */
  quickActions: QuickActionConfig[];
  /** 待办事项类型 */
  pendingTasks: PendingTaskConfig[];
  /** 是否显示趋势图 */
  showTrendChart: boolean;
  /** 是否显示 Top 排行 */
  showTopRankings: boolean;
}

// === KPI 配置定义 ===

/**
 * CEO 视图 KPI
 * 全公司消耗、利润、资金总览
 */
const CEO_KPIS: KPIConfig[] = [
  {
    id: 'total_spend',
    label: '本月总消耗',
    icon: DollarSign,
    color: 'blue',
    dataKey: 'overview.total_spend',
    format: 'currency',
    clickable: true,
    changeKey: 'overview.spend_change',
  },
  {
    id: 'total_revenue',
    label: '本月总收入',
    icon: TrendingUp,
    color: 'green',
    dataKey: 'overview.total_revenue',
    format: 'currency',
    clickable: true,
    changeKey: 'overview.revenue_change',
  },
  {
    id: 'total_profit',
    label: '预计毛利',
    icon: Target,
    color: 'green',
    dataKey: 'overview.total_profit',
    format: 'currency',
    clickable: true,
    changeKey: 'overview.profit_change',
  },
  {
    id: 'overall_cpl',
    label: '整体 CPL',
    icon: BarChart3,
    color: 'orange',
    dataKey: 'overview.cpl',
    format: 'currency',
    targetKey: 'overview.cpl_target',
    changeKey: 'overview.cpl_change',
  },
];

/**
 * 项目负责人视图 KPI
 * 项目消耗、利润、投手绩效
 */
const PROJECT_OWNER_KPIS: KPIConfig[] = [
  {
    id: 'project_spend',
    label: '项目消耗',
    icon: DollarSign,
    color: 'blue',
    dataKey: 'project.total_spend',
    format: 'currency',
    clickable: true,
    changeKey: 'project.spend_change',
  },
  {
    id: 'project_conversions',
    label: '项目进粉',
    icon: Users,
    color: 'purple',
    dataKey: 'project.total_conversions',
    format: 'number',
    clickable: true,
    changeKey: 'project.conversions_change',
  },
  {
    id: 'project_profit',
    label: '项目利润',
    icon: Target,
    color: 'green',
    dataKey: 'project.total_profit',
    format: 'currency',
    changeKey: 'project.profit_change',
  },
  {
    id: 'pitcher_count',
    label: '投手数量',
    icon: UserCheck,
    color: 'gray',
    dataKey: 'project.pitcher_count',
    format: 'number',
  },
];

/**
 * 财务视图 KPI
 * 账户余额、待审充值、月度流水
 */
const FINANCE_KPIS: KPIConfig[] = [
  {
    id: 'total_balance',
    label: '账户总余额',
    icon: Wallet,
    color: 'blue',
    dataKey: 'finance.total_balance',
    format: 'currency',
  },
  {
    id: 'pending_topups',
    label: '待审批充值',
    icon: CreditCard,
    color: 'orange',
    dataKey: 'finance.pending_topups_amount',
    format: 'currency',
  },
  {
    id: 'monthly_income',
    label: '本月流入',
    icon: TrendingUp,
    color: 'green',
    dataKey: 'finance.monthly_income',
    format: 'currency',
  },
  {
    id: 'monthly_expense',
    label: '本月流出',
    icon: DollarSign,
    color: 'red',
    dataKey: 'finance.monthly_expense',
    format: 'currency',
  },
];

/**
 * 投手视图 KPI
 * 我的日报、我的账户、我的CPL
 */
const PITCHER_KPIS: KPIConfig[] = [
  {
    id: 'my_spend',
    label: '我的消耗',
    icon: DollarSign,
    color: 'blue',
    dataKey: 'pitcher.my_spend',
    format: 'currency',
    clickable: true,
  },
  {
    id: 'my_conversions',
    label: '我的进粉',
    icon: Users,
    color: 'purple',
    dataKey: 'pitcher.my_conversions',
    format: 'number',
    clickable: true,
  },
  {
    id: 'my_cpl',
    label: '我的 CPL',
    icon: BarChart3,
    color: 'orange',
    dataKey: 'pitcher.my_cpl',
    format: 'currency',
    targetKey: 'pitcher.cpl_target',
  },
  {
    id: 'my_accounts',
    label: '我的账户',
    icon: FolderOpen,
    color: 'gray',
    dataKey: 'pitcher.account_count',
    format: 'number',
  },
];

/**
 * 户管视图 KPI
 * 账户状态、待分配账户
 */
const ACCOUNT_MANAGER_KPIS: KPIConfig[] = [
  {
    id: 'active_accounts',
    label: '活跃账户',
    icon: Activity,
    color: 'green',
    dataKey: 'account_manager.active_accounts',
    format: 'number',
  },
  {
    id: 'testing_accounts',
    label: '测试中账户',
    icon: AlertTriangle,
    color: 'orange',
    dataKey: 'account_manager.testing_accounts',
    format: 'number',
  },
  {
    id: 'pending_assignments',
    label: '待分配账户',
    icon: Users,
    color: 'purple',
    dataKey: 'account_manager.pending_assignments',
    format: 'number',
  },
  {
    id: 'total_accounts',
    label: '账户总数',
    icon: FolderOpen,
    color: 'blue',
    dataKey: 'account_manager.total_accounts',
    format: 'number',
  },
];

/**
 * 管理员视图 KPI
 * 用户统计、系统健康
 */
const ADMIN_KPIS: KPIConfig[] = [
  {
    id: 'total_users',
    label: '用户总数',
    icon: Users,
    color: 'blue',
    dataKey: 'admin.total_users',
    format: 'number',
  },
  {
    id: 'active_users',
    label: '活跃用户',
    icon: UserCheck,
    color: 'green',
    dataKey: 'admin.active_users',
    format: 'number',
  },
  {
    id: 'pending_actions',
    label: '待处理事项',
    icon: AlertTriangle,
    color: 'orange',
    dataKey: 'admin.pending_actions',
    format: 'number',
  },
  {
    id: 'system_health',
    label: '系统健康度',
    icon: Activity,
    color: 'green',
    dataKey: 'admin.system_health',
    format: 'percent',
  },
];

// === 快捷操作配置 ===

const CEO_QUICK_ACTIONS: QuickActionConfig[] = [
  { id: 'view_reports', label: '查看报表', icon: FileText, href: '/reports', primary: true },
  { id: 'view_finance', label: '财务中心', icon: Wallet, href: '/finance' },
  { id: 'view_projects', label: '项目总览', icon: FolderOpen, href: '/projects' },
];

const PROJECT_OWNER_QUICK_ACTIONS: QuickActionConfig[] = [
  { id: 'review_reports', label: '审核日报', icon: FileText, href: '/daily-reports?status=raw_submitted', primary: true },
  { id: 'view_projects', label: '我的项目', icon: FolderOpen, href: '/projects' },
  { id: 'request_topup', label: '申请充值', icon: CreditCard, href: '/topups/new' },
];

const FINANCE_QUICK_ACTIONS: QuickActionConfig[] = [
  { id: 'approve_topups', label: '审批充值', icon: CreditCard, href: '/topups?status=pending_review', primary: true },
  { id: 'view_ledger', label: '查看账本', icon: Wallet, href: '/finance/ledger' },
  { id: 'view_reconciliation', label: '对账', icon: PieChart, href: '/finance/reconciliation' },
];

const PITCHER_QUICK_ACTIONS: QuickActionConfig[] = [
  { id: 'submit_report', label: '提交日报', icon: FileText, href: '/daily-reports/new', primary: true },
  { id: 'request_topup', label: '申请充值', icon: CreditCard, href: '/topups/new' },
  { id: 'my_accounts', label: '我的账户', icon: FolderOpen, href: '/ad-accounts?filter=mine' },
];

const ACCOUNT_MANAGER_QUICK_ACTIONS: QuickActionConfig[] = [
  { id: 'assign_accounts', label: '分配账户', icon: Users, href: '/ad-accounts?action=assign', primary: true },
  { id: 'create_account', label: '创建账户', icon: FolderOpen, href: '/ad-accounts/new' },
  { id: 'view_channels', label: '渠道管理', icon: Settings, href: '/channels' },
];

const ADMIN_QUICK_ACTIONS: QuickActionConfig[] = [
  { id: 'manage_users', label: '用户管理', icon: Users, href: '/users', primary: true },
  { id: 'system_settings', label: '系统设置', icon: Settings, href: '/settings' },
  { id: 'view_logs', label: '操作日志', icon: FileText, href: '/settings/logs' },
];

// === 待办事项配置 ===

const CEO_PENDING_TASKS: PendingTaskConfig[] = [
  { type: 'pending_topups', label: '待审批充值', icon: CreditCard, href: '/topups?status=pending_review', priority: 'high' },
  { type: 'abnormal_projects', label: '异常项目', icon: AlertTriangle, href: '/projects?filter=abnormal', priority: 'high' },
];

const PROJECT_OWNER_PENDING_TASKS: PendingTaskConfig[] = [
  { type: 'pending_reports', label: '待审核日报', icon: FileText, href: '/daily-reports?status=raw_submitted', priority: 'high' },
  { type: 'trend_flagged', label: '趋势异常', icon: AlertTriangle, href: '/daily-reports?status=trend_flagged', priority: 'medium' },
];

const FINANCE_PENDING_TASKS: PendingTaskConfig[] = [
  { type: 'pending_topups', label: '待审批充值', icon: CreditCard, href: '/topups?status=pending_review', priority: 'high' },
  { type: 'pending_reconciliation', label: '待对账', icon: PieChart, href: '/finance/reconciliation?status=pending', priority: 'medium' },
];

const PITCHER_PENDING_TASKS: PendingTaskConfig[] = [
  { type: 'pending_reports', label: '待提交日报', icon: FileText, href: '/daily-reports?action=submit', priority: 'high' },
  { type: 'low_balance_accounts', label: '余额不足账户', icon: AlertTriangle, href: '/ad-accounts?filter=low_balance', priority: 'medium' },
];

const ACCOUNT_MANAGER_PENDING_TASKS: PendingTaskConfig[] = [
  { type: 'pending_assignments', label: '待分配账户', icon: Users, href: '/ad-accounts?action=assign', priority: 'high' },
  { type: 'suspended_accounts', label: '暂停账户', icon: AlertTriangle, href: '/ad-accounts?status=suspended', priority: 'medium' },
];

const ADMIN_PENDING_TASKS: PendingTaskConfig[] = [
  { type: 'pending_approvals', label: '待审批', icon: FileText, href: '/admin/approvals', priority: 'medium' },
  { type: 'system_alerts', label: '系统告警', icon: AlertTriangle, href: '/admin/alerts', priority: 'low' },
];

// === 角色视图定义 ===

/**
 * 完整角色视图配置
 */
export const ROLE_VIEWS: Record<BusinessRole, RoleViewDefinition> = {
  ceo: {
    role: 'ceo',
    label: '老板视图',
    description: '全公司消耗、利润、资金总览',
    kpis: CEO_KPIS,
    quickActions: CEO_QUICK_ACTIONS,
    pendingTasks: CEO_PENDING_TASKS,
    showTrendChart: true,
    showTopRankings: true,
  },
  project_owner: {
    role: 'project_owner',
    label: '项目负责人视图',
    description: '项目消耗、利润、投手绩效',
    kpis: PROJECT_OWNER_KPIS,
    quickActions: PROJECT_OWNER_QUICK_ACTIONS,
    pendingTasks: PROJECT_OWNER_PENDING_TASKS,
    showTrendChart: true,
    showTopRankings: false,
  },
  finance: {
    role: 'finance',
    label: '财务视图',
    description: '账户余额、待审充值、月度流水',
    kpis: FINANCE_KPIS,
    quickActions: FINANCE_QUICK_ACTIONS,
    pendingTasks: FINANCE_PENDING_TASKS,
    showTrendChart: false,
    showTopRankings: false,
  },
  pitcher: {
    role: 'pitcher',
    label: '投手视图',
    description: '我的日报、我的账户、我的CPL',
    kpis: PITCHER_KPIS,
    quickActions: PITCHER_QUICK_ACTIONS,
    pendingTasks: PITCHER_PENDING_TASKS,
    showTrendChart: true,
    showTopRankings: false,
  },
  account_manager: {
    role: 'account_manager',
    label: '户管视图',
    description: '账户状态、待分配账户',
    kpis: ACCOUNT_MANAGER_KPIS,
    quickActions: ACCOUNT_MANAGER_QUICK_ACTIONS,
    pendingTasks: ACCOUNT_MANAGER_PENDING_TASKS,
    showTrendChart: false,
    showTopRankings: false,
  },
  admin: {
    role: 'admin',
    label: '管理员视图',
    description: '用户统计、系统健康',
    kpis: ADMIN_KPIS,
    quickActions: ADMIN_QUICK_ACTIONS,
    pendingTasks: ADMIN_PENDING_TASKS,
    showTrendChart: false,
    showTopRankings: false,
  },
};

// === 工具函数 ===

/**
 * 获取角色视图配置
 */
export function getRoleView(role: BusinessRole): RoleViewDefinition {
  return ROLE_VIEWS[role] || ROLE_VIEWS.pitcher;
}

/**
 * 获取角色 KPI 配置
 */
export function getRoleKPIs(role: BusinessRole): KPIConfig[] {
  return ROLE_VIEWS[role]?.kpis || [];
}

/**
 * 获取角色快捷操作
 */
export function getRoleQuickActions(role: BusinessRole): QuickActionConfig[] {
  return ROLE_VIEWS[role]?.quickActions || [];
}

/**
 * 获取角色待办事项类型
 */
export function getRolePendingTasks(role: BusinessRole): PendingTaskConfig[] {
  return ROLE_VIEWS[role]?.pendingTasks || [];
}

// === 导出 ===

export {
  CEO_KPIS,
  PROJECT_OWNER_KPIS,
  FINANCE_KPIS,
  PITCHER_KPIS,
  ACCOUNT_MANAGER_KPIS,
  ADMIN_KPIS,
};
