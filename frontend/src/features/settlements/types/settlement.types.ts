/**
 * Settlement Types - 结算类型定义
 *
 * SoT: docs/10.module-specs/D1-monthly-settlement.md §2 数据需求
 * SoT: DATA_SCHEMA.md v5.2 (settlement entity)
 * SoT: LEDGER_SOT.md v1.1 (ledger integration)
 * SoT: STATE_MACHINE.md v2.6 Section 12
 *
 * 一句话定义: 结算管理（通用结算 + 月度项目结算）
 *
 * 通用结算状态机 (7 状态):
 *   DRAFT → PENDING → APPROVED → PROCESSING → COMPLETED
 *                  ↘ REJECTED
 *   任意 → CANCELLED
 *
 * 月度结算状态机 (D1-monthly-settlement.md §2.4, 4 状态):
 *   pending → draft → confirmed → locked (终态)
 *
 * Phase 约束 (D1-monthly-settlement.md §1.4):
 * - Phase 1: 结算可修改，用于观察
 * - Phase 2: 锁定后不可修改
 *
 * Author: AI 代码工厂 v2.4
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

// ========== 月度结算类型 (D1-monthly-settlement.md) ==========

/**
 * 月度结算状态
 * SoT: D1-monthly-settlement.md §2.4 状态机
 */
export type MonthlySettlementStatus = 'pending' | 'draft' | 'confirmed' | 'locked';

/**
 * 月度结算实体
 * SoT: D1-monthly-settlement.md §2.2 字段清单
 */
export interface MonthlySettlement {
  id: number;
  settlement_month: string;       // 结算月份 YYYY-MM
  project_id: number;
  project_name: string;
  owner_name: string;             // 项目负责人
  total_spend: number;            // 总消耗 (SUM ad_spend_daily.spend)
  total_conversions: number;      // 总进粉 (SUM daily_reports.conversions)
  avg_cpl: number;                // 平均CPL = total_spend / total_conversions
  revenue: number;                // 预计收入 = total_conversions × unit_price
  gross_profit: number;           // 毛利 = revenue - total_spend
  profit_rate: number;            // 毛利率 = gross_profit / revenue × 100%
  status: MonthlySettlementStatus;
  confirmed_by: number | null;
  confirmed_by_name: string | null;
  confirmed_at: string | null;
  is_locked: boolean;
  locked_by: number | null;
  locked_by_name: string | null;
  locked_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * 月度结算汇总
 * SoT: D1-monthly-settlement.md §4.2 响应示例
 */
export interface MonthlySettlementSummary {
  settlement_month: string;
  total_spend: number;
  total_conversions: number;
  total_revenue: number;
  total_profit: number;
  avg_profit_rate: number;
  project_count: number;
  confirmed_count: number;
  locked_count: number;
}

/**
 * 月度结算列表参数
 */
export interface MonthlySettlementListParams {
  month?: string;                // YYYY-MM
  project_id?: number;
  status?: MonthlySettlementStatus;
  page?: number;
  page_size?: number;
}

/**
 * 月度结算列表响应
 */
export interface MonthlySettlementListResponse {
  items: MonthlySettlement[];
  total: number;
  page: number;
  page_size: number;
  summary: MonthlySettlementSummary;
}

/**
 * 生成月度结算请求
 */
export interface GenerateMonthlySettlementRequest {
  month: string;                 // YYYY-MM
  project_ids?: number[];        // 可选，不传则全部项目
}

/**
 * 确认/锁定请求
 */
export interface MonthlySettlementActionRequest {
  confirm?: boolean;
  notes?: string;
}

/**
 * 月度结算状态配置
 * SoT: D1-monthly-settlement.md §3.3 状态颜色规范
 */
export const MONTHLY_SETTLEMENT_STATUS_CONFIG: Record<MonthlySettlementStatus, {
  label: string;
  color: 'default' | 'info' | 'warning' | 'success';
  bgClass: string;
  textClass: string;
  description: string;
}> = {
  pending: {
    label: '待生成',
    color: 'default',
    bgClass: 'bg-gray-100',
    textClass: 'text-gray-600',
    description: '月份结束，待生成结算',
  },
  draft: {
    label: '草稿',
    color: 'info',
    bgClass: 'bg-blue-100',
    textClass: 'text-blue-700',
    description: '结算草稿，可修改',
  },
  confirmed: {
    label: '已确认',
    color: 'warning',
    bgClass: 'bg-orange-100',
    textClass: 'text-orange-700',
    description: '已确认，待锁定',
  },
  locked: {
    label: '已锁定',
    color: 'success',
    bgClass: 'bg-green-100',
    textClass: 'text-green-700',
    description: '已锁定，不可修改',
  },
};
