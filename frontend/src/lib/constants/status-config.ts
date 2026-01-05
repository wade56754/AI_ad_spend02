/**
 * 状态配置 - StatusBadge 颜色和标签
 *
 * SoT 引用:
 * - STATE_MACHINE.md v2.9 §4 (全局状态一览表)
 * - STATE_MACHINE.md v2.9 §4A.1 (Phase 边界说明)
 */

import type { StatusVariant } from '@/types/common';
import type {
  DailyReportStatus,
  AccountStatus,
  TopupStatus,
  ProjectStatus,
  ChannelStatus,
} from '@/types/status';

export interface StatusConfig {
  label: string;
  variant: StatusVariant;
  description?: string;
}

// === 日报状态配置 (Phase 1: 3 状态) ===
// SoT: STATE_MACHINE.md v2.9 §4A.1

export const DAILY_REPORT_STATUS_CONFIG: Record<DailyReportStatus, StatusConfig> = {
  raw_submitted: {
    label: '已提交',
    variant: 'info',
    description: '投手已提交原始数据',
  },
  trend_ok: {
    label: '趋势确认',
    variant: 'warning',
    description: '趋势数据已确认',
  },
  final_confirmed: {
    label: '已确认',
    variant: 'success',
    description: '终态锁定',
  },
};

// === 账户状态配置 (6 状态) ===
// SoT: STATE_MACHINE.md v2.9 §4

export const ACCOUNT_STATUS_CONFIG: Record<AccountStatus, StatusConfig> = {
  new: {
    label: '新建',
    variant: 'info',
    description: '新创建的账户',
  },
  testing: {
    label: '测试中',
    variant: 'warning',
    description: '账户正在测试',
  },
  active: {
    label: '活跃',
    variant: 'success',
    description: '账户正常运行',
  },
  suspended: {
    label: '暂停',
    variant: 'warning',
    description: '账户已暂停',
  },
  dead: {
    label: '死号',
    variant: 'error',
    description: '账户已失效（终态）',
  },
  archived: {
    label: '归档',
    variant: 'default',
    description: '账户已归档（终态）',
  },
};

// === 充值状态配置 (7 状态) ===
// SoT: STATE_MACHINE.md v2.9 §4

export const TOPUP_STATUS_CONFIG: Record<TopupStatus, StatusConfig> = {
  draft: {
    label: '草稿',
    variant: 'default',
    description: '充值申请草稿',
  },
  pending_review: {
    label: '待审核',
    variant: 'info',
    description: '等待审核',
  },
  finance_approve: {
    label: '财务已批',
    variant: 'warning',
    description: '财务审批通过',
  },
  paid: {
    label: '已支付',
    variant: 'warning',
    description: '款项已支付',
  },
  completed: {
    label: '已完成',
    variant: 'success',
    description: '充值流程完成（终态）',
  },
  rejected: {
    label: '已拒绝',
    variant: 'error',
    description: '充值申请被拒绝（终态）',
  },
  cancelled: {
    label: '已取消',
    variant: 'default',
    description: '充值申请已取消（终态）',
  },
};

// === 项目状态配置 (4 状态) ===
// SoT: STATE_MACHINE.md v2.9 §5

export const PROJECT_STATUS_CONFIG: Record<ProjectStatus, StatusConfig> = {
  draft: {
    label: '草稿',
    variant: 'default',
    description: '项目草稿',
  },
  active: {
    label: '活跃',
    variant: 'success',
    description: '项目正常运行',
  },
  suspended: {
    label: '暂停',
    variant: 'warning',
    description: '项目已暂停（Phase 1: 仅标记状态）',
  },
  archived: {
    label: '归档',
    variant: 'default',
    description: '项目已归档（终态）',
  },
};

// === 渠道状态配置 (2 状态) ===
// SoT: STATE_MACHINE.md v2.9 §6.1

export const CHANNEL_STATUS_CONFIG: Record<ChannelStatus, StatusConfig> = {
  active: {
    label: '活跃',
    variant: 'success',
    description: '渠道正常运行',
  },
  inactive: {
    label: '停用',
    variant: 'default',
    description: '渠道已停用（终态）',
  },
};

// === 状态选项列表 (用于下拉筛选) ===

export const DAILY_REPORT_STATUS_OPTIONS = [
  { value: 'raw_submitted', label: '已提交' },
  { value: 'trend_ok', label: '趋势确认' },
  { value: 'final_confirmed', label: '已确认' },
] as const;

export const ACCOUNT_STATUS_OPTIONS = [
  { value: 'new', label: '新建' },
  { value: 'testing', label: '测试中' },
  { value: 'active', label: '活跃' },
  { value: 'suspended', label: '暂停' },
  { value: 'dead', label: '死号' },
  { value: 'archived', label: '归档' },
] as const;

export const TOPUP_STATUS_OPTIONS = [
  { value: 'draft', label: '草稿' },
  { value: 'pending_review', label: '待审核' },
  { value: 'finance_approve', label: '财务已批' },
  { value: 'paid', label: '已支付' },
  { value: 'completed', label: '已完成' },
  { value: 'rejected', label: '已拒绝' },
  { value: 'cancelled', label: '已取消' },
] as const;

export const PROJECT_STATUS_OPTIONS = [
  { value: 'draft', label: '草稿' },
  { value: 'active', label: '活跃' },
  { value: 'suspended', label: '暂停' },
  { value: 'archived', label: '归档' },
] as const;

export const CHANNEL_STATUS_OPTIONS = [
  { value: 'active', label: '活跃' },
  { value: 'inactive', label: '停用' },
] as const;
