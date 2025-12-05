/**
 * Topup Types
 *
 * Aligned with:
 * - STATE_MACHINE.md v2.6 Section 7 (Topup states)
 * - DATA_SCHEMA.md v5.2 (topup_requests table)
 * - TOPUP_SOT.md v1.0
 * - LEDGER_SOT.md v1.1 (RECHARGE entry type)
 */

import type { UUID, ISODateString, Money } from '@/types';

// === Status Enum ===

/**
 * Topup request status
 * Flow: pending → approved → completed | rejected | cancelled
 */
export type TopupStatus =
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'completed'
  | 'cancelled';

// === Entity Types ===

export interface TopupRequest {
  id: UUID;
  tenant_id: UUID;
  project_id: UUID;
  amount: Money;
  status: TopupStatus;

  // Display fields (computed from relations)
  ad_account_id?: string;
  ad_account_name?: string;

  // Request details
  requested_by: UUID;
  requested_at: ISODateString;
  notes?: string;

  // Approval details
  approved_by?: UUID;
  approved_at?: ISODateString;
  approval_notes?: string;

  // Completion details
  completed_at?: ISODateString;
  ledger_entry_id?: UUID; // Reference to RECHARGE entry

  // Rejection/cancellation
  rejected_by?: UUID;
  rejected_at?: ISODateString;
  rejection_reason?: string;

  // Metadata
  created_at: ISODateString;
  updated_at: ISODateString;
}

// === List/Filter Types ===

export interface TopupFilters {
  tenant_id?: UUID;
  project_id?: UUID;
  status?: TopupStatus | TopupStatus[];
  start_date?: string;
  end_date?: string;
  min_amount?: number;
  max_amount?: number;
}

export interface TopupListParams extends TopupFilters {
  page?: number;
  page_size?: number;
  sort_by?: 'requested_at' | 'amount' | 'status' | 'created_at';
  sort_order?: 'asc' | 'desc';
}

// === Form Types ===

export interface TopupCreateInput {
  project_id: UUID;
  amount: number; // cents
  notes?: string;
}

export interface TopupApproveInput {
  approval_notes?: string;
}

export interface TopupRejectInput {
  rejection_reason: string;
}

// === Status Display Config ===

export const TOPUP_STATUS_CONFIG: Record<TopupStatus, { label: string; variant: 'default' | 'success' | 'warning' | 'error' | 'info' }> = {
  pending: { label: '待审批', variant: 'warning' },
  approved: { label: '已审批', variant: 'info' },
  completed: { label: '已完成', variant: 'success' },
  rejected: { label: '已拒绝', variant: 'error' },
  cancelled: { label: '已取消', variant: 'default' },
};

// === State Transitions ===

export const TOPUP_TRANSITIONS = {
  pending: ['approved', 'rejected', 'cancelled'],
  approved: ['completed', 'cancelled'],
  rejected: [],
  completed: [],
  cancelled: [],
} as const;

// Alias for component compatibility
export type Topup = TopupRequest;
