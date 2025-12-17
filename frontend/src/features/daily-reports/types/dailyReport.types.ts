/**
 * Daily Report Types
 *
 * Aligned with:
 * - STATE_MACHINE.md v2.6 Section 8 (8-state machine)
 * - DATA_SCHEMA.md v5.2 (daily_reports table)
 * - DAILY_REPORT_SOT.md v2.0
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

// === Entity Types ===

export interface DailyReport {
  id: UUID;
  project_id: UUID;
  report_date: DateString;
  status: DailyReportStatus;

  // Raw data (editable in raw_submitted)
  raw_spend: Money;
  raw_impressions: number;
  raw_clicks: number;
  raw_conversions: number;

  // Trend analysis (set in trend_pending)
  trend_score?: number;
  trend_alert_level?: 'normal' | 'warning' | 'critical';
  trend_notes?: string;

  // Final confirmed data (immutable after final_confirmed)
  final_spend?: Money;
  final_impressions?: number;
  final_clicks?: number;
  final_conversions?: number;

  // Metadata
  submitted_by: UUID;
  confirmed_by?: UUID;
  locked_at?: ISODateString;
  created_at: ISODateString;
  updated_at: ISODateString;
}

// === List/Filter Types ===

export interface DailyReportFilters {
  project_id?: UUID;
  status?: DailyReportStatus | DailyReportStatus[];
  start_date?: DateString;
  end_date?: DateString;
  search?: string;
}

export interface DailyReportListParams extends DailyReportFilters {
  page?: number;
  page_size?: number;
  sort_by?: 'report_date' | 'status' | 'raw_spend' | 'created_at';
  sort_order?: 'asc' | 'desc';
}

// === Form Types ===

export interface DailyReportCreateInput {
  project_id: UUID;
  report_date: DateString;
  raw_spend: number; // cents
  raw_impressions: number;
  raw_clicks: number;
  raw_conversions: number;
}

export interface DailyReportUpdateInput {
  raw_spend?: number;
  raw_impressions?: number;
  raw_clicks?: number;
  raw_conversions?: number;
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
 */
export const ALLOWED_TRANSITIONS: StateTransition[] = [
  { from: 'raw_submitted', to: 'trend_pending', action: 'submit_for_trend', allowed_roles: ['operator', 'manager', 'admin'] },
  { from: 'trend_pending', to: 'trend_ok', action: 'approve_trend', allowed_roles: ['manager', 'admin'] },
  { from: 'trend_pending', to: 'trend_flagged', action: 'flag_trend', allowed_roles: ['manager', 'admin'] },
  { from: 'trend_flagged', to: 'trend_resolved', action: 'resolve_flag', allowed_roles: ['manager', 'admin'] },
  { from: 'trend_ok', to: 'final_pending', action: 'submit_for_final', allowed_roles: ['manager', 'admin'] },
  { from: 'trend_resolved', to: 'final_pending', action: 'submit_for_final', allowed_roles: ['manager', 'admin'] },
  { from: 'final_pending', to: 'final_confirmed', action: 'confirm_final', allowed_roles: ['admin'] },
  { from: 'final_confirmed', to: 'final_locked', action: 'lock', allowed_roles: ['admin'] },
];

// === Status Display Config ===

export const STATUS_CONFIG: Record<DailyReportStatus, { label: string; variant: 'default' | 'success' | 'warning' | 'error' | 'info' }> = {
  raw_submitted: { label: '原始提交', variant: 'default' },
  trend_pending: { label: '趋势待审', variant: 'info' },
  trend_ok: { label: '趋势通过', variant: 'success' },
  trend_flagged: { label: '趋势异常', variant: 'warning' },
  trend_resolved: { label: '异常已处理', variant: 'info' },
  final_pending: { label: '终审待审', variant: 'info' },
  final_confirmed: { label: '终审确认', variant: 'success' },
  final_locked: { label: '已锁定', variant: 'default' },
};
