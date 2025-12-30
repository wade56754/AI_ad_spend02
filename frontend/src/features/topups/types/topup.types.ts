/**
 * Topup Types
 *
 * Aligned with:
 * - STATE_MACHINE.md v2.6 Section 9 (Topup states - 7 status)
 * - DATA_SCHEMA.md v5.2 (topup_requests table)
 * - LEDGER_SOT.md v1.1 (RECHARGE entry type)
 */

import type { UUID, ISODateString, Money } from '@/types';

// === Status Enum (7 states per STATE_MACHINE.md v2.6 § 9) ===

/**
 * Topup request status - 7 state workflow
 * Flow: draft → pending_review → finance_approve → paid → completed
 *                            ↓                   ↓
 *                         rejected           rejected/cancelled
 */
export type TopupStatus =
  | 'draft'           // 草稿
  | 'pending_review'  // 待数据复核
  | 'finance_approve' // 待财务终审
  | 'paid'            // 已支付
  | 'completed'       // 已完成 (终态)
  | 'rejected'        // 已拒绝 (终态)
  | 'cancelled';      // 已取消 (终态)

// === Entity Types ===

export interface TopupRequest {
  id: UUID;
  tenant_id: UUID;
  project_id: UUID;
  project_name?: string;
  ad_account_id?: UUID;
  ad_account_name?: string;
  amount: Money;
  currency: string;
  status: TopupStatus;
  version: number; // Optimistic locking

  // Request details
  requested_by: UUID;
  requested_by_name?: string;
  requested_at: ISODateString;
  notes?: string;

  // Data review details (pending_review → finance_approve)
  data_reviewed_by?: UUID;
  data_reviewed_by_name?: string;
  data_reviewed_at?: ISODateString;
  data_review_notes?: string;

  // Finance approval details (finance_approve → paid)
  finance_approved_by?: UUID;
  finance_approved_by_name?: string;
  finance_approved_at?: ISODateString;
  finance_approval_notes?: string;

  // Payment details (paid → completed)
  paid_at?: ISODateString;
  payment_reference?: string;
  completed_at?: ISODateString;
  ledger_entry_id?: UUID;

  // Rejection/cancellation
  rejected_by?: UUID;
  rejected_by_name?: string;
  rejected_at?: ISODateString;
  rejection_reason?: string;
  cancelled_by?: UUID;
  cancelled_at?: ISODateString;

  // Metadata
  created_at: ISODateString;
  updated_at: ISODateString;
}

// === Approval Log Entry ===

export interface TopupApprovalLog {
  id: UUID;
  topup_id: UUID;
  action: TopupAction;
  from_status: TopupStatus;
  to_status: TopupStatus;
  operator_id: UUID;
  operator_name: string;
  operator_role: string;
  notes?: string;
  created_at: ISODateString;
}

// === List/Filter Types ===

export interface TopupFilters {
  tenant_id?: UUID;
  project_id?: UUID;
  ad_account_id?: UUID;
  status?: TopupStatus | TopupStatus[];
  start_date?: string;
  end_date?: string;
  min_amount?: number;
  max_amount?: number;
  requested_by?: UUID;
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
  ad_account_id?: UUID;
  amount: number; // cents
  currency?: string;
  notes?: string;
}

export interface TopupSubmitInput {
  version: number;
}

export interface TopupDataReviewInput {
  approved: boolean;
  version: number;
  notes?: string;
}

export interface TopupFinanceApproveInput {
  approved: boolean;
  version: number;
  notes?: string;
  payment_reference?: string;
}

export interface TopupCompleteInput {
  version: number;
  payment_reference?: string;
}

export interface TopupRejectInput {
  version: number;
  rejection_reason: string;
}

export interface TopupCancelInput {
  version: number;
  reason?: string;
}

// Legacy aliases for compatibility
export interface TopupApproveInput {
  approval_notes?: string;
}

// === Action Types ===

export type TopupAction =
  | 'create'
  | 'submit'
  | 'data_review_approve'
  | 'data_review_reject'
  | 'finance_approve'
  | 'finance_reject'
  | 'mark_paid'
  | 'complete'
  | 'cancel';

// === Status Display Config ===

export const TOPUP_STATUS_CONFIG: Record<TopupStatus, {
  label: string;
  variant: 'default' | 'success' | 'warning' | 'error' | 'info' | 'secondary';
  description: string;
  step: number; // Progress step (1-5)
}> = {
  draft: {
    label: '草稿',
    variant: 'secondary',
    description: '充值申请已创建，待提交',
    step: 1,
  },
  pending_review: {
    label: '待数据复核',
    variant: 'warning',
    description: '等待数据运营人员复核',
    step: 2,
  },
  finance_approve: {
    label: '待财务终审',
    variant: 'info',
    description: '数据复核通过，等待财务终审',
    step: 3,
  },
  paid: {
    label: '已支付',
    variant: 'info',
    description: '财务已确认支付，等待到账确认',
    step: 4,
  },
  completed: {
    label: '已完成',
    variant: 'success',
    description: '充值已完成，资金已到账',
    step: 5,
  },
  rejected: {
    label: '已拒绝',
    variant: 'error',
    description: '充值申请已被拒绝',
    step: -1,
  },
  cancelled: {
    label: '已取消',
    variant: 'default',
    description: '充值申请已取消',
    step: -1,
  },
};

// === State Transitions (per STATE_MACHINE.md v2.6 § 9) ===

export const TOPUP_TRANSITIONS: Record<TopupStatus, TopupStatus[]> = {
  draft: ['pending_review', 'cancelled'],
  pending_review: ['finance_approve', 'rejected', 'cancelled'],
  finance_approve: ['paid', 'rejected', 'cancelled'],
  paid: ['completed'],
  completed: [],
  rejected: [],
  cancelled: [],
};

// === Role-based Action Permissions ===
// SoT: MASTER.md v4.6 §2.4 - 合法角色 6 个

export const TOPUP_ACTION_ROLES: Record<TopupAction, string[]> = {
  create: ['pitcher', 'account_manager', 'admin'],
  submit: ['pitcher', 'account_manager', 'admin'],
  data_review_approve: ['project_owner', 'admin'],
  data_review_reject: ['project_owner', 'admin'],
  finance_approve: ['finance', 'admin'],
  finance_reject: ['finance', 'admin'],
  mark_paid: ['finance', 'admin'],
  complete: ['finance', 'system', 'admin'],
  cancel: ['pitcher', 'account_manager', 'admin'],
};

// === Statistics Types ===

export interface TopupStatistics {
  by_status: Record<TopupStatus, number>;
  total_amount: number;
  pending_review_count: number;
  finance_approve_count: number;
  total_count: number;
  this_month_amount: number;
  this_month_count: number;
}
