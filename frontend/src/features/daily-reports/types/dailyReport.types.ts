/**
 * Daily Report Types
 *
 * Aligned with:
 * - STATE_MACHINE.md v2.6 Section 8 (8-state machine)
 * - DATA_SCHEMA.md v5.2 (daily_reports table)
 * - DAILY_REPORT_SOT.md v2.0
 *
 * v2.0 新增:
 * - region: 投放地区
 * - platform: 广告平台 (FB/Google/TikTok)
 * - follows_count: 进粉数
 * - result_count: 成效数
 * - cost_per_follow: 单粉成本 (计算字段)
 * - cost_per_result: 单次成效费用 (计算字段)
 */

import type { UUID, ISODateString, DateString, Money } from '@/types';

// === Status Enum (STATE_MACHINE.md v2.6 Section 8) ===

/**
 * 8-state machine for daily reports
 *
 * Flow:
 * raw_submitted → trend_pending → trend_ok/trend_flagged
 * → trend_resolved → final_pending → final_confirmed → final_locked
 */
export type DailyReportStatus =
  | 'raw_submitted'
  | 'trend_pending'
  | 'trend_ok'
  | 'trend_flagged'
  | 'trend_resolved'
  | 'final_pending'
  | 'final_confirmed'
  | 'final_locked';

// === Platform & Region Types (v2.0) ===

export type AdPlatform = 'FB' | 'Google' | 'TikTok' | 'Other';

export type AdRegion =
  | 'Turkey'
  | 'India'
  | 'Italy'
  | 'Germany'
  | 'Brazil'
  | 'UK'
  | 'Korea'
  | 'France'
  | 'Malaysia'
  | 'Japan'
  | 'Austria'
  | 'Spain'
  | 'Nigeria'
  | 'Singapore'
  | 'Belgium'
  | 'Sweden'
  | 'Canada'
  | 'Indonesia'
  | 'USA'
  | 'Ireland'
  | 'Other';

export type Currency = 'USD' | 'CNY';

// === Entity Types ===

export interface DailyReport {
  id: number;
  ad_account_id: number;
  report_date: DateString;
  status: DailyReportStatus;

  // 投手提交字段 (v2.0)
  raw_spend: Money;
  follows_count: number; // 进粉数
  result_count: number; // 成效数
  region?: AdRegion; // 投放地区
  platform?: AdPlatform; // 广告平台
  currency: Currency; // 货币类型

  // 系统计算字段 (v2.0)
  cost_per_follow?: Money; // 单粉成本 = raw_spend / follows_count
  cost_per_result?: Money; // 单次成效费用 = raw_spend / result_count

  // 兼容旧字段
  raw_impressions?: number;
  raw_clicks?: number;
  raw_conversions?: number;
  conversions_raw?: number;

  // Trend analysis (set in trend_pending)
  trend_flag?: 'normal' | 'flagged' | 'resolved';
  trend_flag_reason?: string;
  trend_resolution_note?: string;

  // Final confirmed data (immutable after final_confirmed)
  final_spend?: Money;
  final_impressions?: number;
  final_clicks?: number;
  final_conversions?: number;
  conversions_final?: number;
  real_spend?: Money;

  // 广告信息
  campaign_name?: string;
  ad_group_name?: string;
  ad_creative_name?: string;

  // 聚合字段
  ad_account_name?: string;
  project_id?: number;
  project_name?: string;

  // Metadata
  submitted_by?: UUID;
  created_by?: UUID;
  created_by_name?: string;
  submitter_name?: string; // 投手名称 (v2.1)
  team_name?: string; // 团队名称 (v2.1)
  audit_user_id?: UUID;
  locked_at?: ISODateString;
  created_at: ISODateString;
  updated_at: ISODateString;
}

// === List/Filter Types ===

export interface DailyReportFilters {
  ad_account_id?: number;
  project_id?: number;
  status?: DailyReportStatus | DailyReportStatus[];
  start_date?: DateString;
  end_date?: DateString;
  region?: AdRegion;
  platform?: AdPlatform;
  team_id?: string; // 团队ID (UUID, v2.1)
  submitter_name?: string; // 投手名称 (v2.1)
  search?: string;
}

export interface DailyReportListParams extends DailyReportFilters {
  page?: number;
  page_size?: number;
  sort_by?:
    | 'report_date'
    | 'status'
    | 'raw_spend'
    | 'follows_count'
    | 'result_count'
    | 'created_at';
  sort_order?: 'asc' | 'desc';
}

// === Form Types ===

/**
 * 日报创建表单 - 投手提交原始数据
 *
 * 必填字段:
 * - report_date: 报告日期
 * - ad_account_id: 广告账户ID
 * - raw_spend: 广告消耗
 * - follows_count: 进粉数
 * - result_count: 成效数
 * - region: 投放地区
 */
export interface DailyReportCreateInput {
  report_date: DateString;
  ad_account_id: number;
  raw_spend: number; // 广告消耗 (USD)
  follows_count: number; // 进粉数
  result_count: number; // 成效数
  region: AdRegion; // 投放地区
  platform?: AdPlatform; // 广告平台 (可选)
  currency?: Currency; // 货币类型 (默认 USD)
  campaign_name?: string;
  ad_group_name?: string;
  ad_creative_name?: string;
  impressions?: number;
  clicks?: number;
  notes?: string;
}

/**
 * 日报更新表单 - 仅可更新原始提交字段
 */
export interface DailyReportUpdateInput {
  raw_spend?: number;
  follows_count?: number;
  result_count?: number;
  region?: AdRegion;
  platform?: AdPlatform;
  currency?: Currency;
  campaign_name?: string;
  ad_group_name?: string;
  ad_creative_name?: string;
  impressions?: number;
  clicks?: number;
  notes?: string;
}

export interface TrendResolveInput {
  trend_notes: string;
  resolution_action: 'accept' | 'adjust' | 'reject';
}

export interface FinalConfirmInput {
  final_spend: number;
  final_impressions: number;
  final_clicks: number;
  final_conversions: number;
  confirmation_notes?: string;
}

// === State Transition Types ===

export interface StateTransition {
  from: DailyReportStatus;
  to: DailyReportStatus;
  action: string;
  allowed_roles: string[];
}

/**
 * Allowed transitions per STATE_MACHINE.md v2.6 Section 8.2
 *
 * SoT: MASTER.md v4.6 §2.4 - 宪法角色定义
 * - pitcher: 投手
 * - project_owner: 项目负责人
 * - admin: 管理员
 */
export const ALLOWED_TRANSITIONS: StateTransition[] = [
  {
    from: 'raw_submitted',
    to: 'trend_pending',
    action: 'submit_for_trend',
    allowed_roles: ['pitcher', 'project_owner', 'admin'],
  },
  {
    from: 'trend_pending',
    to: 'trend_ok',
    action: 'approve_trend',
    allowed_roles: ['project_owner', 'admin'],
  },
  {
    from: 'trend_pending',
    to: 'trend_flagged',
    action: 'flag_trend',
    allowed_roles: ['project_owner', 'admin'],
  },
  {
    from: 'trend_flagged',
    to: 'trend_resolved',
    action: 'resolve_flag',
    allowed_roles: ['project_owner', 'admin'],
  },
  {
    from: 'trend_ok',
    to: 'final_pending',
    action: 'submit_for_final',
    allowed_roles: ['project_owner', 'admin'],
  },
  {
    from: 'trend_resolved',
    to: 'final_pending',
    action: 'submit_for_final',
    allowed_roles: ['project_owner', 'admin'],
  },
  {
    from: 'final_pending',
    to: 'final_confirmed',
    action: 'confirm_final',
    allowed_roles: ['admin'],
  },
  { from: 'final_confirmed', to: 'final_locked', action: 'lock', allowed_roles: ['admin'] },
];

// === Status Display Config ===

export const STATUS_CONFIG: Record<
  DailyReportStatus,
  { label: string; variant: 'default' | 'success' | 'warning' | 'error' | 'info' }
> = {
  raw_submitted: { label: '原始提交', variant: 'default' },
  trend_pending: { label: '趋势待审', variant: 'info' },
  trend_ok: { label: '趋势通过', variant: 'success' },
  trend_flagged: { label: '趋势异常', variant: 'warning' },
  trend_resolved: { label: '异常已处理', variant: 'info' },
  final_pending: { label: '终审待审', variant: 'info' },
  final_confirmed: { label: '终审确认', variant: 'success' },
  final_locked: { label: '已锁定', variant: 'default' },
};

// === Phase 1 简化状态配置 (CLAUDE.md Phase 1 要求) ===
// Phase 1 只展示 3 个核心状态: raw_submitted → trend_ok → final_confirmed
// 其他中间状态映射到这 3 个状态进行展示

export type Phase1Status = 'raw_submitted' | 'trend_ok' | 'final_confirmed';

/**
 * 将 8 状态映射到 Phase 1 的 3 个展示状态
 */
export const PHASE1_STATUS_MAP: Record<DailyReportStatus, Phase1Status> = {
  raw_submitted: 'raw_submitted', // 已提交
  trend_pending: 'raw_submitted', // 处理中 → 显示为已提交
  trend_ok: 'trend_ok', // 趋势通过
  trend_flagged: 'raw_submitted', // 异常 → 显示为已提交(待处理)
  trend_resolved: 'trend_ok', // 已解决 → 显示为趋势通过
  final_pending: 'trend_ok', // 待终审 → 显示为趋势通过
  final_confirmed: 'final_confirmed', // 已确认
  final_locked: 'final_confirmed', // 已锁定 → 显示为已确认
};

export const PHASE1_STATUS_CONFIG: Record<
  Phase1Status,
  { label: string; variant: 'default' | 'success' | 'warning' | 'error' | 'info' }
> = {
  raw_submitted: { label: '已提交', variant: 'info' },
  trend_ok: { label: '已审核', variant: 'success' },
  final_confirmed: { label: '已确认', variant: 'default' },
};

/**
 * 获取状态的 Phase 1 展示配置
 */
export function getPhase1StatusConfig(status: DailyReportStatus): {
  label: string;
  variant: 'default' | 'success' | 'warning' | 'error' | 'info';
} {
  const phase1Status = PHASE1_STATUS_MAP[status];
  return PHASE1_STATUS_CONFIG[phase1Status];
}

// === Platform & Region Options (v2.0) ===

export const PLATFORM_OPTIONS: Array<{ value: AdPlatform; label: string }> = [
  { value: 'FB', label: 'Facebook' },
  { value: 'Google', label: 'Google Ads' },
  { value: 'TikTok', label: 'TikTok' },
  { value: 'Other', label: '其他' },
];

export const REGION_OPTIONS: Array<{ value: AdRegion; label: string }> = [
  { value: 'Turkey', label: '土耳其' },
  { value: 'India', label: '印度' },
  { value: 'Italy', label: '意大利' },
  { value: 'Germany', label: '德国' },
  { value: 'Brazil', label: '巴西' },
  { value: 'UK', label: '英国' },
  { value: 'Korea', label: '韩国' },
  { value: 'France', label: '法国' },
  { value: 'Malaysia', label: '马来西亚' },
  { value: 'Japan', label: '日本' },
  { value: 'Austria', label: '奥地利' },
  { value: 'Spain', label: '西班牙' },
  { value: 'Nigeria', label: '尼日利亚' },
  { value: 'Singapore', label: '新加坡' },
  { value: 'Belgium', label: '比利时' },
  { value: 'Sweden', label: '瑞典' },
  { value: 'Canada', label: '加拿大' },
  { value: 'Indonesia', label: '印度尼西亚' },
  { value: 'USA', label: '美国' },
  { value: 'Ireland', label: '爱尔兰' },
  { value: 'Other', label: '其他' },
];

export const CURRENCY_OPTIONS: Array<{ value: Currency; label: string }> = [
  { value: 'USD', label: '美元 (USD)' },
  { value: 'CNY', label: '人民币 (CNY)' },
];
