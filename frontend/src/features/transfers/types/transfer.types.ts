/**
 * Transfer Types
 *
 * SoT 对齐: STATE_MACHINE.md v2.6 第12章 (transfer_requests 状态机)
 * SoT 对齐: DATA_SCHEMA.md v5.2 第3.4.6节
 */

/** 迁移申请状态 - 5状态机 */
export type TransferStatus =
  | 'draft'
  | 'pending_approval'
  | 'approved'
  | 'completed'
  | 'rejected';

/** 状态配置 */
export const TRANSFER_STATUS_CONFIG: Record<TransferStatus, {
  label: string;
  variant: 'default' | 'secondary' | 'destructive' | 'outline';
}> = {
  draft: { label: '草稿', variant: 'secondary' },
  pending_approval: { label: '待审批', variant: 'outline' },
  approved: { label: '已审批', variant: 'default' },
  completed: { label: '已完成', variant: 'default' },
  rejected: { label: '已拒绝', variant: 'destructive' },
};

/** 允许的状态转换 */
export const TRANSFER_ALLOWED_TRANSITIONS: Record<TransferStatus, TransferStatus[]> = {
  draft: ['pending_approval', 'rejected'],
  pending_approval: ['approved', 'rejected'],
  approved: ['completed'],
  completed: [],
  rejected: [],
};

/** 迁移申请 */
export interface Transfer {
  id: number;
  request_no: string;
  source_ad_account_id: number;
  source_ad_account_name?: string;
  target_ad_account_id: number;
  target_ad_account_name?: string;
  transfer_amount: string;
  status: TransferStatus;
  reason?: string;
  approval_notes?: string;
  rejection_reason?: string;
  created_by?: string;
  created_by_name?: string;
  approved_by?: string;
  approved_by_name?: string;
  created_at: string;
  updated_at: string;
  approved_at?: string;
  completed_at?: string;
}

/** 创建迁移申请输入 */
export interface TransferCreateInput {
  source_ad_account_id: number;
  target_ad_account_id: number;
  transfer_amount: number;
  reason?: string;
}

/** 审批迁移申请输入 */
export interface TransferApproveInput {
  approval_notes?: string;
}

/** 拒绝迁移申请输入 */
export interface TransferRejectInput {
  rejection_reason: string;
}

/** 迁移申请列表查询参数 */
export interface TransferListParams {
  page?: number;
  page_size?: number;
  status?: TransferStatus;
}
