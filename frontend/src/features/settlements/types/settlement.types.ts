/**
 * Settlement Types - 结算类型定义
 *
 * SoT 对齐:
 * - DATA_SCHEMA.md v5.2 (settlement entity)
 * - LEDGER_SOT.md v1.1 (ledger integration)
 * - backend/routers/settlements.py
 */

// ========== 枚举 ==========

/**
 * 结算状态
 * @see STATE_MACHINE.md v2.6 Section 12
 */
export type SettlementStatus =
  | 'DRAFT'
  | 'PENDING'
  | 'APPROVED'
  | 'REJECTED'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'CANCELLED';

/**
 * 支付状态
 */
export type SettlementPaymentStatus = 'UNPAID' | 'PARTIAL' | 'PAID';

/**
 * 结算类型
 */
export type SettlementType = 'SUPPLIER' | 'CLIENT';

// ========== 基础接口 ==========

/**
 * 结算实体
 */
export interface Settlement {
  id: number;
  settlement_no: string;
  type: SettlementType;
  status: SettlementStatus;
  payment_status: SettlementPaymentStatus;

  // 关联实体
  supplier_id: number | null;
  supplier_name: string | null;
  client_id: number | null;
  client_name: string | null;
  project_id: number | null;
  project_name: string | null;

  // 金额相关
  amount: number;
  paid_amount: number;
  currency: string;

  // 日期
  settlement_period_start: string;
  settlement_period_end: string;
  due_date: string | null;

  // 审批信息
  submitted_by: number | null;
  submitted_by_name: string | null;
  submitted_at: string | null;
  approved_by: number | null;
  approved_by_name: string | null;
  approved_at: string | null;
  rejection_reason: string | null;

  // 附加信息
  notes: string | null;
  metadata: Record<string, unknown> | null;

  // 审计字段
  created_by: number;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * 结算摘要（列表展示用）
 */
export interface SettlementSummary {
  id: number;
  settlement_no: string;
  type: SettlementType;
  status: SettlementStatus;
  payment_status: SettlementPaymentStatus;
  supplier_name: string | null;
  client_name: string | null;
  amount: number;
  paid_amount: number;
  currency: string;
  due_date: string | null;
  created_at: string;
}

/**
 * 结算支付记录
 */
export interface SettlementPayment {
  id: number;
  settlement_id: number;
  amount: number;
  payment_method: string;
  payment_reference: string | null;
  payment_date: string;
  notes: string | null;
  created_by: number;
  created_at: string;
}

// ========== 请求接口 ==========

/**
 * 创建结算请求
 */
export interface SettlementCreateInput {
  type: SettlementType;
  supplier_id?: number;
  client_id?: number;
  project_id?: number;
  amount: number;
  currency?: string;
  settlement_period_start: string;
  settlement_period_end: string;
  due_date?: string;
  notes?: string;
  metadata?: Record<string, unknown>;
}

/**
 * 更新结算请求
 */
export interface SettlementUpdateInput {
  amount?: number;
  currency?: string;
  settlement_period_start?: string;
  settlement_period_end?: string;
  due_date?: string;
  notes?: string;
  metadata?: Record<string, unknown>;
}

/**
 * 审批结算请求
 */
export interface SettlementApproveInput {
  action: 'approve' | 'reject';
  reason?: string;
}

/**
 * 记录支付请求
 */
export interface SettlementPaymentInput {
  amount: number;
  payment_method: string;
  payment_reference?: string;
  payment_date?: string;
  notes?: string;
}

/**
 * 结算列表查询参数
 */
export interface SettlementListParams {
  page?: number;
  page_size?: number;
  settlement_type?: SettlementType;
  status?: SettlementStatus;
  payment_status?: SettlementPaymentStatus;
  supplier_id?: number;
  client_id?: number;
  start_date?: string;
  end_date?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// ========== 响应接口 ==========

/**
 * 结算统计信息
 */
export interface SettlementStatistics {
  total_settlements: number;
  total_amount: number;
  pending_amount: number;
  paid_amount: number;
  overdue_count: number;
  overdue_amount: number;
  status_distribution: Array<{ status: SettlementStatus; count: number; amount: number }>;
  type_distribution: Array<{ type: SettlementType; count: number; amount: number }>;
}

// ========== UI 配置 ==========

/**
 * 结算状态配置
 */
export const SETTLEMENT_STATUS_CONFIG: Record<SettlementStatus, {
  label: string;
  color: 'default' | 'success' | 'warning' | 'error' | 'info';
  description: string;
}> = {
  DRAFT: {
    label: '草稿',
    color: 'default',
    description: '结算单草稿，尚未提交',
  },
  PENDING: {
    label: '待审批',
    color: 'warning',
    description: '已提交，等待审批',
  },
  APPROVED: {
    label: '已审批',
    color: 'info',
    description: '已审批通过，待支付',
  },
  REJECTED: {
    label: '已拒绝',
    color: 'error',
    description: '审批被拒绝',
  },
  PROCESSING: {
    label: '支付中',
    color: 'info',
    description: '正在处理支付',
  },
  COMPLETED: {
    label: '已完成',
    color: 'success',
    description: '结算已完成',
  },
  CANCELLED: {
    label: '已取消',
    color: 'default',
    description: '结算已取消',
  },
};

/**
 * 支付状态配置
 */
export const PAYMENT_STATUS_CONFIG: Record<SettlementPaymentStatus, {
  label: string;
  color: 'default' | 'success' | 'warning' | 'error' | 'info';
}> = {
  UNPAID: {
    label: '未支付',
    color: 'error',
  },
  PARTIAL: {
    label: '部分支付',
    color: 'warning',
  },
  PAID: {
    label: '已支付',
    color: 'success',
  },
};

/**
 * 结算类型配置
 */
export const SETTLEMENT_TYPE_CONFIG: Record<SettlementType, {
  label: string;
  icon: string;
}> = {
  SUPPLIER: {
    label: '供应商结算',
    icon: 'truck',
  },
  CLIENT: {
    label: '客户结算',
    icon: 'users',
  },
};
