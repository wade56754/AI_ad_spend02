/**
 * Finance Types - 财务管理类型定义
 *
 * 匹配任务规格的新 API 响应格式
 *
 * SoT: MASTER.md v4.4 §4.5.5 资金口径定义
 * SoT: LEDGER_SOT.md v1.1 §2-3 双账本
 *
 * @module features/finance/types
 */

// ============================================================================
// 枚举类型
// ============================================================================

export type ProfitStatus = 'healthy' | 'warning' | 'danger' | 'inactive';
export type ReceivableStatus = 'settled' | 'outstanding' | 'refunded';
export type TrendGranularity = 'day' | 'week' | 'month';
export type DistributionGroupBy = 'project' | 'supplier' | 'platform';
export type ProjectSortBy = 'profit' | 'profit_rate' | 'revenue';

// ============================================================================
// Page 1: 资金总览 (Fund Overview) - Types
// ============================================================================

// ---------- API 1: GET /api/v1/finance/fund/overview ----------

export interface FundSummary {
  total_income: number;
  total_expense: number;
  total_receivable: number;
  total_received: number;
  outstanding: number;
  outstanding_count: number;
  available_balance: number;
  opening_balance: number;
}

export interface FundChanges {
  income_change_pct: number | null;
  expense_change_pct: number | null;
  balance_change_pct: number | null;
}

export interface FundOverviewData {
  period: string;
  currency: string;
  summary: FundSummary;
  changes: FundChanges;
}

// ---------- API 2: GET /api/v1/finance/fund/receivables ----------

export interface ReceivableItem {
  project_id: number;
  project_name: string;
  client_name: string;
  total_topup: number;
  total_receivable: number;
  total_received: number;
  outstanding: number;
  balance: number;
  status: ReceivableStatus;
  last_payment_date: string | null;
  refund_date: string | null;
}

export interface ReceivablesTotals {
  total_topup: number;
  total_receivable: number;
  total_outstanding: number;
}

export interface ReceivablesData {
  items: ReceivableItem[];
  totals: ReceivablesTotals;
}

// ---------- API 3: GET /api/v1/finance/fund/distribution ----------

export interface DistributionItem {
  id: number;
  name: string;
  balance: number;
  percentage: number;
}

export interface FundDistributionData {
  group_by: DistributionGroupBy;
  items: DistributionItem[];
  total: number;
}

// ============================================================================
// Page 2: 项目盈亏 (Profit Analysis) - Types
// ============================================================================

// ---------- API 4: GET /api/v1/finance/profit/overview ----------

export interface ProfitSummary {
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  total_conversions: number;
  avg_profit_rate: number;
  total_fee: number;
}

export interface ProfitChanges {
  revenue_change_pct: number | null;
  profit_change_pct: number | null;
}

export interface ProfitBenchmarks {
  industry_avg_profit_rate: number;
  company_target_profit_rate: number;
}

export interface ProfitOverviewData {
  period: string;
  currency: string;
  summary: ProfitSummary;
  changes: ProfitChanges;
  benchmarks: ProfitBenchmarks;
}

// ---------- API 5: GET /api/v1/finance/profit/projects ----------

export interface PriceTier {
  min: number;
  max: number | null;
  price: number;
}

export interface PriceRules {
  type: 'fixed' | 'tiered' | 'spend_ratio';
  tiers?: PriceTier[];
  ratio?: number;
}

export interface ProjectProfitItem {
  project_id: number;
  project_name: string;
  status: string;
  profit_status: ProfitStatus;
  conversions: number | null;
  revenue: number;
  avg_unit_price: number;
  cost: number;
  fee_rate: number;
  profit: number;
  profit_rate: number;
  price_rules: PriceRules | null;
}

export interface ProjectProfitTotals {
  total_conversions: number;
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  avg_profit_rate: number;
}

export interface ProjectProfitsData {
  items: ProjectProfitItem[];
  totals: ProjectProfitTotals;
}

// ---------- API 6: GET /api/v1/finance/profit/suppliers ----------

export interface SupplierCostItem {
  supplier_id: string;
  supplier_name: string;
  platform: string | null;
  fee_rate: number;
  total_spend: number;
  total_fee: number;
  total_cost: number;
  account_count: number;
}

export interface SupplierCostSummary {
  avg_fee_rate: number;
  total_spend: number;
  total_fee: number;
}

export interface SupplierCostsData {
  items: SupplierCostItem[];
  summary: SupplierCostSummary;
}

// ---------- API 7: GET /api/v1/finance/profit/trend ----------

export interface TrendSeriesItem {
  period: string;
  revenue: number;
  cost: number;
  profit: number;
}

export interface ProfitTrendData {
  granularity: TrendGranularity;
  series: TrendSeriesItem[];
}

// ============================================================================
// 请求参数类型
// ============================================================================

export interface FundOverviewParams {
  period?: 'month' | 'quarter' | 'year';
  date?: string; // 2025-12
}

export interface ReceivablesParams {
  status?: 'all' | 'outstanding' | 'settled';
  sort_by?: 'outstanding' | 'receivable' | 'client';
}

export interface FundDistributionParams {
  group_by?: DistributionGroupBy;
  period?: string;
}

export interface ProfitOverviewParams {
  period?: string; // 2025-12
}

export interface ProjectProfitsParams {
  period?: string;
  sort_by?: ProjectSortBy;
  status?: 'all' | 'active' | 'inactive';
}

export interface SupplierCostsParams {
  period?: string;
}

export interface ProfitTrendParams {
  granularity?: TrendGranularity;
  period?: string;
}

// ============================================================================
// UI 辅助类型
// ============================================================================

export const PROFIT_STATUS_CONFIG: Record<ProfitStatus, {
  label: string;
  icon: string;
  color: string;
}> = {
  healthy: { label: '健康', icon: '🟢', color: 'text-green-500' },
  warning: { label: '关注', icon: '🟡', color: 'text-amber-500' },
  danger: { label: '警告', icon: '🔴', color: 'text-red-500' },
  inactive: { label: '非活跃', icon: '⚫', color: 'text-gray-500' },
};

export const RECEIVABLE_STATUS_CONFIG: Record<ReceivableStatus, {
  label: string;
  variant: 'default' | 'secondary' | 'destructive';
}> = {
  settled: { label: '已结清', variant: 'default' },
  outstanding: { label: '待收款', variant: 'destructive' },
  refunded: { label: '已退款', variant: 'secondary' },
};
