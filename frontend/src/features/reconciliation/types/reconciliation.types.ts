/**
 * Reconciliation Types
 *
 * Aligned with:
 * - RECONCILIATION_SOT.md v1.0
 * - STATE_MACHINE.md v2.6 Section 9 (Reconciliation states)
 * - DATA_SCHEMA.md v5.2 (reconciliations table)
 */

import type { UUID, ISODateString, DateString, Money } from '@/types';

// === Status Enum ===

/**
 * Reconciliation status
 * Flow: pending → in_progress → completed | failed
 */
export type ReconciliationStatus =
  | 'pending'
  | 'in_progress'
  | 'completed'
  | 'failed';

// === Reconciliation Type ===

export type ReconciliationType =
  | 'daily'      // Daily reconciliation
  | 'weekly'     // Weekly summary
  | 'monthly'    // Monthly closing
  | 'ad_hoc';    // Manual reconciliation

// === Entity Types ===

export interface Reconciliation {
  id: UUID;
  tenant_id: UUID;
  project_id?: UUID; // Optional: null means tenant-level

  // Reconciliation scope
  type: ReconciliationType;
  period_start: DateString;
  period_end: DateString;
  status: ReconciliationStatus;

  // Calculated values
  expected_spend: Money;
  actual_spend: Money;
  discrepancy: Money;
  discrepancy_percentage: number;

  // Threshold check
  threshold_exceeded: boolean;
  threshold_value: number; // percentage

  // Results
  items_checked: number;
  items_matched: number;
  items_mismatched: number;
  mismatch_details?: ReconciliationMismatch[];

  // Execution info
  started_at?: ISODateString;
  completed_at?: ISODateString;
  initiated_by: UUID;
  error_message?: string;

  // Metadata
  created_at: ISODateString;
  updated_at: ISODateString;
}

export interface ReconciliationMismatch {
  id: UUID;
  reconciliation_id: UUID;
  daily_report_id: UUID;
  report_date: DateString;

  // Discrepancy details
  expected_amount: Money;
  actual_amount: Money;
  difference: Money;

  // Resolution
  resolution_status: 'pending' | 'resolved' | 'accepted';
  resolution_notes?: string;
  resolved_by?: UUID;
  resolved_at?: ISODateString;
}

// === List/Filter Types ===

export interface ReconciliationFilters {
  tenant_id?: UUID;
  project_id?: UUID;
  type?: ReconciliationType | ReconciliationType[];
  status?: ReconciliationStatus | ReconciliationStatus[];
  start_date?: string;
  end_date?: string;
  threshold_exceeded?: boolean;
}

export interface ReconciliationListParams extends ReconciliationFilters {
  page?: number;
  page_size?: number;
  sort_by?: 'created_at' | 'period_start' | 'discrepancy' | 'status';
  sort_order?: 'asc' | 'desc';
}

// === Form Types ===

export interface ReconciliationCreateInput {
  project_id?: UUID;
  type: ReconciliationType;
  period_start: DateString;
  period_end: DateString;
  threshold_value?: number; // Default: 5%
}

export interface MismatchResolveInput {
  resolution_notes: string;
  action: 'accept' | 'adjust';
}

// === Status Display Config ===

export const RECONCILIATION_STATUS_CONFIG: Record<ReconciliationStatus, { label: string; variant: 'default' | 'success' | 'warning' | 'error' | 'info' }> = {
  pending: { label: '待执行', variant: 'default' },
  in_progress: { label: '执行中', variant: 'info' },
  completed: { label: '已完成', variant: 'success' },
  failed: { label: '执行失败', variant: 'error' },
};

export const RECONCILIATION_TYPE_CONFIG: Record<ReconciliationType, { label: string; description: string }> = {
  daily: { label: '日对账', description: '每日自动对账' },
  weekly: { label: '周汇总', description: '每周汇总对账' },
  monthly: { label: '月结', description: '月度结算对账' },
  ad_hoc: { label: '手动对账', description: '临时手动触发' },
};
