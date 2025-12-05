/**
 * Transfer Types (死号余额迁移)
 *
 * Aligned with:
 * - TRANSFER_SOT.md v1.0 (Transfer business rules)
 * - STATE_MACHINE.md v2.6 (Transfer states)
 * - LEDGER_SOT.md v1.1 (TRANSFER_OUT/IN)
 */

import type { UUID, ISODateString, Money } from '@/types';

// === Status Enum (TRANSFER_SOT.md §5) ===

/**
 * Transfer request status
 * Flow: draft → approved → completed | rejected
 */
export type TransferStatus =
  | 'draft'
  | 'approved'
  | 'completed'
  | 'rejected';

// === Entity Types ===

export interface TransferRequest {
  id: UUID;
  request_no: string; // Unique idempotent key (TRF-{timestamp}-{random})
  tenant_id: UUID;

  // Source/Target accounts
  source_ad_account_id: UUID;
  target_ad_account_id: UUID;
  source_ad_account_name?: string;
  target_ad_account_name?: string;
  supplier_id: UUID;
  supplier_name?: string;

  // Transfer amount (must = source.remaining_balance)
  transfer_amount: Money;

  // Status
  status: TransferStatus;
  version: number; // Optimistic lock

  // Request details
  created_by: UUID;
  created_by_name?: string;
  notes?: string;

  // Approval details
  approved_by?: UUID;
  approved_by_name?: string;
  approved_at?: ISODateString;
  approval_notes?: string;

  // Completion details
  completed_at?: ISODateString;

  // Rejection details
  rejected_by?: UUID;
  rejected_at?: ISODateString;
  rejection_reason?: string;

  // Metadata
  created_at: ISODateString;
  updated_at: ISODateString;
}

// === List/Filter Types ===

export interface TransferFilters {
  tenant_id?: UUID;
  supplier_id?: UUID;
  status?: TransferStatus | TransferStatus[];
  start_date?: string;
  end_date?: string;
  source_ad_account_id?: UUID;
  target_ad_account_id?: UUID;
}

export interface TransferListParams extends TransferFilters {
  page?: number;
  page_size?: number;
  sort_by?: 'created_at' | 'transfer_amount' | 'status';
  sort_order?: 'asc' | 'desc';
}

// === Form Types ===

export interface TransferCreateInput {
  source_ad_account_id: UUID;
  target_ad_account_id: UUID;
  notes?: string;
}

export interface TransferApproveInput {
  expected_version: number;
  approval_notes?: string;
}

export interface TransferRejectInput {
  expected_version: number;
  rejection_reason: string;
}

// === Status Display Config ===

export const TRANSFER_STATUS_CONFIG: Record<TransferStatus, { label: string; variant: 'default' | 'success' | 'warning' | 'error' | 'info' }> = {
  draft: { label: '草稿', variant: 'default' },
  approved: { label: '已审批', variant: 'info' },
  completed: { label: '已完成', variant: 'success' },
  rejected: { label: '已拒绝', variant: 'error' },
};

// === State Transitions (TRANSFER_SOT.md §5.2) ===

export const TRANSFER_TRANSITIONS = {
  draft: ['approved', 'rejected'],
  approved: ['completed'],
  completed: [], // Terminal state
  rejected: [],  // Terminal state
} as const;

// Alias for component compatibility
export type Transfer = TransferRequest;
