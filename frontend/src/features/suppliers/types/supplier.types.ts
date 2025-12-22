/**
 * Supplier Types - 供应商类型定义
 *
 * SoT 对齐:
 * - DATA_SCHEMA.md v5.2 (supplier entity)
 * - backend/schemas/supplier.py
 */

// ========== 枚举 ==========

export enum SupplierStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  PENDING_REVIEW = 'pending_review',
}

export enum PaymentMethod {
  BANK_TRANSFER = 'bank_transfer',
  WIRE = 'wire',
  PAYPAL = 'paypal',
  CRYPTO = 'crypto',
  OTHER = 'other',
}

// ========== 基础接口 ==========

export interface Supplier {
  id: number;
  name: string;
  contact_name: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  base_currency: string;
  payment_method: PaymentMethod;
  payment_terms: string | null;
  bank_info: Record<string, unknown> | null;
  tax_id: string | null;
  address: string | null;
  country: string | null;
  status: SupplierStatus;
  notes: string | null;
  metadata: Record<string, unknown> | null;

  // 统计字段
  total_accounts: number;
  total_spend: number;

  // 审计字段
  created_by: number;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface SupplierSummary {
  id: number;
  name: string;
  status: SupplierStatus;
  base_currency: string;
  total_accounts: number;
  created_at: string;
}

// ========== 请求接口 ==========

export interface SupplierCreateInput {
  name: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  base_currency?: string;
  payment_method?: PaymentMethod;
  payment_terms?: string;
  bank_info?: Record<string, unknown>;
  tax_id?: string;
  address?: string;
  country?: string;
  notes?: string;
  metadata?: Record<string, unknown>;
}

export interface SupplierUpdateInput {
  name?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  base_currency?: string;
  payment_method?: PaymentMethod;
  payment_terms?: string;
  bank_info?: Record<string, unknown>;
  tax_id?: string;
  address?: string;
  country?: string;
  status?: SupplierStatus;
  notes?: string;
  metadata?: Record<string, unknown>;
}

export interface SupplierListParams {
  page?: number;
  page_size?: number;
  status?: SupplierStatus;
  search?: string;
  base_currency?: string;
  payment_method?: PaymentMethod;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// ========== 响应接口 ==========

export interface SupplierStatistics {
  total_suppliers: number;
  active_suppliers: number;
  inactive_suppliers: number;
  total_accounts_managed: number;
  total_spend: number;
  currency_distribution: Array<{ currency: string; count: number }>;
  payment_method_distribution: Array<{ method: string; count: number }>;
}

export interface SupplierLedgerSummary {
  total_topups: number;
  total_spend: number;
  balance: number;
  last_transaction_date: string | null;
}

export interface SupplierAccount {
  id: number;
  account_code: string; // 对齐 init_schema.sql - 账户代码
  name: string; // 对齐 init_schema.sql - 账户名称
  platform: string;
  status: string;
  balance: number;
  created_at: string;
}

// ========== UI 配置 ==========

export const SUPPLIER_STATUS_CONFIG: Record<SupplierStatus, {
  label: string;
  color: 'default' | 'success' | 'warning' | 'error';
  description: string;
}> = {
  [SupplierStatus.ACTIVE]: {
    label: '活跃',
    color: 'success',
    description: '正常运营中',
  },
  [SupplierStatus.INACTIVE]: {
    label: '非活跃',
    color: 'default',
    description: '暂停合作',
  },
  [SupplierStatus.SUSPENDED]: {
    label: '已暂停',
    color: 'error',
    description: '账户已暂停',
  },
  [SupplierStatus.PENDING_REVIEW]: {
    label: '待审核',
    color: 'warning',
    description: '等待审核中',
  },
};

export const PAYMENT_METHOD_CONFIG: Record<PaymentMethod, {
  label: string;
  icon: string;
}> = {
  [PaymentMethod.BANK_TRANSFER]: {
    label: '银行转账',
    icon: 'bank',
  },
  [PaymentMethod.WIRE]: {
    label: '电汇',
    icon: 'wire',
  },
  [PaymentMethod.PAYPAL]: {
    label: 'PayPal',
    icon: 'paypal',
  },
  [PaymentMethod.CRYPTO]: {
    label: '加密货币',
    icon: 'crypto',
  },
  [PaymentMethod.OTHER]: {
    label: '其他',
    icon: 'other',
  },
};
