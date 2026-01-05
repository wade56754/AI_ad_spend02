/**
 * 状态枚举定义
 *
 * SoT 引用:
 * - STATE_MACHINE.md v2.9 §4 (全局状态一览表)
 * - STATE_MACHINE.md v2.9 §4A.1 (Phase 边界说明)
 *
 * 重要: Phase 1 日报仅使用 3 个状态
 */

// === 日报状态 (Phase 1: 3 状态) ===
// SoT: STATE_MACHINE.md v2.9 §4A.1

export type DailyReportStatusPhase1 =
  | 'raw_submitted'      // 投手提交原始数据
  | 'trend_ok'           // 趋势确认
  | 'final_confirmed';   // 终态锁定

export const DAILY_REPORT_STATUS_PHASE1 = [
  'raw_submitted',
  'trend_ok',
  'final_confirmed',
] as const;

// === 日报状态 (Phase 2: 8 状态，当前禁用) ===
// SoT: STATE_MACHINE.md v2.9 §4
// 注意: Phase 2 需要 Feature Flag ENABLE_FULL_DAILY_REPORT_SM=true

export type DailyReportStatusPhase2 =
  | 'raw_submitted'      // 投手提交原始数据
  | 'trend_pending'      // 趋势风控检测中
  | 'trend_ok'           // 趋势正常
  | 'trend_flagged'      // 趋势异常待审核
  | 'trend_resolved'     // 趋势异常已解决
  | 'final_pending'      // 等待最终确认
  | 'final_confirmed'    // 运营确认最终粉数
  | 'final_locked';      // 计费锁定 (终态)

// 当前使用 Phase 1 状态
export type DailyReportStatus = DailyReportStatusPhase1;

export const DAILY_REPORT_STATUS = DAILY_REPORT_STATUS_PHASE1;

// === 账户状态 (6 状态) ===
// SoT: STATE_MACHINE.md v2.9 §4

export type AccountStatus =
  | 'new'         // 新建
  | 'testing'     // 测试中
  | 'active'      // 活跃
  | 'suspended'   // 暂停
  | 'dead'        // 死号 (终态)
  | 'archived';   // 归档 (终态)

export const ACCOUNT_STATUS = [
  'new',
  'testing',
  'active',
  'suspended',
  'dead',
  'archived',
] as const;

// === 充值状态 (7 状态) ===
// SoT: STATE_MACHINE.md v2.9 §4

export type TopupStatus =
  | 'draft'           // 草稿
  | 'pending_review'  // 待审核
  | 'finance_approve' // 财务审批通过
  | 'paid'            // 已支付
  | 'completed'       // 已完成 (终态)
  | 'rejected'        // 已拒绝 (终态)
  | 'cancelled';      // 已取消 (终态)

export const TOPUP_STATUS = [
  'draft',
  'pending_review',
  'finance_approve',
  'paid',
  'completed',
  'rejected',
  'cancelled',
] as const;

// === 项目状态 (4 状态) ===
// SoT: STATE_MACHINE.md v2.9 §5

export type ProjectStatus =
  | 'draft'      // 草稿
  | 'active'     // 活跃
  | 'suspended'  // 暂停 (Phase 1: 仅标记状态，不阻断投放)
  | 'archived';  // 归档 (终态)

export const PROJECT_STATUS = [
  'draft',
  'active',
  'suspended',
  'archived',
] as const;

// === 渠道状态 (2 状态) ===
// SoT: STATE_MACHINE.md v2.9 §6.1

export type ChannelStatus =
  | 'active'    // 活跃
  | 'inactive'; // 停用 (终态)

export const CHANNEL_STATUS = [
  'active',
  'inactive',
] as const;

// === 对账批次状态 (5 状态) ===
// SoT: STATE_MACHINE.md v2.9 §4

export type ReconciliationBatchStatus =
  | 'draft'            // 草稿
  | 'pending_review'   // 待审核
  | 'approved'         // 已审批
  | 'needs_adjustment' // 需调整
  | 'completed';       // 已完成 (终态)

export const RECONCILIATION_BATCH_STATUS = [
  'draft',
  'pending_review',
  'approved',
  'needs_adjustment',
  'completed',
] as const;

// === 对账明细状态 (3 状态) ===
// SoT: STATE_MACHINE.md v2.9 §4

export type ReconciliationDetailStatus =
  | 'pending'    // 待确认
  | 'confirmed'  // 已确认 (终态)
  | 'adjusted';  // 已调整 (终态)

export const RECONCILIATION_DETAIL_STATUS = [
  'pending',
  'confirmed',
  'adjusted',
] as const;
